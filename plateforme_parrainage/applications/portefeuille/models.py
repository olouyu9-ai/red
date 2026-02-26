from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid


def generate_reference():
    """Génère une référence unique pour chaque transaction."""
    return 'admin'+ str(uuid.uuid4())


class TransactionPortefeuille(models.Model):
    """Modèle pour les transactions du portefeuille."""
    TYPE_CHOIX = [
        ('depot', 'Dépôt'),
        ('retrait', 'Retrait'),
        ('gain_quotidien', 'Gain quotidien'),
        ('bonus_parrainage', 'Bonus parrainage'),
        ('achat', 'Signer contrat'),
        ('bonus_inscription', 'Bonus inscription'),
        ('capital', 'à retirer capital'),
    ]

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="Utilisateur"
    )
    type = models.CharField(max_length=24, choices=TYPE_CHOIX, verbose_name="Type de transaction")
    montant = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant")
    reference = models.CharField(
        max_length=64,


        default=generate_reference,
        editable=False,
        verbose_name="Référence"
    )
    cree_le = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    solde_apres = models.DecimalField(max_digits=12,editable=False, decimal_places=2, verbose_name="Solde après transaction")
    details = models.TextField(blank=True, null=True, verbose_name="Détails supplémentaires")

    def save(self, *args, **kwargs):
        """Définit automatiquement le solde après transaction."""
        from applications.comptes.models import ProfilUtilisateur  # éviter import circulaire
        solde_actuel = self.utilisateur.profil.get_solde()

        if self.type in ['depot', 'gain_quotidien', 'bonus_parrainage', 'bonus_inscription', 'capital']:
            self.solde_apres = solde_actuel + Decimal(self.montant)
        elif self.type in ['retrait', 'achat']:
            self.solde_apres = solde_actuel - abs(Decimal(self.montant))
        else:
            self.solde_apres = solde_actuel

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.utilisateur.email} - {self.get_type_display()} - {self.montant} FC"








class CapitalClient(models.Model):
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,  verbose_name="Utilisateur")
    capital = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.utilisateur.username} - {self.capital}"


