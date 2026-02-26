from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta


class Pret(models.Model):
    STATUT_CHOIX = [
        ('en_attente', 'En attente'),
        ('actif', 'Actif'),
        ('rembourse', 'Remboursé'),
        ('defaut', 'Défaillant'),
    ]

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prets')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    taux_annuel = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal('0.00'), help_text="Taux annuel en pourcentage")
    duree_mois = models.PositiveIntegerField(default=12)
    date_debut = models.DateField(null=True, blank=True)
    date_echeance = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=12, choices=STATUT_CHOIX, default='en_attente')
    principal_restant = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Prêt'
        verbose_name_plural = 'Prêts'

    def save(self, *args, **kwargs):
        if not self.date_debut:
            self.date_debut = timezone.now().date()
        if not self.date_echeance:
            # approximation : 30 jours par mois
            self.date_echeance = self.date_debut + timedelta(days=30 * self.duree_mois)
        if self.principal_restant == Decimal('0.00'):
            self.principal_restant = self.montant
        super().save(*args, **kwargs)

    def apply_remboursement(self, montant):
        montant = Decimal(montant)
        self.principal_restant = max(Decimal('0.00'), self.principal_restant - montant)
        if self.principal_restant == Decimal('0.00'):
            self.statut = 'rembourse'
        self.save()

    def montant_interet_mensuel(self):
        if self.taux_annuel and self.taux_annuel != Decimal('0.00'):
            return (self.montant * (self.taux_annuel / Decimal('100'))) / Decimal('12')
        return Decimal('0.00')

    def __str__(self):
        return f"{self.utilisateur} — {self.montant} ({self.get_statut_display()})"


class Remboursement(models.Model):
    pret = models.ForeignKey(Pret, on_delete=models.CASCADE, related_name='remboursements')
    date = models.DateTimeField(auto_now_add=True)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    methode = models.CharField(max_length=50, blank=True, null=True)
    reference = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = 'Remboursement'
        verbose_name_plural = 'Remboursements'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # appliquer automatiquement le remboursement au prêt
        try:
            self.pret.apply_remboursement(self.montant)
        except Exception:
            pass

    def __str__(self):
        return f"Remboursement {self.montant} — {self.pret}"
