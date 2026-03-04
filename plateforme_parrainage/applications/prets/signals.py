"""
Signaux pour l'automatisation des remboursements de retraits crédit.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import RetraitCredit, AjustementRemboursement
from .utils import GestionnaireRemboursement
from applications.produits.models import GainQuotidien


@receiver(post_save, sender=GainQuotidien)
def creer_ajustement_remboursement(sender, instance, created, **kwargs):
    """
    Créé automatiquement un ajustement de remboursement quand un gain quotidien est généré.
    """
    if not created:
        return
    
    # Chercher les retraits en cours de remboursement pour cet utilisateur
    utilisateur = instance.achat.utilisateur
    retraits_actifs = RetraitCredit.objects.filter(
        utilisateur=utilisateur,
        statut='en_remboursement'
    )
    
    for retrait in retraits_actifs:
        try:
            GestionnaireRemboursement.creer_ajustement_depuis_gain(instance, retrait)
        except Exception as e:
            print(f"Erreur lors de la création d'un ajustement pour {utilisateur}: {str(e)}")


@receiver(post_save, sender=RetraitCredit)
def mettre_a_jour_statut_pret(sender, instance, **kwargs):
    """
    Synchronise automatiquement le statut du prêt avec le retrait crédit.
    """
    if instance.pret:
        if instance.statut == 'rembourse' and instance.pret.statut != 'rembourse':
            # Appliquer le dernier montant de remboursement
            instance.pret.apply_remboursement(instance.montant_restant)
        elif instance.statut == 'reject' and instance.pret.statut == 'en_attente':
            instance.pret.statut = 'defaut'
            instance.pret.save()

