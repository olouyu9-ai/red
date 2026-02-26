from django.db import models
from django.conf import settings
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Depot(models.Model):
    STATUT_CHOIX = [
        ('en_attente', 'En attente'),
        ('confirme', 'Confirmé'),
        ('rejete', 'Rejeté'),
    ]

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='depots')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    methode = models.CharField(max_length=32)
    statut = models.CharField(max_length=12, choices=STATUT_CHOIX, default='confirme')  # Statut par défaut : 'confirme'
    reference = models.CharField(max_length=64, unique=True, null=True, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    confirme_le = models.DateTimeField( null=True, blank=True)  # Date de confirmation automatique

    def save(self, *args, **kwargs):
        # Générer une référence unique si aucune n'est fournie
        if not self.reference:
            self.reference = str(uuid.uuid4())
        # Définir le statut à 'confirme' et la date de confirmation
        if self.statut == 'confirme' and not self.confirme_le:
            self.confirme_le = timezone.now()

        super().save(*args, **kwargs)
     

    def __str__(self):
        return f"Dépôt de {self.montant} FC par {self.utilisateur.email} ({self.get_statut_display()})"




from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

def calculer_frais_retrait(montant):
    """
    Calcule les frais de retrait pour un montant donné en utilisant les tranches définies.
    """
    # Convertir en Decimal pour éviter les problèmes de comparaison
    montant_decimal = Decimal(str(montant))
    
    # Trouver la tranche active qui correspond au montant
    frais_tranche = FraisRetrait.objects.filter(
        actif=True,
        montant_min__lte=montant_decimal
    ).order_by('-montant_min').first()  # Prendre la tranche avec le montant_min le plus élevé qui est <= au montant
    
    if frais_tranche and frais_tranche.est_dans_la_tranche(montant_decimal):
        return frais_tranche.calculer_frais(montant_decimal)
    
    # Fallback: frais par défaut si aucune tranche ne correspond
    return Decimal('0.00')

class Retrait(models.Model):
    """Modèle pour les retraits."""
    STATUT_CHOIX = [
        ('demande', 'Demandé'),
        ('en_traitement', 'En traitement'),
        ('paye', 'Payé'),
        ('rejete', 'Rejeté'),
    ]

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='retraits', verbose_name="Utilisateur")
    montant = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant")
    methode = models.CharField(max_length=32, verbose_name="Méthode de retrait")
    destination = models.CharField(max_length=128, verbose_name="Destination (numéro de compte/téléphone)")
    statut = models.CharField(max_length=13, choices=STATUT_CHOIX, default='demande', verbose_name="Statut")
    cree_le = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    traite_le = models.DateTimeField(null=True, blank=True, verbose_name="Date de traitement")
    frais = models.DecimalField(
        max_digits=8, decimal_places=2, 
        default=0, verbose_name="Frais de retrait",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    montant_net = models.DecimalField(
        max_digits=12, decimal_places=2, 
        default=0, verbose_name="Montant net",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    def save(self, *args, **kwargs):
        """Surcharge de la méthode save pour calculer automatiquement les frais."""
        if not self.pk:  # Seulement pour les nouveaux retraits
            self.frais = calculer_frais_retrait(self.montant)
            self.montant_net = self.montant - self.frais
        super().save(*args, **kwargs)   

    def __str__(self):
        return f"Retrait de {self.montant} FC par {self.utilisateur.email} ({self.get_statut_display()})"

class FraisRetrait(models.Model):
    """Modèle pour gérer les frais de retrait progressifs."""
    
    TYPE_FRAIS_CHOIX = [
        ('pourcentage', 'Pourcentage'),
        ('fixe', 'Frais fixe'),
        ('mixte', 'Mixte (fixe + pourcentage)'),
    ]
    
    nom = models.CharField(max_length=100, verbose_name="Nom de la tranche de frais")
    type_frais = models.CharField(max_length=12, choices=TYPE_FRAIS_CHOIX, default='mixte', verbose_name="Type de frais")
    
    # Seuils pour la tranche
    montant_min = models.DecimalField(
        max_digits=12, decimal_places=2, 
        verbose_name="Montant minimum", 
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    montant_max = models.DecimalField(
        max_digits=12, decimal_places=2, 
        verbose_name="Montant maximum",
        null=True, blank=True,
        help_text="Laissez vide pour les tranches sans limite supérieure"
    )
    
    # Frais fixes
    frais_fixe = models.DecimalField(
        max_digits=8, decimal_places=2, 
        default=0, verbose_name="Frais fixe",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Frais en pourcentage
    frais_pourcentage = models.DecimalField(
        max_digits=5, decimal_places=2, 
        default=0, verbose_name="Frais en pourcentage",
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text="Pourcentage appliqué au montant du retrait"
    )
    
    frais_minimum = models.DecimalField(
        max_digits=8, decimal_places=2, 
        default=0, verbose_name="Frais minimum",
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Frais minimum à appliquer même si le calcul donne moins"
    )
    
    frais_maximum = models.DecimalField(
        max_digits=8, decimal_places=2, 
        null=True, blank=True, verbose_name="Frais maximum",
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Frais maximum à appliquer même si le calcul donne plus"
    )
    
    actif = models.BooleanField(default=True, verbose_name="Actif")
    ordre = models.PositiveIntegerField(default=0, verbose_name="Ordre d'application")
    
    cree_le = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    modifie_le = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    class Meta:
        verbose_name = "Frais de retrait"
        verbose_name_plural = "Frais de retrait"
        ordering = ['montant_min']  # Ordre par montant minimum croissant
    
    def __str__(self):
        return f"{self.nom} ({self.montant_min} - {self.montant_max or '∞'})"
    
    def calculer_frais(self, montant_retrait):
        """Calcule les frais pour un montant de retrait donné."""
        frais = Decimal('0.00')
        
        if self.type_frais == 'fixe':
            frais = self.frais_fixe
        
        elif self.type_frais == 'pourcentage':
            frais = (montant_retrait * self.frais_pourcentage) / Decimal('100.00')
        
        elif self.type_frais == 'mixte':
            frais = self.frais_fixe + ((montant_retrait * self.frais_pourcentage) / Decimal('100.00'))
        
        # Appliquer les limites
        if frais < self.frais_minimum:
            frais = self.frais_minimum
        
        if self.frais_maximum and frais > self.frais_maximum:
            frais = self.frais_maximum
        
        return frais.quantize(Decimal('0.01'))
    
    def montant_net(self, montant_retrait):
        """Calcule le montant net après déduction des frais."""
        frais = self.calculer_frais(montant_retrait)
        return (montant_retrait - frais).quantize(Decimal('0.01'))
    
    def est_dans_la_tranche(self, montant):
        """Vérifie si un montant est dans cette tranche de frais."""
        montant_decimal = Decimal(str(montant))
        
        if self.montant_max:
            return self.montant_min <= montant_decimal <= self.montant_max
        return montant_decimal >= self.montant_min