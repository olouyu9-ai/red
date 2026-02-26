from django.db import models
from django.conf import settings
from decimal import Decimal
from datetime import timedelta

from django.db import models
from django.conf import settings
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

class Produit(models.Model):
    """Modèle pour les marchandises (produits virtuels)."""
    nom = models.CharField(max_length=80, verbose_name="Nom du produit")
    description = models.TextField(verbose_name="Description")
    prix = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Prix")
    duree_jours = models.PositiveIntegerField(default=30, verbose_name="Durée en jours")
    taux_quotidien = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal('0.05'), verbose_name="Taux quotidien")
    est_actif = models.BooleanField(default=True, verbose_name="Est actif")
    image = models.ImageField(upload_to='produits/', verbose_name="Image du produit", blank=True, null=True)

    def __str__(self):
        return self.nom


class Achat(models.Model):
    """Modèle pour les achats de marchandises."""
    STATUT_CHOIX = [
        ('actif', 'Actif'),
        ('expire', 'Expiré'),
        ('annule', 'Annulé'),
    ]

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achats', verbose_name="Utilisateur")
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, verbose_name="Produit")
    prix_au_moment_achat = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Prix au moment de l'achat")
    date_debut = models.DateField(auto_now_add=True, verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    jours_payes = models.PositiveIntegerField(default=0, verbose_name="Jours payés")
    statut = models.CharField(max_length=12, choices=STATUT_CHOIX, default='actif', verbose_name="Statut")
    est_reinvesti = models.BooleanField(default=False, verbose_name="Est réinvesti")

    def save(self, *args, **kwargs):
        if not self.date_fin:
            self.date_fin = self.date_debut + timedelta(days=self.produit.duree_jours)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Achat de {self.produit.nom} par {self.utilisateur.email} ({self.get_statut_display()})"

class GainQuotidien(models.Model):
    """Modèle pour les gains quotidiens générés par les achats."""
    achat = models.ForeignKey(Achat, on_delete=models.CASCADE, related_name='gains_quotidiens', verbose_name="Achat")
    jour = models.DateField(verbose_name="Jour")
    montant = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant")
    poste = models.BooleanField(default=False, verbose_name="Posté au portefeuille")
    poste_le = models.DateTimeField(null=True, blank=True, verbose_name="Date de postage")

    def __str__(self):
        return f"Gain de {self.montant} FC pour {self.achat} le {self.jour}"

"""class Control_achat(models.Model):
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achat_control', verbose_name="Utilisateur")
    jours_payes = models.PositiveIntegerField(default=0, verbose_name="comptage")"""




