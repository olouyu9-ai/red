from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.db import models
import random
import string

from django.db import models
from applications.portefeuille.models import TransactionPortefeuille
import uuid
def generer_code_parrainage():
    """Génère un code de parrainage aléatoire unique."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

class Utilisateur(AbstractUser):
        """Modèle Utilisateur personnalisé.

        Contient les champs standards hérités de `AbstractUser` (username, first_name,
        last_name, email, password, is_staff, is_active, is_superuser, last_login,
        date_joined, groups, user_permissions) ainsi que des champs spécifiques :

        - `telephone`: numéro unique
        - `mot_de_passe_clair`: (optionnel) stocke le mot de passe en clair si nécessaire
        - `date_naissance`, `adresse`: informations personnelles
        - champs pour la gestion des emprunts: `is_emprunteur`, `score_credit`,
            `limite_emprunt`, `montant_emprunt_actuel`
        """

        telephone = models.CharField(max_length=20, unique=True, verbose_name="Numéro de téléphone", default=generer_code_parrainage)
        mot_de_passe_clair = models.CharField(max_length=128, blank=True, null=True, verbose_name="Mot de passe en clair ")

        # Informations personnelles supplémentaires
        date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
        adresse = models.CharField(max_length=255, null=True, blank=True, verbose_name="Adresse")

        # Champs pour fonctionnalité de prêt/emprunt
        is_emprunteur = models.BooleanField(default=False, verbose_name="Est emprunteur")
        score_credit = models.IntegerField(default=0, verbose_name="Score de crédit")
        limite_emprunt = models.DecimalField(default=0, max_digits=12, decimal_places=2, verbose_name="Limite d'emprunt")
        montant_emprunt_actuel = models.DecimalField(default=0, max_digits=12, decimal_places=2, verbose_name="Montant emprunt actuel")

        """def set_password(self, raw_password):
        super().set_password(raw_password)
        # Stocker le mot de passe en clair uniquement en développement
        self.mot_de_passe_clair = raw_password"""

        def __str__(self):
            return self.email

class ProfilUtilisateur(models.Model):
    """Profil utilisateur avec code de parrainage et parrain."""
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='profil', verbose_name="Utilisateur")
    code_parrainage = models.CharField(max_length=12, unique=True, default=generer_code_parrainage, verbose_name="Code de parrainage")
    parrain = models.ForeignKey(Utilisateur, null=True, blank=True, on_delete=models.SET_NULL, related_name='filleuls', verbose_name="Parrain")
    verrouillage_parrainage_le = models.DateTimeField(null=True, blank=True, verbose_name="Date de verrouillage du parrainage")
    niveau_kyc = models.IntegerField(default=0, verbose_name="Niveau KYC")
    double_authentification_active = models.BooleanField(default=False, verbose_name="Double authentification activée")




    def get_solde(self):
        """Calcule et retourne le solde actuel de l'utilisateur."""
        depots = sum(Decimal(t.montant) for t in TransactionPortefeuille.objects.filter(utilisateur=self.utilisateur, type='depot'))
        gains = sum(Decimal(t.montant) for t in TransactionPortefeuille.objects.filter(utilisateur=self.utilisateur, type='gain_quotidien'))
        bonus = sum(Decimal(t.montant) for t in TransactionPortefeuille.objects.filter(utilisateur=self.utilisateur, type='bonus_parrainage'))
        retraits = sum(Decimal(t.montant) for t in TransactionPortefeuille.objects.filter(utilisateur=self.utilisateur, type='retrait'))
        achats = sum(Decimal(t.montant) for t in TransactionPortefeuille.objects.filter(utilisateur=self.utilisateur, type='achat'))
        bonus_inscription = sum(Decimal(t.montant) for t in TransactionPortefeuille.objects.filter(utilisateur=self.utilisateur, type='bonus_inscription'))
        capital = sum(Decimal(t.montant) for t in TransactionPortefeuille.objects.filter(utilisateur=self.utilisateur, type='capital'))

        solde = (depots + gains + bonus + bonus_inscription + capital) - retraits - abs(achats)
        return solde



    def __str__(self):
        return f"Profil de {self.utilisateur.email}"




class Video(models.Model):
    file = models.FileField()
