"""from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Depot
from applications.parrainages.models import BonusParrainage
from applications.portefeuille.models import TransactionPortefeuille
from decimal import Decimal

@receiver(post_save, sender=Depot)
def gerer_bonus_premier_depot(sender, instance, created, **kwargs):
    if instance.statut == 'confirme':
        depots_confirmes = Depot.objects.filter(
            utilisateur=instance.utilisateur,
            statut='confirme'
        ).order_by('confirme_le')

        if depots_confirmes.first() == instance:  # C'est bien le premier dépôt confirmé
            if instance.utilisateur.profil.parrain:
                montant_bonus = instance.montant * Decimal('0.10')

                BonusParrainage.objects.create(
                    parrain=instance.utilisateur.profil.parrain,
                    filleul=instance.utilisateur,
                    depot=instance,
                    montant=montant_bonus
                )

                # Calculer le nouveau solde du parrain
                solde_actuel = instance.utilisateur.profil.parrain.profil.get_solde()
                nouveau_solde = solde_actuel + montant_bonus

                # Créer la transaction dans le portefeuille du parrain
                TransactionPortefeuille.objects.create(
                    utilisateur=instance.utilisateur.profil.parrain,
                    type='bonus_parrainage',
                    montant=montant_bonus,
                    reference=f"Bonus parrainage pour {instance.utilisateur.email}",
                    solde_apres=nouveau_solde
                )
"""