from django.apps import AppConfig

class MarchandisesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'applications.produits'
    verbose_name = 'produits'

    def ready(self):
        # Importer les signaux
        import applications.produits.signals