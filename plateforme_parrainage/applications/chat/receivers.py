import logging
from django.dispatch import receiver
from .signals import user_message_post_assistant

logger = logging.getLogger(__name__)


@receiver(user_message_post_assistant)
def example_post_assistant(sender, message, **kwargs):
    """Exemple de récepteur déclenché après la réponse de l'assistant.

    - `message` est l'instance `Message` de l'utilisateur.
    Modifiez cette fonction pour appeler votre méthode personnalisée.
    Ne faites pas d'opérations trop longues directement ici; préférez déléguer à Celery ou à une tâche asynchrone.
    """
    try:
        logger.info(f"user_message_post_assistant: message_id={getattr(message, 'id', None)} sender={getattr(message, 'sender', None)} content={getattr(message, 'content', '')[:120]!r}")

        # Exemple d'action minimale (commentée):
        # from applications.chat.models import Message
        # Message.objects.create(group=message.group, sender=None, content='Traitement utilisateur terminé', is_system=True)

        # Placez ici votre logique personnalisée — ex: lancer un job, enregistrer un événement, etc.
    except Exception:
        logger.exception('Erreur dans example_post_assistant')
