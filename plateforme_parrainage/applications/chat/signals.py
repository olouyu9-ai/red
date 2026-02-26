from django.dispatch import Signal

# Signal envoyé après que l'assistant ait répondu et que le message utilisateur
# ait été diffusé. Recepteurs reçoivent kwarg 'message' (instance de Message).
user_message_post_assistant = Signal()
