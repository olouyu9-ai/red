from django.apps import AppConfig

class PaiementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'applications.paiements'

    def ready(self):
        # Charger les signaux
        import applications.paiements.signals
