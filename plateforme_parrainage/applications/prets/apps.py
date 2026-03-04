from django.apps import AppConfig


class PretsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'applications.prets'
    verbose_name = 'Gestion des prêts'    
    def ready(self):
        """Enregistre les signaux quand l'app est prête."""
        import applications.prets.signals