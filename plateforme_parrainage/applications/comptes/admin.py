from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Sum, Count, Q
from django.http import FileResponse
from django.template.response import TemplateResponse
from django.urls import path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io
from datetime import datetime, timezone
from django.utils import timezone
from decimal import Decimal

from .models import Utilisateur, ProfilUtilisateur , Video
from applications.portefeuille.models import TransactionPortefeuille

admin.site.register(Video)

@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    
    """Administration des utilisateurs."""

    list_display = ("email", "telephone", "first_name", "last_name", "date_joined", "is_active")
    search_fields = ("email", "telephone", "first_name", "last_name")
    list_filter = ("is_active", "date_joined", "is_staff")
    ordering = ("-date_joined",)
    actions = ["exporter_pdf_utilisateurs", "activer_utilisateurs", "desactiver_utilisateurs"]
    change_list_template = "utilisateur_change_list.html"

    # Ajouter le champ telephone aux fieldsets
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'telephone', "mot_de_passe_clair")}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'telephone', 'password1', 'password2', "mot_de_passe_clair"),
        }),
    )

    def changelist_view(self, request, extra_context=None):
        """Injecter les totaux dans le contexte admin."""
        response = super().changelist_view(request, extra_context=extra_context)

        if hasattr(response, 'context_data') and response.context_data is not None:
            try:
                qs = response.context_data["cl"].queryset
                totals = qs.aggregate(
                    total_utilisateurs=Count("id"),
                    utilisateurs_actifs=Count("id", filter=Q(is_active=True)),
                    utilisateurs_inactifs=Count("id", filter=Q(is_active=False)),
                    staff_members=Count("id", filter=Q(is_staff=True)),
                    superusers=Count("id", filter=Q(is_superuser=True)),
                )
                response.context_data["totaux"] = totals
            except (AttributeError, KeyError):
                totals = {}
                response.context_data["totaux"] = totals

        return response

    def activer_utilisateurs(self, request, queryset):
        """Activer les utilisateurs sélectionnés."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} utilisateur(s) activé(s).")
    activer_utilisateurs.short_description = "Activer les utilisateurs"

    def desactiver_utilisateurs(self, request, queryset):
        """Désactiver les utilisateurs sélectionnés."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} utilisateur(s) désactivé(s).")
    desactiver_utilisateurs.short_description = "Désactiver les utilisateurs"

    def exporter_pdf_utilisateurs(self, request, queryset):
        """Exporter un rapport des utilisateurs en PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=30)
        elements = []
        styles = getSampleStyleSheet()

        # Titre
        title = Paragraph("Rapport des Utilisateurs", styles['Title'])
        elements.append(title)

        # Date de génération
        date_str = f"Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        date_para = Paragraph(date_str, styles['Normal'])
        elements.append(date_para)

        elements.append(Paragraph("<br/>", styles['Normal']))

        # Préparer les données du tableau
        data = [['Utilisateur', 'Téléphone', 'Nom', 'Prénom', 'Date inscription', 'Statut']]

        for obj in queryset:
            data.append([
                obj.email,
                obj.telephone,
                obj.last_name or "-",
                obj.first_name or "-",
                obj.date_joined.strftime('%d/%m/%Y'),
                "ACTIF" if obj.is_active else "INACTIF"
            ])

        # Créer le tableau
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)

        # Ajouter les totaux
        elements.append(Paragraph("<br/>", styles['Normal']))
        elements.append(Paragraph(f"Nombre total d'utilisateurs : {queryset.count()}", styles['Normal']))

        actifs = queryset.filter(is_active=True).count()
        elements.append(Paragraph(f"Utilisateurs actifs : {actifs}", styles['Normal']))
        elements.append(Paragraph(f"Utilisateurs inactifs : {queryset.count() - actifs}", styles['Normal']))

        staff = queryset.filter(is_staff=True).count()
        elements.append(Paragraph(f"Membres staff : {staff}", styles['Normal']))

        # Générer le PDF
        doc.build(elements)
        buffer.seek(0)


        return FileResponse(buffer, as_attachment=True, filename="rapport_utilisateurs.pdf")

    exporter_pdf_utilisateurs.short_description = "Exporter les utilisateurs en PDF"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('statistiques/', self.admin_site.admin_view(self.statistiques_view),
                 name='utilisateur_statistiques'),
        ]
        return custom_urls + urls

    def statistiques_view(self, request):
        """Vue personnalisée pour afficher des statistiques détaillées."""
        # Récupérer tous les utilisateurs
        utilisateurs = Utilisateur.objects.all()

        # Calculer les statistiques
        stats = utilisateurs.aggregate(
            total_utilisateurs=Count("id"),
            utilisateurs_actifs=Count("id", filter=Q(is_active=True)),
            utilisateurs_inactifs=Count("id", filter=Q(is_active=False)),
            staff_members=Count("id", filter=Q(is_staff=True)),
            superusers=Count("id", filter=Q(is_superuser=True)),
        )

        # Par mois d'inscription
        from django.db.models.functions import TruncMonth
        par_mois = utilisateurs.annotate(mois=TruncMonth('date_joined')).values('mois').annotate(
            count=Count('id')
        ).order_by('mois')

        context = {
            **self.admin_site.each_context(request),
            'title': 'Statistiques des utilisateurs',
            'stats': stats,
            'par_mois': par_mois,
            'opts': self.model._meta,
        }

        return TemplateResponse(request, 'utilisateur_statistiques.html', context)


@admin.register(ProfilUtilisateur)
class ProfilUtilisateurAdmin(admin.ModelAdmin):
    """Administration des profils utilisateurs."""

    list_display = ("utilisateur", "code_parrainage", "parrain", "niveau_kyc", "double_authentification_active")
    search_fields = ("utilisateur__email", "code_parrainage", "parrain__email")
    list_filter = ("niveau_kyc", "double_authentification_active")
    readonly_fields = ("code_parrainage",)
    actions = ["exporter_pdf_profils", "augmenter_niveau_kyc", "reduire_niveau_kyc", "activer_2fa", "desactiver_2fa"]
    change_list_template = "profilutilisateur_change_list.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("utilisateur", "parrain")

    def changelist_view(self, request, extra_context=None):
        """Injecter les totaux dans le contexte admin."""
        response = super().changelist_view(request, extra_context=extra_context)

        if hasattr(response, 'context_data') and response.context_data is not None:
            try:
                qs = response.context_data["cl"].queryset
                totals = qs.aggregate(
                    total_profils=Count("id"),
                    avec_parrain=Count("id", filter=Q(parrain__isnull=False)),
                    sans_parrain=Count("id", filter=Q(parrain__isnull=True)),
                    deux_fa_actif=Count("id", filter=Q(double_authentification_active=True)),
                    deux_fa_inactif=Count("id", filter=Q(double_authentification_active=False)),
                )

                # Statistiques par niveau KYC
                niveaux_kyc = {}
                for niveau in range(0, 4):  # Supposons 4 niveaux KYC (0-3)
                    count = qs.filter(niveau_kyc=niveau).count()
                    niveaux_kyc[f'niveau_{niveau}'] = count

                totals.update(niveaux_kyc)
                response.context_data["totaux"] = totals
            except (AttributeError, KeyError):
                totals = {}
                response.context_data["totaux"] = totals

        return response

    def augmenter_niveau_kyc(self, request, queryset):
        """Augmenter le niveau KYC des profils sélectionnés."""
        for profil in queryset:
            if profil.niveau_kyc < 3:  # Supposons que 3 est le niveau max
                profil.niveau_kyc += 1
                profil.save()
        self.message_user(request, f"Niveau KYC augmenté pour {queryset.count()} profil(s).")
    augmenter_niveau_kyc.short_description = "Augmenter le niveau KYC"

    def reduire_niveau_kyc(self, request, queryset):
        """Réduire le niveau KYC des profils sélectionnés."""
        for profil in queryset:
            if profil.niveau_kyc > 0:
                profil.niveau_kyc -= 1
                profil.save()
        self.message_user(request, f"Niveau KYC réduit pour {queryset.count()} profil(s).")
    reduire_niveau_kyc.short_description = "Réduire le niveau KYC"

    def activer_2fa(self, request, queryset):
        """Activer la 2FA pour les profils sélectionnés."""
        updated = queryset.update(double_authentification_active=True)
        self.message_user(request, f"2FA activée pour {updated} profil(s).")
    activer_2fa.short_description = "Activer la 2FA"

    def desactiver_2fa(self, request, queryset):
        """Désactiver la 2FA pour les profils sélectionnés."""
        updated = queryset.update(double_authentification_active=False)
        self.message_user(request, f"2FA désactivée pour {updated} profil(s).")
    desactiver_2fa.short_description = "Désactiver la 2FA"

    def exporter_pdf_profils(self, request, queryset):
        """Exporter un rapport des profils en PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=30)
        elements = []
        styles = getSampleStyleSheet()

        # Titre
        title = Paragraph("Rapport des Profils Utilisateurs", styles['Title'])
        elements.append(title)

        # Date de génération
        date_str = f"Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        date_para = Paragraph(date_str, styles['Normal'])
        elements.append(date_para)

        elements.append(Paragraph("<br/>", styles['Normal']))

        # Préparer les données du tableau
        data = [['Utilisateur', 'Code Parrainage', 'Parrain', 'Niveau KYC', '2FA', 'Solde']]

        for obj in queryset:
            try:
                solde = obj.get_solde()
            except:
                solde = Decimal('0.00')

            data.append([
                str(obj.utilisateur),
                obj.code_parrainage,
                str(obj.parrain) if obj.parrain else "-",
                str(obj.niveau_kyc),
                "ACTIVE" if obj.double_authentification_active else "INACTIVE",
                f"{solde:.2f} FC"
            ])

        # Créer le tableau
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)

        # Ajouter les totaux
        elements.append(Paragraph("<br/>", styles['Normal']))
        elements.append(Paragraph(f"Nombre total de profils : {queryset.count()}", styles['Normal']))

        avec_parrain = queryset.filter(parrain__isnull=False).count()
        elements.append(Paragraph(f"Profils avec parrain : {avec_parrain}", styles['Normal']))
        elements.append(Paragraph(f"Profils sans parrain : {queryset.count() - avec_parrain}", styles['Normal']))

        deux_fa_actif = queryset.filter(double_authentification_active=True).count()
        elements.append(Paragraph(f"2FA activée : {deux_fa_actif}", styles['Normal']))

        # Générer le PDF
        doc.build(elements)
        buffer.seek(0)

        return FileResponse(buffer, as_attachment=True, filename="rapport_profils.pdf")

    exporter_pdf_profils.short_description = "Exporter les profils en PDF"