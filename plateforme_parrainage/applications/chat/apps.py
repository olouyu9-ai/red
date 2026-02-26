from django.apps import AppConfig


class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'applications.chat'
    verbose_name = 'Chat entre utilisateurs'
    def ready(self):
        # Import signals to register any receivers
        try:
            import applications.chat.signals  # noqa: F401
            import applications.chat.receivers  # noqa: F401
        except Exception:
            pass
