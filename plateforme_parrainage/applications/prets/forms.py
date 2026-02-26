from django import forms
from decimal import Decimal
from .models import Pret


# Montants proposés en USD (chaînes converties en Decimal dans clean_montant)
MONTANT_CHOICES = [
    ('50.00', '50'),
    ('100.00', '100'),
    
]


class DemandePretForm(forms.ModelForm):
    montant = forms.ChoiceField(choices=MONTANT_CHOICES, label='Montant (USD)')

    class Meta:
        model = Pret
        fields = ['montant', 'taux_annuel', 'duree_mois']

    def clean_montant(self):
        montant = self.cleaned_data.get('montant')
        try:
            montant_dec = Decimal(str(montant))
        except Exception:
            raise forms.ValidationError('Montant invalide.')
        if montant_dec <= Decimal('0.00'):
            raise forms.ValidationError('Le montant doit être supérieur à 0.')
        return montant_dec

    def clean_duree_mois(self):
        duree = self.cleaned_data.get('duree_mois')
        if duree is None or duree <= 0:
            raise forms.ValidationError('La durée doit être un nombre de mois positif.')
        return duree
