import json
import logging
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatGroup, Message
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from django.conf import settings
from applications.chat.signals import user_message_post_assistant

logger = logging.getLogger(__name__)
User = get_user_model()


class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs'].get('group_id')
        self.room_group_name = f'chat_{self.group_id}'

        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            logger.info('WebSocket connection refused: anonymous user')
            await self.close()
            return

        logger.info(f'WebSocket connect: user={user.email} group_id={self.group_id}')

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        logger.info(f'WebSocket disconnect: group_id={self.group_id} code={close_code}')
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        try:
            if not text_data:
                return
            data = json.loads(text_data)
            message = data.get('message')
            user = self.scope.get('user')

            logger.info(f'Received WS message from {getattr(user, "email", None)}: {message}')

            if message and user and user.is_authenticated:
                # Save message to DB
                msg = await database_sync_to_async(self.create_message)(user, message)
                if not msg:
                    await self.send(text_data=json.dumps({'error': 'Group not found'}))
                    return

                payload = {
                    'type': 'chat.message',
                    'message': message,
                    'sender': user.email,
                    'created_at': msg.created_at.isoformat(),
                    'message_id': msg.id,
                    'is_system': False,
                    'reply_to': msg.reply_to.id if getattr(msg, 'reply_to', None) else None,
                }
                # Send to group
                await self.channel_layer.group_send(self.room_group_name, payload)
                # Notify other parts of the app that the assistant has already replied
                try:
                    user_message_post_assistant.send(sender=self.__class__, message=msg)
                except Exception:
                    pass
        except Exception:
            logger.exception('Error in WebSocket receive')
            await self.send(text_data=json.dumps({'error': 'Internal server error'}))

    # Receive message from room group
    async def chat_message(self, event):
        out = {
            'message': event.get('message'),
            'sender': event.get('sender'),
            'created_at': event.get('created_at'),
            'message_id': str(event.get('message_id')) if event.get('message_id') is not None else None,
            'reply_to': str(event.get('reply_to')) if event.get('reply_to') is not None else None,
            'is_system': bool(event.get('is_system', False)),
            'reformulated': event.get('reformulated'),
            'original_message': event.get('original_message'),
        }
        await self.send(text_data=json.dumps(out))

    async def chat_typing(self, event):
        """Forward typing indicator events to WebSocket clients."""
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
            logger.warning(f'Create message failed: group {self.group_id} does not exist')
            return None
        msg = Message.objects.create(group=group, sender=user, content=message_text)
        # Assistant removed: do not auto-generate replies
        return msg

    def create_assistant_reply(self, msg: Message):
        """Assistant removed — no automatic replies will be generated."""
        return None
