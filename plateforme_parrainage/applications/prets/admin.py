from django.contrib import admin
from .models import Pret, Remboursement


@admin.register(Pret)
class PretAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilisateur', 'montant', 'principal_restant', 'statut', 'date_debut', 'date_echeance')
    list_filter = ('statut',)
    search_fields = ('utilisateur__email', 'utilisateur__username')


@admin.register(Remboursement)
class RemboursementAdmin(admin.ModelAdmin):
    list_display = ('id', 'pret', 'montant', 'date', 'methode')
    search_fields = ('pret__utilisateur__email',)
