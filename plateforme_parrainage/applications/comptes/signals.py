# applications/comptes/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import ProfilUtilisateur

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import ProfilUtilisateur

Utilisateur = get_user_model()

@receiver(post_save, sender=Utilisateur)
def creer_profil_utilisateur(sender, instance, created, **kwargs):
    if created:
        # Vérifiez si un profil existe déjà pour cet utilisateur
        if not hasattr(instance, 'profil'):
            ProfilUtilisateur.objects.create(utilisateur=instance)
