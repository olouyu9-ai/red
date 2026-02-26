from django import forms
from .models import Message, ChatGroup


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows':2, 'placeholder':'Écrire un message...'})
        }


class CreateGroupForm(forms.ModelForm):
    class Meta:
        model = ChatGroup
        fields = ['name', 'description', 'is_private']
