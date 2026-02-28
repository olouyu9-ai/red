import json
import logging
import time
import asyncio
import requests
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatGroup, Message
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from django.conf import settings
from applications.chat.signals import user_message_post_assistant


# ----- Fonctions utilitaires LLM ------------------------------------------------

def call_hf_model(prompt, model=None):
    """Appelle le routeur d'inférence HuggingFace pour générer du texte.

    Retourne le texte généré ou ``None`` en cas de problème.
    """
    hf_token = getattr(settings, 'HF_API_TOKEN', None)
    hf_model = model or getattr(settings, 'HF_INFERENCE_MODEL', None)
    if not hf_token or not hf_model:
        return None

    url = f'https://router.huggingface.co/models/{hf_model}'
    headers = {'Authorization': f'Bearer {hf_token}'}
    payload = {'inputs': prompt, 'options': {'wait_for_model': True}}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if isinstance(data, dict):
            if 'generated_text' in data:
                return data['generated_text']
            # some models return list/dict
        if isinstance(data, list) and len(data) > 0:
            first = data[0]
            if isinstance(first, dict) and 'generated_text' in first:
                return first['generated_text']
            if isinstance(first, str):
                return first
        return resp.text
    except Exception:
        return None


def _load_knowledge():
    """Lit le fichier de base de connaissances optionnel indiqué dans settings.

    Retourne tout le texte ou ``None`` si non configuré ou introuvable.
    """
    path = getattr(settings, 'KNOWLEDGE_BASE_PATH', None)
    if not path:
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def search_knowledge_base(question_text):
    """Recherche dans la base de connaissances des passages pertinents selon des mots-clés.
    
    Scinde la base en sections, les note selon les correspondances de mots-clés
    et retourne le(s) passage(s) le(s) plus pertinent(s). Retourne ``None`` si rien.
    """
    kb_text = _load_knowledge()
    if not kb_text:
        return None
    
    # normaliser la question : minuscules, découper en mots
    question_lower = question_text.lower()
    question_words = set(word.strip(',.;:!?') for word in question_lower.split() if len(word) > 2)
    
    # découper la base de connaissances en sections (par sauts de paragraphe)
    sections = kb_text.split('\n\n')
    best_matches = []
    
    for section in sections:
        if not section.strip():
            continue
        section_lower = section.lower()
        # compter les correspondances de mots-clés dans cette section
        matches = sum(1 for word in question_words if word in section_lower)
        if matches > 0:
            best_matches.append((matches, section.strip()))
    
    if not best_matches:
        return None
    
    # trier par nombre de correspondances (décroissant) et renvoyer les meilleurs passages
    best_matches.sort(key=lambda x: x[0], reverse=True)
    top_sections = [match[1] for match in best_matches[:2]]
    return '\n\n'.join(top_sections)


def llm_generate_answer(question_text, context=None):
    """Renvoie une réponse à la question donnée en utilisant le LLM configuré.

    Le prompt inclura automatiquement le contenu de la base de connaissances
    (si définie via ``settings.KNOWLEDGE_BASE_PATH``), ce qui permet de fournir
    de longs textes de référence au modèle.

    Si aucun LLM n'est activé, on retombe sur une recherche par mots-clés
    dans la base de connaissances. Retourne ``None`` uniquement en cas d'échec
    complet.

    Préfère le routeur HuggingFace si ``ASSISTANT_USE_HF`` est vrai ; sinon
    utilise OpenAI si ``ASSISTANT_USE_OPENAI`` est activé et la clé existe.
    """
    # préfixer éventuellement le contexte utilisateur avec la base de connaissances
    kb_text = _load_knowledge()
    if kb_text:
        if context:
            context = kb_text + "\n\n" + context
        else:
            context = kb_text

    # HuggingFace first
    if getattr(settings, 'ASSISTANT_USE_HF', False):
        prompt = f"Vous êtes un assistant. Répondez brièvement en français.\nQuestion:\n{question_text}\n"
        if context:
            prompt += f"Contexte : {context}\n"
        out = call_hf_model(prompt)
        if out:
            return out.strip()

    # OpenAI fallback
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    use_openai = getattr(settings, 'ASSISTANT_USE_OPENAI', False)
    model = getattr(settings, 'ASSISTANT_OPENAI_MODEL', 'gpt-3.5-turbo')
    if api_key and use_openai:
        prompt = f"Vous êtes un assistant. Répondez brièvement en français.\nQuestion:\n{question_text}\n"
        if context:
            prompt += f"Contexte : {context}\n"

        try:
            url = 'https://api.openai.com/v1/chat/completions'
            headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
            payload = {
                'model': model,
                'messages': [
                    {'role': 'system', 'content': 'Vous êtes un assistant en français qui répond clairement et poliment.'},
                    {'role': 'user', 'content': prompt},
                ],
                'max_tokens': 300,
                'temperature': 0.4,
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get('choices') or []
                if choices:
                    return choices[0].get('message', {}).get('content', '').strip()
        except Exception:
            pass
    
    # If no LLM available or it failed, try intelligent knowledge base search
    search_result = search_knowledge_base(question_text)
    return search_result

# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)
User = get_user_model()


class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs'].get('group_id')
        self.room_group_name = f'chat_{self.group_id}'

        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            logger.info('Connexion WebSocket refusée : utilisateur anonyme')
            await self.close()
            return

        logger.info(f'Connexion WebSocket : user={user.email} group_id={self.group_id}')

        # Rejoindre le groupe de la salle
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        logger.info(f'Déconnexion WebSocket : group_id={self.group_id} code={close_code}')
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        try:
            if not text_data:
                return
            data = json.loads(text_data)
            message = data.get('message')
            user = self.scope.get('user')

            logger.info(f'Message WS reçu de {getattr(user, "email", None)} : {message}')

            if message and user and user.is_authenticated:
                # Save message to DB
                temp_id = data.get('temp_id')
                msg = await database_sync_to_async(self.create_message)(user, message)
                payloads = None
                if not msg:
                    await self.send(text_data=json.dumps({'error': 'Groupe introuvable'}))
                    return

                payload = {
                    'type': 'chat.message',
                    'message': message,
                    'temp_id': temp_id,
                    'sender': user.email,
                    'created_at': msg.created_at.isoformat(),
                    'message_id': msg.id,
                    'is_system': False,
                    'reply_to': msg.reply_to.id if getattr(msg, 'reply_to', None) else None,
                }
                # Send the user's message to the group immediately
                await self.channel_layer.group_send(self.room_group_name, payload)
                # Notify other parts of the app
                try:
                    user_message_post_assistant.send(sender=self.__class__, message=msg)
                except Exception:
                    pass

                # Send typing indicator immediately, then generate assistant reply in background
                try:
                    typing_payload = {
                        'type': 'chat.typing',
                        'sender': 'Assistant',
                        'reply_to': msg.id,
                        'message': '...'
                    }
                    await self.channel_layer.group_send(self.room_group_name, typing_payload)
                except Exception:
                    logger.exception('Impossible d\'envoyer l\'indicateur typing')

                # Launch background task to generate and send assistant reply
                try:
                    asyncio.create_task(self._async_generate_and_send_assistant(msg.id, message))
                except Exception:
                    logger.exception('Impossible de lancer la tâche assistant en arrière-plan')
        except Exception:
            logger.exception('Erreur lors de la réception WebSocket')
            await self.send(text_data=json.dumps({'error': 'Erreur serveur interne'}))

    # Réception d'un message provenant du groupe de discussion
    async def chat_message(self, event):
        out = {
            'message': event.get('message'),
            'sender': event.get('sender'),
            'created_at': event.get('created_at'),
            'temp_id': event.get('temp_id'),
            'message_id': str(event.get('message_id')) if event.get('message_id') is not None else None,
            'reply_to': str(event.get('reply_to')) if event.get('reply_to') is not None else None,
            'is_system': bool(event.get('is_system', False)),
            'reformulated': event.get('reformulated'),
            'original_message': event.get('original_message'),
        }
        await self.send(text_data=json.dumps(out))

    async def chat_typing(self, event):
        """Transmet les événements d'indicateur de saisie aux clients WebSocket."""
        out = {
            'typing': True,
            'sender': event.get('sender'),
            'reply_to': str(event.get('reply_to')) if event.get('reply_to') is not None else None,
            'message': event.get('message', '...'),
        }
        await self.send(text_data=json.dumps(out))

    def create_message(self, user, message_text):
        try:
            group = ChatGroup.objects.get(id=self.group_id)
        except ChatGroup.DoesNotExist:
            logger.warning(f'Échec création du message : le groupe {self.group_id} n\'existe pas')
            return None
        msg = Message.objects.create(group=group, sender=user, content=message_text)
        return msg

    def _generate_assistant_payload(self, msg_id, message_text):
        """Sync helper: simulate typing, call LLM / KB, create assistant Message and return payload."""
        try:
            # simulate typing / thinking time
            try:
                time.sleep(8)
            except Exception:
                pass

            reply_text = llm_generate_answer(message_text)
            if not reply_text:
                reply_text = "Merci, votre message a bien été reçu. Je vous réponds dès que possible."

            # create assistant message in DB
            group = ChatGroup.objects.get(id=self.group_id)
            assistant_msg = Message.objects.create(
                group=group,
                sender=None,
                content=reply_text,
                is_system=True,
                reply_to=Message.objects.get(id=msg_id),
            )

            assistant_payload = {
                'type': 'chat.message',
                'message': assistant_msg.content,
                'sender': 'Assistant',
                'created_at': assistant_msg.created_at.isoformat(),
                'message_id': assistant_msg.id,
                'reply_to': msg_id,
                'is_system': True,
            }
            return assistant_payload
        except Exception:
            logger.exception('Erreur génération assistant (sync helper)')
            return None

    async def _async_generate_and_send_assistant(self, msg_id, message_text):
        # Run the blocking generation + DB write in threadpool
        try:
            assistant_payload = await database_sync_to_async(self._generate_assistant_payload)(msg_id, message_text)
            if assistant_payload:
                await self.channel_layer.group_send(self.room_group_name, assistant_payload)
        except Exception:
            logger.exception('Erreur lors de l\'envoi du message assistant')

