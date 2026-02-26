from django.contrib import admin
from django.db.models import Sum, Count, Q
from django.http import FileResponse
from django.template.response import TemplateResponse
from django.urls import path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io
from datetime import datetime
from decimal import Decimal

from .models import Produit, Achat, GainQuotidien




@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    """Administration des produits."""


    list_display = ("nom", "prix", "duree_jours", "taux_quotidien", "est_actif")
    search_fields = ("nom", "description")
    list_filter = ("est_actif",)
    ordering = ("nom",)
    actions = ["exporter_pdf_produits", "activer_produits", "desactiver_produits"]
    change_list_template = "produit_change_list.html"

    def changelist_view(self, request, extra_context=None):
        """Injecter les totaux dans le contexte admin."""
        response = super().changelist_view(request, extra_context=extra_context)

        if hasattr(response, 'context_data') and response.context_data is not None:
            try:
                qs = response.context_data["cl"].queryset
                totals = qs.aggregate(
                    total_produits=Count("id"),
                    produits_actifs=Count("id", filter=Q(est_actif=True)),
                    produits_inactifs=Count("id", filter=Q(est_actif=False)),
                    valeur_total=Sum("prix"),
                )
                response.context_data["totaux"] = totals
            except (AttributeError, KeyError):
                totals = {}
                response.context_data["totaux"] = totals

        return response

    def activer_produits(self, request, queryset):
        """Activer les produits sélectionnés."""
        updated = queryset.update(est_actif=True)
        self.message_user(request, f"{updated} produit(s) activé(s).")
    activer_produits.short_description = "Activer les produits"

    def desactiver_produits(self, request, queryset):
        """Désactiver les produits sélectionnés."""
        updated = queryset.update(est_actif=False)
        self.message_user(request, f"{updated} produit(s) désactivé(s).")
    desactiver_produits.short_description = "Désactiver les produits"

    def exporter_pdf_produits(self, request, queryset):
        """Exporter un rapport des produits en PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=30)
        elements = []
        styles = getSampleStyleSheet()

        # Titre
        title = Paragraph("Rapport des Produits", styles['Title'])
        elements.append(title)

        # Date de génération
        date_str = f"Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        date_para = Paragraph(date_str, styles['Normal'])
        elements.append(date_para)

        elements.append(Paragraph("<br/>", styles['Normal']))

        # Préparer les données du tableau
        data = [['Nom', 'Prix', 'Durée (jours)', 'Taux quotidien', 'Statut']]

        for obj in queryset:
            data.append([
                obj.nom,
                f"{obj.prix:.2f} FC",
                str(obj.duree_jours),
                f"{obj.taux_quotidien * 100}%",
                "ACTIF" if obj.est_actif else "INACTIF"
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
        elements.append(Paragraph(f"Nombre total de produits : {queryset.count()}", styles['Normal']))

        actifs = queryset.filter(est_actif=True).count()
        elements.append(Paragraph(f"Produits actifs : {actifs}", styles['Normal']))
        elements.append(Paragraph(f"Produits inactifs : {queryset.count() - actifs}", styles['Normal']))

        # Générer le PDF
        doc.build(elements)
        buffer.seek(0)

        return FileResponse(buffer, as_attachment=True, filename="rapport_produits.pdf")

    exporter_pdf_produits.short_description = "Exporter les produits en PDF"


@admin.register(Achat)
class AchatAdmin(admin.ModelAdmin):
    """Administration des achats."""

    list_display = ("utilisateur", "produit", "prix_au_moment_achat", "date_debut", "date_fin", "statut", "jours_payes")
    search_fields = ("utilisateur__email", "produit__nom")
    list_filter = ("statut", "date_debut", "produit")
    ordering = ("-date_debut",)
    readonly_fields = ("prix_au_moment_achat", "date_debut")
    actions = ["exporter_pdf_achats", "marquer_comme_actif", "marquer_comme_expire", "marquer_comme_annule"]
    change_list_template = "achat_change_list.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("utilisateur", "produit")

    def changelist_view(self, request, extra_context=None):
        """Injecter les totaux dans le contexte admin."""
        response = super().changelist_view(request, extra_context=extra_context)

        if hasattr(response, 'context_data') and response.context_data is not None:
            try:
                qs = response.context_data["cl"].queryset
                totals = qs.aggregate(
                    total_achats=Count("id"),
                    total_investissement=Sum("prix_au_moment_achat"),
                    achats_actifs=Count("id", filter=Q(statut='actif')),
                    achats_expires=Count("id", filter=Q(statut='expire')),
                    achats_annules=Count("id", filter=Q(statut='annule')),
                    investissement_actif=Sum("prix_au_moment_achat", filter=Q(statut='actif')),
                    investissement_expire=Sum("prix_au_moment_achat", filter=Q(statut='expire')),
                    investissement_annule=Sum("prix_au_moment_achat", filter=Q(statut='annule')),
                )
                response.context_data["totaux"] = totals
            except (AttributeError, KeyError):
                totals = {}
                response.context_data["totaux"] = totals

        return response

    def marquer_comme_actif(self, request, queryset):
        """Marquer les achats sélectionnés comme actifs."""
        updated = queryset.update(statut='actif')
        self.message_user(request, f"{updated} achat(s) marqué(s) comme actif(s).")
    marquer_comme_actif.short_description = "Marquer comme actif"

    def marquer_comme_expire(self, request, queryset):
        """Marquer les achats sélectionnés comme expirés."""
        updated = queryset.update(statut='expire')
        self.message_user(request, f"{updated} achat(s) marqué(s) comme expiré(s).")
    marquer_comme_expire.short_description = "Marquer comme expiré"

    def marquer_comme_annule(self, request, queryset):
        """Marquer les achats sélectionnés comme annulés."""
        updated = queryset.update(statut='annule')
        self.message_user(request, f"{updated} achat(s) marqué(s) comme annulé(s).")
    marquer_comme_annule.short_description = "Marquer comme annulé"

    def exporter_pdf_achats(self, request, queryset):
        """Exporter un rapport des achats en PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=30)
        elements = []
        styles = getSampleStyleSheet()

        # Titre
        title = Paragraph("Rapport des Achats", styles['Title'])
        elements.append(title)

        # Date de génération
        date_str = f"Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        date_para = Paragraph(date_str, styles['Normal'])
        elements.append(date_para)

        elements.append(Paragraph("<br/>", styles['Normal']))

        # Préparer les données du tableau
        data = [['Utilisateur', 'Produit', 'Prix', 'Date début', 'Date fin', 'Statut', 'Jours payés']]

        total_investissement = Decimal('0.00')
        for obj in queryset:
            data.append([
                str(obj.utilisateur),
                obj.produit.nom,
                f"{obj.prix_au_moment_achat:.2f} FC",
                obj.date_debut.strftime('%d/%m/%Y'),
                obj.date_fin.strftime('%d/%m/%Y') if obj.date_fin else "-",
                obj.get_statut_display(),
                str(obj.jours_payes)
            ])
            total_investissement += obj.prix_au_moment_achat

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
        elements.append(Paragraph(f"Nombre total d'achats : {queryset.count()}", styles['Normal']))
        elements.append(Paragraph(f"Investissement total : {total_investissement:.2f} FC", styles['Normal']))

        actifs = queryset.filter(statut='actif').count()
        expires = queryset.filter(statut='expire').count()
        annules = queryset.filter(statut='annule').count()

        elements.append(Paragraph(f"Achats actifs : {actifs}", styles['Normal']))
        elements.append(Paragraph(f"Achats expirés : {expires}", styles['Normal']))
        elements.append(Paragraph(f"Achats annulés : {annules}", styles['Normal']))

        # Générer le PDF
        doc.build(elements)
        buffer.seek(0)

        return FileResponse(buffer, as_attachment=True, filename="rapport_achats.pdf")

    exporter_pdf_achats.short_description = "Exporter les achats en PDF"


@admin.register(GainQuotidien)
class GainQuotidienAdmin(admin.ModelAdmin):
    """Administration des gains quotidiens."""

    list_display = ("achat", "jour", "montant", "poste", "poste_le")
    search_fields = ("achat__utilisateur__email", "achat__produit__nom")
    list_filter = ("poste", "jour")
    ordering = ("-jour",)
    readonly_fields = ("achat", "jour", "montant")
    actions = ["exporter_pdf_gains", "marquer_comme_poste", "marquer_comme_non_poste"]
    change_list_template = "gainquotidien_change_list.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("achat__utilisateur", "achat__produit")

    def changelist_view(self, request, extra_context=None):
        """Injecter les totaux dans le contexte admin."""
        response = super().changelist_view(request, extra_context=extra_context)

        if hasattr(response, 'context_data') and response.context_data is not None:
            try:
                qs = response.context_data["cl"].queryset
                totals = qs.aggregate(
                    total_gains=Count("id"),
                    total_montant=Sum("montant"),
                    gains_poste=Count("id", filter=Q(poste=True)),
                    gains_non_poste=Count("id", filter=Q(poste=False)),
                    montant_poste=Sum("montant", filter=Q(poste=True)),
                    montant_non_poste=Sum("montant", filter=Q(poste=False)),
                )
                response.context_data["totaux"] = totals
            except (AttributeError, KeyError):
                totals = {}
                response.context_data["totaux"] = totals

        return response

    def marquer_comme_poste(self, request, queryset):
        """Marquer les gains sélectionnés comme postés."""
        updated = queryset.update(poste=True, poste_le=datetime.now())
        self.message_user(request, f"{updated} gain(s) marqué(s) comme posté(s).")
    marquer_comme_poste.short_description = "Marquer comme posté"

    def marquer_comme_non_poste(self, request, queryset):
        """Marquer les gains sélectionnés comme non postés."""
        updated = queryset.update(poste=False, poste_le=None)
        self.message_user(request, f"{updated} gain(s) marqué(s) comme non posté(s).")
    marquer_comme_non_poste.short_description = "Marquer comme non posté"

    def exporter_pdf_gains(self, request, queryset):
        """Exporter un rapport des gains en PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=30)
        elements = []
        styles = getSampleStyleSheet()

        # Titre
        title = Paragraph("Rapport des Gains Quotidiens", styles['Title'])
        elements.append(title)

        # Date de génération
        date_str = f"Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        date_para = Paragraph(date_str, styles['Normal'])
        elements.append(date_para)

        elements.append(Paragraph("<br/>", styles['Normal']))

        # Préparer les données du tableau
        data = [['Utilisateur', 'Produit', 'Jour', 'Montant', 'Statut', 'Date postage']]

        total_montant = Decimal('0.00')
        for obj in queryset:
            data.append([
                str(obj.achat.utilisateur),
                obj.achat.produit.nom,
                obj.jour.strftime('%d/%m/%Y'),
                f"{obj.montant:.2f} FC",
                "POSTÉ" if obj.poste else "NON POSTÉ",
                obj.poste_le.strftime('%d/%m/%Y %H:%M') if obj.poste_le else "-"
            ])
            total_montant += obj.montant

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
        elements.append(Paragraph(f"Nombre total de gains : {queryset.count()}", styles['Normal']))
        elements.append(Paragraph(f"Montant total : {total_montant:.2f} FC", styles['Normal']))

        postes = queryset.filter(poste=True).count()
        elements.append(Paragraph(f"Gains postés : {postes}", styles['Normal']))
        elements.append(Paragraph(f"Gains non postés : {queryset.count() - postes}", styles['Normal']))

        # Générer le PDF
        doc.build(elements)
        buffer.seek(0)

        return FileResponse(buffer, as_attachment=True, filename="rapport_gains_quotidiens.pdf")

    exporter_pdf_gains.short_description = "Exporter les gains en PDF"


