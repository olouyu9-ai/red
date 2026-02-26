from django import forms
from .models import Utilisateur


class UtilisateurUpdateForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ['first_name', 'last_name', 'email', 'telephone', 'date_naissance', 'adresse']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Friendly labels in French
        self.fields['first_name'].label = 'Prénom'
        self.fields['last_name'].label = 'Nom'
        self.fields['email'].label = 'Email'
        self.fields['telephone'].label = 'Téléphone'

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        if not telephone:
            return telephone
        qs = Utilisateur.objects.filter(telephone=telephone)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return telephone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email
        qs = Utilisateur.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email
