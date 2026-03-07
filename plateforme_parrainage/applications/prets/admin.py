from django.contrib import admin
from .models import (
    Pret, Remboursement, EligibiliteRetrait, 
    RetraitCredit, AjustementRemboursement
)


@admin.register(Pret)
class PretAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilisateur', 'montant', 'principal_restant', 'statut', 'date_debut', 'date_echeance')
    list_filter = ('statut',)
    search_fields = ('utilisateur__email', 'utilisateur__username')


@admin.register(Remboursement)
class RemboursementAdmin(admin.ModelAdmin):
    list_display = ('id', 'pret', 'montant', 'date', 'methode')
    search_fields = ('pret__utilisateur__email',)


@admin.register(EligibiliteRetrait)
class EligibiliteRetraitAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'utilisateur', 'nombre_filleuls_valides', 
        'nombre_filleuls_requis', 'est_eligible', 'derniere_verification'
    )
    list_filter = ('est_eligible', 'derniere_verification')
    search_fields = ('utilisateur__email', 'utilisateur__username')
    readonly_fields = ('nombre_filleuls_valides', 'est_eligible', 'derniere_verification')
    
    def save_model(self, request, obj, form, change):
        obj.verifier_eligibilite()
        super().save_model(request, obj, form, change)


@admin.register(RetraitCredit)
class RetraitCreditAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'utilisateur', 'montant_demande', 'montant_approuve',
        'statut', 'nombre_filleuls_valides', 'demande_le'
    )
    list_filter = ('statut', 'est_eligible', 'demande_le')
    search_fields = ('utilisateur__email', 'utilisateur__username')
    readonly_fields = (
        'montant_rembourse', 'montant_restant', 'est_eligible',
        'nombre_filleuls_valides', 'demande_le', 'approuve_le',
        'debute_le', 'termine_le'
    )
    fieldsets = (
        ('Informations Générales', {
            'fields': ('utilisateur', 'pret', 'statut')
        }),
        ('Montants', {
            'fields': ('montant_demande', 'montant_approuve', 'montant_rembourse', 'montant_restant')
        }),
        ('Éligibilité', {
            'fields': ('est_eligible', 'nombre_filleuls_valides', 'nombre_filleuls_requis')
        }),
        ('Remboursement', {
            'fields': ('pourcentage_remboursement',)
        }),
        ('Dates', {
            'fields': ('demande_le', 'approuve_le', 'debute_le', 'termine_le'),
            'classes': ('collapse',)
        }),
        ('Rejet', {
            'fields': ('raison_rejet',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approuver_retrait', 'rejeter_retrait']
    
    def approuver_retrait(self, request, queryset):
        for retrait in queryset:
            if retrait.statut == 'demande':
                retrait.approuver()
        self.message_user(request, "Retraits approuvés avec succès")
    approuver_retrait.short_description = "✅ Approuver les retraits sélectionnés"
    
    def rejeter_retrait(self, request, queryset):
        for retrait in queryset:
            if retrait.statut == 'demande':
                retrait.rejeter("Rejeté par l'administrateur")
        self.message_user(request, "Retraits rejetés avec succès")
    rejeter_retrait.short_description = "❌ Rejeter les retraits sélectionnés"


@admin.register(AjustementRemboursement)
class AjustementRemboursementAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'retrait_credit', 'montant_gain', 'montant_rembourse',
        'pourcentage_applique', 'statut', 'applique_le'
    )
    list_filter = ('statut', 'applique_le')
    search_fields = ('retrait_credit__utilisateur__email',)
    readonly_fields = ('applique_le',)
    
    actions = ['appliquer_ajustement']
    
    def appliquer_ajustement(self, request, queryset):
        for ajustement in queryset:
            if ajustement.statut == 'en_attente':
                ajustement.appliquer()
        self.message_user(request, "Ajustements appliqués avec succès")
    appliquer_ajustement.short_description = "Appliquer les ajustements sélectionnés"
