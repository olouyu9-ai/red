from django.contrib import admin
from django.db.models import Sum, Count, Q
from django.http import FileResponse
from django.template.response import TemplateResponse
from django.urls import path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
import io
from datetime import datetime
from decimal import Decimal

from .models import TransactionPortefeuille, CapitalClient


@admin.register(TransactionPortefeuille)
class TransactionPortefeuilleAdmin(admin.ModelAdmin):
    """Configuration de l'administration pour les transactions du portefeuille."""

    list_display = ("utilisateur", "type", "montant", "solde_apres", "reference", "cree_le")
    search_fields = ("utilisateur__email", "reference", "type")
    list_filter = ("type", "cree_le")
    ordering = ("-cree_le",)
    readonly_fields = ("cree_le", "reference", "solde_apres")
    actions = ["exporter_pdf"]
    change_list_template = "transactionportefeuille_change_list.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("utilisateur")

    def changelist_view(self, request, extra_context=None):
        """Injecter les totaux dans le contexte admin."""
        response = super().changelist_view(request, extra_context=extra_context)

        # Vérifier si la réponse est un TemplateResponse (et non un FileResponse)
        if hasattr(response, 'context_data') and response.context_data is not None:
            try:
                qs = response.context_data["cl"].queryset
                totals = qs.aggregate(
                    total_montant=Sum("montant"),
                    total_transactions=Count("id"),
                    total_depot=Sum("montant", filter=Q(type="depot")),
                    total_retrait=Sum("montant", filter=Q(type="retrait")),
                    total_gain_quotidien=Sum("montant", filter=Q(type="gain_quotidien")),
                    total_bonus_parrainage=Sum("montant", filter=Q(type="bonus_parrainage")),
                    total_achat=Sum("montant", filter=Q(type="achat")),
                    total_bonus_inscription=Sum("montant", filter=Q(type="bonus_inscription")),
                    total_capital=Sum("montant", filter=Q(type="capital")),
                )

                # Calculer le solde net (entrées - sorties)
                entrées = ((totals.get('total_depot', 0) or 0) +
                          (totals.get('total_gain_quotidien', 0) or 0) +
                          (totals.get('total_bonus_parrainage', 0) or 0) +
                          (totals.get('total_bonus_inscription', 0) or 0) +
                          (totals.get('total_capital', 0) or 0))

                sorties = ((totals.get('total_retrait', 0) or 0) +
                          (totals.get('total_achat', 0) or 0))

                totals['solde_net'] = entrées - sorties
                totals['total_entrees'] = entrées
                totals['total_sorties'] = sorties

                response.context_data["totaux"] = totals
            except (AttributeError, KeyError):
                totals = {}
                response.context_data["totaux"] = totals

        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('statistiques/', self.admin_site.admin_view(self.statistiques_view),
                 name='transactionportefeuille_statistiques'),
        ]
        return custom_urls + urls

    def statistiques_view(self, request):
        """Vue personnalisée pour afficher des statistiques détaillées."""
        # Récupérer toutes les transactions
        transactions = TransactionPortefeuille.objects.all()

        # Calculer les statistiques
        stats = transactions.aggregate(
            total_montant=Sum("montant"),
            total_transactions=Count("id"),
            total_depot=Sum("montant", filter=Q(type="depot")),
            total_retrait=Sum("montant", filter=Q(type="retrait")),
            total_gain_quotidien=Sum("montant", filter=Q(type="gain_quotidien")),
            total_bonus_parrainage=Sum("montant", filter=Q(type="bonus_parrainage")),
            total_achat=Sum("montant", filter=Q(type="achat")),
            total_bonus_inscription=Sum("montant", filter=Q(type="bonus_inscription")),
            total_capital=Sum("montant", filter=Q(type="capital")),
        )

        # Calculer le solde net
        entrées = ((stats.get('total_depot', 0) or 0) +
                  (stats.get('total_gain_quotidien', 0) or 0) +
                  (stats.get('total_bonus_parrainage', 0) or 0) +
                  (stats.get('total_bonus_inscription', 0) or 0) +
                  (stats.get('total_capital', 0) or 0))

        sorties = ((stats.get('total_retrait', 0) or 0) +
                  (stats.get('total_achat', 0) or 0))

        stats['solde_net'] = entrées - sorties
        stats['total_entrees'] = entrées
        stats['total_sorties'] = sorties

        # Par utilisateur
        par_utilisateur = transactions.values('utilisateur__email').annotate(
            total=Sum('montant'),
            count=Count('id')
        ).order_by('-total')

        # Par type
        par_type = transactions.values('type').annotate(
            total=Sum('montant'),
            count=Count('id')
        ).order_by('type')

        context = {
            **self.admin_site.each_context(request),
            'title': 'Statistiques des transactions',
            'stats': stats,
            'par_utilisateur': par_utilisateur,
            'par_type': par_type,
            'opts': self.model._meta,
        }

        return TemplateResponse(request, 'transactionportefeuille_statistiques.html', context)

    # === Export PDF amélioré avec ReportLab ===
    def exporter_pdf(self, request, queryset):
        """Exporter un rapport structuré (journalier/mensuel)."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=30)
        elements = []
        styles = getSampleStyleSheet()

        # Titre
        title = Paragraph("Rapport des Transactions du Portefeuille", styles['Title'])
        elements.append(title)

        # Date de génération
        date_str = f"Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        date_para = Paragraph(date_str, styles['Normal'])
        elements.append(date_para)

        # Espacement
        elements.append(Paragraph("<br/>", styles['Normal']))

        # Préparer les données du tableau
        data = [['Utilisateur', 'Type', 'Montant', 'Solde Après', 'Référence', 'Date']]

        total_entrees = Decimal('0')
        total_sorties = Decimal('0')

        for obj in queryset:
            data.append([
                str(obj.utilisateur),
                obj.get_type_display(),
                f"{obj.montant:.2f}",
                f"{obj.solde_apres:.2f}",
                obj.reference or "-",
                obj.cree_le.strftime('%d/%m/%Y %H:%M')
            ])

            # Calculer entrées et sorties séparément
            if obj.type in ['depot', 'gain_quotidien', 'bonus_parrainage', 'bonus_inscription', 'capital']:
                total_entrees += Decimal(obj.montant)
            elif obj.type in ['retrait', 'achat']:
                total_sorties += Decimal(obj.montant)

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
        elements.append(Paragraph(f"Nombre total de transactions : {queryset.count()}", styles['Normal']))
        elements.append(Paragraph(f"Total des entrées : {total_entrees:.2f} FC", styles['Normal']))
        elements.append(Paragraph(f"Total des sorties : {total_sorties:.2f} FC", styles['Normal']))
        elements.append(Paragraph(f"Solde net : {(total_entrees - total_sorties):.2f} FC", styles['Normal']))

        # Générer le PDF
        doc.build(elements)
        buffer.seek(0)

        return FileResponse(buffer, as_attachment=True, filename="rapport_transactions.pdf")

    exporter_pdf.short_description = "Exporter le rapport en PDF"


@admin.register(CapitalClient)
class CapitalClientAdmin(admin.ModelAdmin):
    """Configuration de l'administration pour le capital des clients."""
    
    list_display = ("utilisateur", "capital", "date_creation")
    search_fields = ("utilisateur__email", "utilisateur__username")
    list_filter = ("date_creation",)
    ordering = ("-date_creation",)
    readonly_fields = ("date_creation",)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("utilisateur")


# Fonctions utilitaires pour calculer les bonus et capital
def calculer_bonus_inscription(utilisateur):
    """Calcule le total des bonus d'inscription pour un utilisateur"""
    return TransactionPortefeuille.objects.filter(
        utilisateur=utilisateur, 
        type='bonus_inscription'
    ).aggregate(total=Sum('montant'))['total'] or Decimal('0')

def calculer_capital_total(utilisateur):
    """Calcule le total des transactions de capital pour un utilisateur"""
    return TransactionPortefeuille.objects.filter(
        utilisateur=utilisateur, 
        type='capital'
    ).aggregate(total=Sum('montant'))['total'] or Decimal('0')