from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class ChatGroup(models.Model):
    """Groupe de discussion (similaire à un groupe WhatsApp)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_private = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_groups')
    created_at = models.DateTimeField(default=timezone.now)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='GroupMembership', related_name='chat_groups')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class GroupMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'group')

    def __str__(self):
        return f"{self.user} in {self.group}"


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_system = models.BooleanField(default=False)
    read_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='read_messages', blank=True)
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        sender = self.sender.email if self.sender else 'system'
        return f"{sender}: {self.content[:40]}"


class Attachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='chat_attachments/')

    def __str__(self):
        return f"Attachment for {self.message_id}"
