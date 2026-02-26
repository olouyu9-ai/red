from django.db import models
from django.conf import settings

from django.db import models
from django.conf import settings





class BonusParrainage(models.Model):
    parrain = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bonus_parrainages')
    filleul = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bonus_parrain')
    achat = models.OneToOneField('produits.Achat', on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    pourcentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    est_premier_achat = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['parrain', 'filleul']  # Un seul bonus par paire

    def __str__(self):
        return f"Bonus unique - {self.montant} FC"