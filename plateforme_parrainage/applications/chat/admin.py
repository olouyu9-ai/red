from django.contrib import admin
from .models import ChatGroup, GroupMembership, Message, Attachment


@admin.register(ChatGroup)
class ChatGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'is_private')
    search_fields = ('name', 'description')


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'is_admin', 'joined_at')
    search_fields = ('user__email', 'group__name')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'group', 'created_at', 'is_system')
    search_fields = ('sender__email', 'content')
    readonly_fields = ('created_at',)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('message', 'file')
