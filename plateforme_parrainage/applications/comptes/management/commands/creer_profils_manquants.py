# applications/comptes/management/commands/creer_profils_manquants.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from applications.comptes.models import ProfilUtilisateur

Utilisateur = get_user_model()

class Command(BaseCommand):
    help = 'Crée des profils pour les utilisateurs qui n\'en ont pas'

    def handle(self, *args, **options):
        utilisateurs = Utilisateur.objects.all()
        for utilisateur in utilisateurs:
            ProfilUtilisateur.objects.get_or_create(utilisateur=utilisateur)
            self.stdout.write(self.style.SUCCESS(f'Profil vérifié/créé pour {utilisateur.email}'))
