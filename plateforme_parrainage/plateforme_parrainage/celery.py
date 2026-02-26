"""import os
from celery import Celery

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_parrainage.settings')

# Création de l'application Celery

app = Celery('plateforme_parrainage')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configuration importante pour Windows
app.conf.broker_connection_retry_on_startup = True
app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.result_backend = 'redis://localhost:6379/0'
app.autodiscover_tasks()"""

