from django.db import models
from decimal import Decimal

from plateforme_parrainage import settings

class Order(models.Model):
    customer_name = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    # le client saisit ce code après avoir payé
    reference_code = models.CharField(max_length=60, unique=True, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # Nouveau champ pour l'utilisateur
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='orders')

    def __str__(self):
        status = "PAYÉE" if self.is_paid else "EN ATTENTE"
        return f"{self.reference_code or '—'} • {self.amount} CDF • {status}"

class PaymentMessage(models.Model):
    sms_text = models.TextField()
    sender = models.CharField(max_length=50, blank=True)   # numéro expéditeur si dispo
    received_at = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    reference = models.CharField(max_length=60, unique=True, null=True, blank=True)
    processed = models.BooleanField(default=False)
    error = models.TextField(blank=True)

    def __str__(self):
        return f"{self.reference or '—'} • {self.amount or '—'} CDF"