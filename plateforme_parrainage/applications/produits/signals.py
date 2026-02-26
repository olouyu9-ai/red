from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Achat
from applications.parrainages.models import BonusParrainage
from applications.portefeuille.models import TransactionPortefeuille
from decimal import Decimal

from django.db.models import Q
from django.db import IntegrityError
from decimal import Decimal

@receiver(post_save, sender=Achat)
def gerer_bonus_parrainage_achat(sender, instance, created, **kwargs):
    """
    Signal pour gérer les bonus de parrainage lors d'un achat.
    Le parrain reçoit le bonus UNE SEULE FOIS par filleul.
    """
    # Only for new active purchases
    if created and instance.statut == 'actif':
        utilisateur = instance.utilisateur

        # Check if user has a sponsor and profile
        if not hasattr(utilisateur, 'profil') or not utilisateur.profil.parrain:
            return

        parrain = utilisateur.profil.parrain

        # CRITICAL: Check if sponsor already received a bonus for this godchild
        deja_bonus = BonusParrainage.objects.filter(
            parrain=parrain,
            filleul=utilisateur
        ).exists()

        if deja_bonus:
            return  # EXIT - sponsor already got their bonus for this godchild

        # Check if this is the godchild's FIRST active purchase
        # We exclude the current purchase being processed
        autres_achats_actifs = Achat.objects.filter(
            utilisateur=utilisateur,
            statut='actif'
        ).exclude(id=instance.id).exists()

        # If other active purchases exist, this is not the first one
        if autres_achats_actifs:
            return  # EXIT - not the first active purchase

        # Also check for expired purchases to ensure it's truly the first purchase ever
        autres_achats_tous_statuts = Achat.objects.filter(
            utilisateur=utilisateur
        ).exclude(id=instance.id).exists()

        # If any other purchase exists (active, expired or cancelled), this is not the first
        if autres_achats_tous_statuts:
            return  # EXIT - not the first purchase overall

        # Now we're sure it's the FIRST purchase - create the bonus
        pourcentage_bonus = determiner_pourcentage_bonus(instance.produit)
        montant_bonus = instance.prix_au_moment_achat * pourcentage_bonus

        try:
            # Create the bonus with unique constraint
            BonusParrainage.objects.create(
                parrain=parrain,
                filleul=utilisateur,
                achat=instance,
                montant=montant_bonus,
                pourcentage=pourcentage_bonus,
                est_premier_achat=True
            )

            # Update sponsor's wallet
            mettre_a_jour_portefeuille_parrain(parrain, montant_bonus, utilisateur, instance)

        except IntegrityError:
            # Handle rare race condition case
            print("Bonus déjà existant (race condition gérée)")

def determiner_pourcentage_bonus(produit):
    """Détermine le pourcentage de bonus selon le type de produit"""
    nom_produit = produit.nom.lower()


    if any(mot in nom_produit for mot in ['prime trading corporation', 'starter prime capital partners', 'vip 0']):
        return Decimal('0.10')  # 10% pour les packs starter

    elif any(mot in nom_produit for mot in ['altime trading corporation', 'mango capital trading', 'vip 4']):
        return Decimal('0.12')  # 13% pour les packs premium

    elif any(mot in nom_produit for mot in ['tranford global trading', 'world Trading market', 'elite']):
        return Decimal('0.13')  # 16% pour les packs VIP

    elif any(mot in nom_produit for mot in ['scofield trading group', 'ferguson capital partners', 'ultimate']):
        return Decimal('0.15')  # 20% pour les packs diamond
    else:
        return Decimal('0.10')  # 10% par défaut

def mettre_a_jour_portefeuille_parrain(parrain, montant_bonus, filleul, achat):
    """Met à jour le portefeuille du parrain avec le bonus"""
    try:
        # Calculer le nouveau solde du parrain
        solde_actuel = parrain.profil.get_solde()
        nouveau_solde = solde_actuel + montant_bonus

        # Créer la transaction dans le portefeuille du parrain
        TransactionPortefeuille.objects.create(
            utilisateur=parrain,
            type='bonus_parrainage',
            montant=montant_bonus,
            reference=f"Bonus parrainage - {filleul.email} - {achat.produit.nom}",
            solde_apres=nouveau_solde,
            details=f"Bonus de {montant_bonus} FC ({achat.produit.nom})"
        )

        # Mettre à jour le solde du parrain (si votre modèle Profil a un champ solde)
        if hasattr(parrain.profil, 'solde'):
            parrain.profil.solde = nouveau_solde
            parrain.profil.save()

    except Exception as e:
        # Logger l'erreur pour le debugging
        print(f"Erreur lors de la mise à jour du portefeuille: {e}")