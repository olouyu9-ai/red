"""
Commande Django pour gérer les retraits crédit et les remboursements.
Usage: python manage.py gerer_retraits [action] [params]
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from decimal import Decimal

from applications.prets.models import RetraitCredit, Pret
from applications.prets.utils import (
    VerificateurEligibilite,
    GestionnairePret,
    GestionnaireRemboursement,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Gérer les retraits crédit et les remboursements"
    
    def add_arguments(self, parser):
        parser.add_argument('action', type=str, help='Action à effectuer: info, demander, approuver, rejeter, remboursements')
        parser.add_argument('--email', type=str, help='Email de l\'utilisateur')
        parser.add_argument('--montant', type=Decimal, help='Montant du retrait')
        parser.add_argument('--duree', type=int, default=12, help='Durée en mois (défaut: 12)')
        parser.add_argument('--taux', type=Decimal, default=0, help='Taux annuel (défaut: 0)')
        parser.add_argument('--raison', type=str, help='Raison du rejet')
    
    def handle(self, *args, **options):
        action = options['action']
        email = options.get('email')
        
        if action == 'info':
            self.afficher_infos(email)
        elif action == 'demander':
            self.demander_retrait(email, options.get('montant'), options.get('duree'), options.get('taux'))
        elif action == 'approuver':
            self.approuver_retrait(email)
        elif action == 'rejeter':
            self.rejeter_retrait(email, options.get('raison'))
        elif action == 'remboursements':
            self.afficher_remboursements(email)
        else:
            raise CommandError(f"Action inconnue: {action}")
    
    def afficher_infos(self, email):
        """Affiche les informations d'éligibilité d'un utilisateur."""
        if not email:
            raise CommandError("Email requis (--email)")
        
        try:
            utilisateur = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"Utilisateur non trouvé: {email}")
        
        is_eligible, nb_filleuls, nb_requis = VerificateurEligibilite.verifier_utilisateur(utilisateur)
        montant_max = VerificateurEligibilite.obtenir_montant_max_autorise(utilisateur)
        
        self.stdout.write(self.style.SUCCESS(f"\n📋 Infos d'éligibilité pour {email}"))
        self.stdout.write(f"   Filleuls valides: {nb_filleuls}/{nb_requis}")
        self.stdout.write(f"   Éligible: {'✅ Oui' if is_eligible else '❌ Non'}")
        self.stdout.write(f"   Montant maximum: {montant_max}$\n")
    
    def demander_retrait(self, email, montant, duree, taux):
        """Crée une demande de retrait crédit."""
        if not email or not montant:
            raise CommandError("Email et montant requis (--email, --montant)")
        
        try:
            utilisateur = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"Utilisateur non trouvé: {email}")
        
        retrait, message = GestionnairePret.demander_retrait_credit(
            utilisateur, montant, duree, taux
        )
        
        if retrait:
            self.stdout.write(self.style.SUCCESS(f"✅ {message}"))
            self.stdout.write(f"   Demande ID: {retrait.id}")
            self.stdout.write(f"   Montant: {retrait.montant_demande}$")
            self.stdout.write(f"   Statut: {retrait.get_statut_display()}\n")
        else:
            self.stdout.write(self.style.ERROR(f"❌ {message}\n"))
    
    def approuver_retrait(self, email):
        """Approuve un retrait crédit en attente."""
        if not email:
            raise CommandError("Email requis (--email)")
        
        try:
            retrait = RetraitCredit.objects.get(
                utilisateur__email=email,
                statut='demande'
            )
        except RetraitCredit.DoesNotExist:
            raise CommandError(f"Aucune demande en attente pour {email}")
        
        success, message = GestionnairePret.approuver_retrait(retrait)
        
        if success:
            self.stdout.write(self.style.SUCCESS(f"✅ {message}"))
            self.stdout.write(f"   Retrait ID: {retrait.id}")
            self.stdout.write(f"   Montant approuvé: {retrait.montant_approuve}$\n")
        else:
            self.stdout.write(self.style.ERROR(f"❌ {message}\n"))
    
    def rejeter_retrait(self, email, raison):
        """Rejette un retrait crédit en attente."""
        if not email:
            raise CommandError("Email requis (--email)")
        
        if not raison:
            raison = "Non éligible"
        
        try:
            retrait = RetraitCredit.objects.get(
                utilisateur__email=email,
                statut='demande'
            )
        except RetraitCredit.DoesNotExist:
            raise CommandError(f"Aucune demande en attente pour {email}")
        
        success, message = GestionnairePret.rejeter_retrait(retrait, raison)
        
        self.stdout.write(self.style.SUCCESS(f"✅ {message}"))
        self.stdout.write(f"   Raison: {raison}\n")
    
    def afficher_remboursements(self, email):
        """Affiche les détails des remboursements en cours."""
        if not email:
            raise CommandError("Email requis (--email)")
        
        try:
            utilisateur = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"Utilisateur non trouvé: {email}")
        
        retraits = RetraitCredit.objects.filter(utilisateur=utilisateur)
        
        if not retraits.exists():
            self.stdout.write(self.style.WARNING("Aucun retrait trouvé\n"))
            return
        
        self.stdout.write(self.style.SUCCESS(f"\n💰 Remboursements pour {email}\n"))
        
        for retrait in retraits:
            infos = GestionnaireRemboursement.obtenir_infos_remboursement(retrait)
            progression = infos['pourcentage_rembourse']
            
            self.stdout.write(f"ID: {retrait.id}")
            self.stdout.write(f"  Montant demandé: {infos['montant_initial']}$")
            self.stdout.write(f"  Montant approuvé: {infos['montant_approuve']}$")
            self.stdout.write(f"  Remboursé: {infos['montant_rembourse']}$")
            self.stdout.write(f"  Restant: {infos['montant_restant']}$")
            self.stdout.write(f"  Progression: {progression:.1f}%")
            self.stdout.write(f"  Prélèvement: {infos['pourcentage_prelevement']}% des gains")
            self.stdout.write(f"  Statut: {infos['statut']}\n")

