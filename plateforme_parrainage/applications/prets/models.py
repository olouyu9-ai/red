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

# =====================================================
# SYSTÈME DE RETRAIT CRÉDIT AVEC PROTECTION
# =====================================================

class EligibiliteRetrait(models.Model):
    """
    Modèle de vérification d'éligibilité pour les retraits de crédit.
    Contrôle que l'utilisateur a suffisamment de filleuls avec achats validés.
    """
    MONTANTS_ELIGIBILITE = [
        (100, '5 filleuls minimum'),
        (500, '10 filleuls minimum'),
        (1000, '15 filleuls minimum'),
        (5000, '20 filleuls minimum'),
    ]
    
    utilisateur = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='eligibilite_retrait')
    montant_max_autorise = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))
    nombre_filleuls_requis = models.PositiveIntegerField(default=5)
    nombre_filleuls_valides = models.PositiveIntegerField(default=0, help_text="Nombre de filleuls avec achats validés")
    est_eligible = models.BooleanField(default=False)
    derniere_verification = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Eligibilité Retrait'
        verbose_name_plural = 'Eligibilités Retraits'
    
    def verifier_eligibilite(self):
        """
        Vérifie l'éligibilité de l'utilisateur basée sur le nombre de filleuls.
        Compte les filleuls qui ont des achats de produits à 20 ou 100.
        """
        from parrainages.models import BonusParrainage
        from produits.models import Achat, Produit
        
        # Récupérer les produits éligibles (prix 20 ou 100)
        produits_eligibles = Produit.objects.filter(prix__in=[Decimal('20'), Decimal('100')])
        
        # Compter les filleuls uniques qui ont acheté ces produits ET ont un bonus parrainage
        filleuls_valides = BonusParrainage.objects.filter(
            parrain=self.utilisateur,
            achat__produit__in=produits_eligibles,
            achat__statut='actif'
        ).values('filleul').distinct().count()
        
        self.nombre_filleuls_valides = filleuls_valides
        self.est_eligible = filleuls_valides >= self.nombre_filleuls_requis
        self.derniere_verification = timezone.now()
        self.save()
        
        return self.est_eligible
    
    def __str__(self):
        return f"{self.utilisateur.email} - Filleuls: {self.nombre_filleuls_valides}/{self.nombre_filleuls_requis}"


class RetraitCredit(models.Model):
    """
    Modèle pour gérer les retraits de crédit.
    Chaque retrait est lié à un prêt et doit respecter les conditions d'éligibilité.
    """
    STATUT_CHOIX = [
        ('demande', 'Demandé'),
        ('approuve', 'Approuvé'),
        ('reject', 'Rejeté'),
        ('en_remboursement', 'En remboursement'),
        ('rembourse', 'Remboursé'),
    ]
    
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='retraits_credit')
    pret = models.OneToOneField(Pret, on_delete=models.CASCADE, related_name='retrait_credit')
    montant_demande = models.DecimalField(max_digits=12, decimal_places=2)
    montant_approuve = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOIX, default='demande')
    
    nombre_filleuls_requis = models.PositiveIntegerField(default=5)
    nombre_filleuls_valides = models.PositiveIntegerField(default=0)
    est_eligible = models.BooleanField(default=False)
    
    pourcentage_remboursement = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('10.00'),
        help_text="Pourcentage des gains quotidiens à prélever pour le remboursement"
    )
    
    montant_rembourse = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    montant_restant = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    demande_le = models.DateTimeField(auto_now_add=True)
    approuve_le = models.DateTimeField(null=True, blank=True)
    debute_le = models.DateTimeField(null=True, blank=True)
    termine_le = models.DateTimeField(null=True, blank=True)
    
    raison_rejet = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Retrait Crédit'
        verbose_name_plural = 'Retraits Crédits'
        unique_together = ['utilisateur', 'pret']
    
    def save(self, *args, **kwargs):
        if not self.montant_restant or self.montant_restant == Decimal('0.00'):
            self.montant_restant = self.montant_demande
        super().save(*args, **kwargs)
    
    def verifier_eligibilite(self):
        """Vérifie si l'utilisateur est éligible pour ce retrait."""
        from parrainages.models import BonusParrainage
        from produits.models import Produit
        
        # Récupérer les produits éligibles
        produits_eligibles = Produit.objects.filter(prix__in=[Decimal('20'), Decimal('100')])
        
        # Compter les filleuls uniques avec achats validés
        filleuls = BonusParrainage.objects.filter(
            parrain=self.utilisateur,
            achat__produit__in=produits_eligibles,
            achat__statut='actif'
        ).values('filleul').distinct().count()
        
        self.nombre_filleuls_valides = filleuls
        self.est_eligible = filleuls >= self.nombre_filleuls_requis
        
        return self.est_eligible
    
    def approuver(self):
        """Approuve le retrait et crée un prêt actif."""
        if not self.verifier_eligibilite():
            self.statut = 'reject'
            self.raison_rejet = f"Nombre de filleuls insuffisant ({self.nombre_filleuls_valides}/{self.nombre_filleuls_requis})"
            self.save()
            return False
        
        self.statut = 'approuve'
        self.montant_approuve = self.montant_demande
        self.approuve_le = timezone.now()
        
        # Activer le prêt associé
        self.pret.statut = 'actif'
        self.pret.date_debut = timezone.now().date()
        self.pret.save()
        
        # Changer le statut du retrait crédit
        self.statut = 'en_remboursement'
        self.debute_le = timezone.now()
        self.save()
        
        return True
    
    def rejeter(self, raison="Non éligible"):
        """Rejette le retrait."""
        self.statut = 'reject'
        self.raison_rejet = raison
        self.save()
    
    def __str__(self):
        return f"Retrait {self.montant_demande} $ - {self.utilisateur.email} ({self.get_statut_display()})"


class AjustementRemboursement(models.Model):
    """
    Modèle pour tracker les ajustements de remboursement automatiques.
    Chaque gain quotidien génère un ajustement de remboursement.
    """
    STATUT_CHOIX = [
        ('en_attente', 'En attente'),
        ('applique', 'Appliqué'),
        ('annule', 'Annulé'),
    ]
    
    retrait_credit = models.ForeignKey(RetraitCredit, on_delete=models.CASCADE, related_name='ajustements')
    gain_quotidien = models.ForeignKey('produits.GainQuotidien', on_delete=models.SET_NULL, null=True, blank=True)
    
    montant_gain = models.DecimalField(max_digits=12, decimal_places=2)
    montant_rembourse = models.DecimalField(max_digits=12, decimal_places=2)
    pourcentage_applique = models.DecimalField(max_digits=5, decimal_places=2)
    
    statut = models.CharField(max_length=15, choices=STATUT_CHOIX, default='en_attente')
    applique_le = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Ajustement Remboursement'
        verbose_name_plural = 'Ajustements Remboursements'
    
    def appliquer(self):
        """Applique l'ajustement au remboursement."""
        if self.statut == 'applique':
            return False
        
        self.statut = 'applique'
        self.applique_le = timezone.now()
        self.save()
        
        # Mettre à jour le retrait crédit
        retrait = self.retrait_credit
        retrait.montant_rembourse += self.montant_rembourse
        retrait.montant_restant = max(
            Decimal('0.00'),
            retrait.montant_restant - self.montant_rembourse
        )
        
        # Si remboursement complet, marquer comme remboursé
        if retrait.montant_restant == Decimal('0.00'):
            retrait.statut = 'rembourse'
            retrait.termine_le = timezone.now()
            
            # Marquer le prêt comme remboursé
            retrait.pret.apply_remboursement(retrait.montant_approuve)
        
        retrait.save()
        return True
    
    def __str__(self):
        return f"Remboursement {self.montant_rembourse} $ - {self.retrait_credit.utilisateur.email}"