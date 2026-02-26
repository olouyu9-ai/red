from django.contrib import admin
from django.db.models import Sum, Count
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
from django.http import HttpResponse
from datetime import datetime
from django.utils import timezone
from django.shortcuts import redirect
from decimal import Decimal
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.conf import settings

from .models import Depot, Retrait, FraisRetrait



from django.contrib import admin
from django.db.models import Sum, Count, Q
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
from django.http import HttpResponse
from datetime import datetime
from django.utils import timezone
from django.shortcuts import redirect
from decimal import Decimal
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from django.conf import settings

from .models import Depot, Retrait, FraisRetrait

def export_depots_pdf(modeladmin, request, queryset):
    """
    Export les dépôts sélectionnés en PDF using ReportLab
    """
    date_expo = timezone.now().strftime('%d/%m/%Y')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{date_expo}-depots_export.pdf"'

    # Create PDF buffer
    buffer = io.BytesIO()

    # Create PDF document - using landscape orientation for better table display
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []

    # Title
    styles = getSampleStyleSheet()
    title = Paragraph("Rapport des Dépôts", styles['Title'])
    elements.append(title)

    # Date d'exportation
    date_export = Paragraph(f"Date d'exportation: {timezone.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal'])
    elements.append(date_export)
    elements.append(Spacer(1, 12))

    # Prepare data for table
    data = [['Utilisateur', 'Montant', 'Méthode', 'Statut', 'Référence', 'Date Création', 'Date Confirmation']]

    for depot in queryset:
        data.append([
            str(depot.utilisateur.email),
            f"{depot.montant} FC",
            depot.methode,
            depot.get_statut_display(),
            depot.reference,
            depot.cree_le.strftime('%Y-%m-%d %H:%M'),
            depot.confirme_le.strftime('%Y-%m-%d %H:%M') if depot.confirme_le else 'N/A'
        ])

    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))

    # Totaux
    total_montant = sum(depot.montant for depot in queryset)
    total_confirme = sum(depot.montant for depot in queryset if depot.statut == 'confirme')
    total_en_attente = sum(depot.montant for depot in queryset if depot.statut == 'en_attente')

    totals_data = [
        ['TOTAL GÉNÉRAL:', f'{total_montant} FC', '', '', '', '', ''],
        ['Total Confirmé:', f'{total_confirme} FC', '', '', '', '', ''],
        ['Total En Attente:', f'{total_en_attente} FC', '', '', '', '', '']
    ]

    totals_table = Table(totals_data)
    totals_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('BACKGROUND', (0, 1), (-1, 1), colors.darkgreen),
        ('BACKGROUND', (0, 2), (-1, 2), colors.darkorange),
        ('TEXTCOLOR', (0, 0), (-1, 2), colors.white),
        ('ALIGN', (0, 0), (-1, 2), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 2), 10),
        ('GRID', (0, 0), (-1, 2), 1, colors.black)
    ]))

    elements.append(totals_table)

    # Build PDF
    doc.build(elements)

    # Get PDF value from buffer and return response
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response

export_depots_pdf.short_description = "Exporter les dépôts sélectionnés en PDF"


def export_retraits_pdf(modeladmin, request, queryset):
    """
    Export les retraits sélectionnés en PDF using ReportLab
    """
    date_expo = timezone.now().strftime('%d/%m/%Y')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{date_expo}-retraits_export.pdf"'

    # Create PDF buffer
    buffer = io.BytesIO()

    # Create PDF document - using landscape orientation for better table display
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []

    # Title
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    title = Paragraph("RAPPORT DES RETRAITS", title_style)
    elements.append(title)

    # Date d'exportation
    date_export = Paragraph(f"Date d'exportation: {timezone.now().strftime('%d/%m/%Y à %H:%M')}", styles['Normal'])
    elements.append(date_export)
    elements.append(Spacer(1, 20))

    # Prepare data for table
    data = [
        ['Utilisateur', 'Montant', 'Frais', 'Net', 'Méthode', 'Destination', 'Statut', 'Date Création', 'Date Traitement']
    ]

    for retrait in queryset:
        data.append([
            str(retrait.utilisateur.email),
            f"{retrait.montant:.2f} FC",
            f"{retrait.frais:.2f} FC",
            f"{retrait.montant_net:.2f} FC",
            retrait.methode,
            retrait.destination,
            retrait.get_statut_display(),
            retrait.cree_le.strftime('%d/%m/%Y %H:%M'),
            retrait.traite_le.strftime('%d/%m/%Y %H:%M') if retrait.traite_le else 'N/A'
        ])

    # Create table with adjusted column widths
    col_widths = [1.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1.2*inch, 1*inch, 1.2*inch, 1.2*inch]
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (3, -1), 'RIGHT'),  # Align montant, frais, net to right
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#D9E1F2')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#5B9BD5')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#EDEDED')])
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # Totaux détaillés
    total_montant = sum(retrait.montant for retrait in queryset)
    total_frais = sum(retrait.frais for retrait in queryset)
    total_net = sum(retrait.montant_net for retrait in queryset)

    # Statistiques par statut avec counts
    statuts = ['demande', 'en_traitement', 'paye', 'rejete']
    stats_data = []

    for statut in statuts:
        montant = sum(r.montant for r in queryset if r.statut == statut)
        count = queryset.filter(statut=statut).count()
        frais = sum(r.frais for r in queryset if r.statut == statut)
        net = sum(r.montant_net for r in queryset if r.statut == statut)
        stats_data.append({
            'statut': statut,
            'montant': montant,
            'count': count,
            'frais': frais,
            'net': net
        })

    # Tableau des totaux généraux
    totals_data = [
        ['TOTAUX GÉNÉRAUX', 'MONTANT', 'FRAIS', 'NET', 'NOMBRE'],
        ['Total Général:', f'{total_montant:.2f} FC', f'{total_frais:.2f} FC', f'{total_net:.2f} FC', f'{queryset.count()}']
    ]

    totals_table = Table(totals_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 0.8*inch])
    totals_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#70AD47')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#FFC000')),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#5B9BD5')),
    ]))

    elements.append(totals_table)
    elements.append(Spacer(1, 12))

    # Tableau des statistiques par statut
    stats_table_data = [
        ['STATUT', 'MONTANT', 'FRAIS', 'NET', 'NOMBRE']
    ]

    colors_by_statut = {
        'demande': '#FF5050',
        'en_traitement': '#FFC000',
        'paye': '#70AD47',
        'rejete': '#A5A5A5'
    }

    for i, stat_data in enumerate(stats_data, 1):
        stats_table_data.append([
            stat_data['statut'].capitalize(),
            f"{stat_data['montant']:.2f} FC",
            f"{stat_data['frais']:.2f} FC",
            f"{stat_data['net']:.2f} FC",
            f"{stat_data['count']}"
        ])

    stats_table = Table(stats_table_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 0.8*inch])
    stats_table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#5B9BD5')),
    ])

    # Add background colors for each status row
    for i in range(1, len(stats_table_data)):
        statut = stats_table_data[i][0].lower()
        bg_color = colors.HexColor(colors_by_statut.get(statut, '#FFFFFF'))
        stats_table_style.add('BACKGROUND', (0, i), (-1, i), bg_color)

    stats_table.setStyle(stats_table_style)
    elements.append(stats_table)

    # Build PDF
    doc.build(elements)

    # Get PDF value from buffer and return response
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response

export_retraits_pdf.short_description = "Exporter les retraits sélectionnés en PDF"


@admin.register(Depot)
class DepotAdmin(admin.ModelAdmin):
    """Configuration de l'administration pour le modèle Dépôt avec totaux."""
    list_display = ("utilisateur", "montant", "methode", "statut", "reference", "cree_le", "confirme_le")
    search_fields = ("utilisateur__email", "reference", "methode")
    list_filter = ("statut", "methode", "cree_le")
    ordering = ("-cree_le",)
    readonly_fields = ("reference", "statut", "cree_le", "confirme_le")
    actions = [export_depots_pdf, "marquer_comme_confirme"]  # Export PDF uniquement
    change_list_template = "paiements/admin/depots_change_list.html"

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            # Calcul des totaux
            qs = response.context_data['cl'].queryset
            total_depots = qs.aggregate(total=Sum('montant'))['total'] or 0
            total_en_attente = qs.filter(statut='en_attente').aggregate(total=Sum('montant'))['total'] or 0
            total_confirme = qs.filter(statut='confirme').aggregate(total=Sum('montant'))['total'] or 0

            # Ajout des totaux au contexte
            response.context_data['total_depots'] = total_depots
            response.context_data['total_en_attente'] = total_en_attente
            response.context_data['total_confirme'] = total_confirme

            # Statistiques par méthode de paiement
            methodes_stats = qs.values('methode').annotate(
                total=Sum('montant'),
                count=Count('id')
            ).order_by('-total')
            response.context_data['methodes_stats'] = methodes_stats

        except (AttributeError, KeyError):
            pass

        return response

    def get_readonly_fields(self, request, obj=None):
        """Empêcher la modification du statut après création."""
        if obj:  # si l'objet existe déjà
            return self.readonly_fields + ("montant", "utilisateur", "methode")
        return self.readonly_fields

    def get_queryset(self, request):
        # Ajouter une annotation pour les totaux par utilisateur
        return super().get_queryset(request).select_related('utilisateur')

    def marquer_comme_confirme(self, request, queryset):
        """Marquer les dépôts sélectionnés comme confirmés."""
        updated = queryset.filter(statut='en_attente').update(
            statut='confirme',
            confirme_le=timezone.now()
        )
        self.message_user(request, f"{updated} dépôt(s) marqué(s) comme confirmé(s).")
    marquer_comme_confirme.short_description = "Marquer comme confirmé"


@admin.register(Retrait)
class RetraitAdmin(admin.ModelAdmin):
    """Configuration de l'administration pour le modèle Retrait avec totaux."""
    list_display = ("utilisateur", "montant", "frais", "montant_net", "methode", "destination", "statut", "cree_le", "traite_le", "actions_personnalisees")
    search_fields = ("utilisateur__email", "destination", "methode")
    list_filter = ("statut", "methode", "cree_le")
    ordering = ("-cree_le",)
    readonly_fields = ("cree_le", "frais", "montant_net")
    actions = [export_retraits_pdf, "marquer_comme_paye", "marquer_comme_rejete", "marquer_comme_en_traitement"]  # Export PDF uniquement
    change_list_template = "paiements/admin/retraits_change_list.html"

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            # Calcul des totaux
            qs = response.context_data['cl'].queryset
            total_retraits = qs.aggregate(total=Sum('montant'))['total'] or 0
            total_frais = qs.aggregate(total=Sum('frais'))['total'] or 0
            total_net = qs.aggregate(total=Sum('montant_net'))['total'] or 0

            # Par statut
            total_demande = qs.filter(statut='demande').aggregate(total=Sum('montant'))['total'] or 0
            total_en_traitement = qs.filter(statut='en_traitement').aggregate(total=Sum('montant'))['total'] or 0
            total_paye = qs.filter(statut='paye').aggregate(total=Sum('montant'))['total'] or 0
            total_rejete = qs.filter(statut='rejete').aggregate(total=Sum('montant'))['total'] or 0

            # Ajout des totaux au contexte
            response.context_data['total_retraits'] = total_retraits
            response.context_data['total_frais'] = total_frais
            response.context_data['total_net'] = total_net
            response.context_data['total_demande'] = total_demande
            response.context_data['total_en_traitement'] = total_en_traitement
            response.context_data['total_paye'] = total_paye
            response.context_data['total_rejete'] = total_rejete

            # Statistiques par méthode de retrait
            methodes_stats = qs.values('methode').annotate(
                total=Sum('montant'),
                total_frais=Sum('frais'),
                count=Count('id')
            ).order_by('-total')
            response.context_data['methodes_stats'] = methodes_stats

        except (AttributeError, KeyError):
            pass

        return response

    def save_model(self, request, obj, form, change):
        """Met à jour automatiquement la date de traitement quand le statut change."""
        if change and obj.statut in ["paye", "rejete"] and obj.traite_le is None:
            obj.traite_le = timezone.now()
        super().save_model(request, obj, form, change)

    def actions_personnalisees(self, obj):
        """Affiche des boutons d'action rapide dans la liste."""
        if obj.statut == 'demande':
            return format_html(
                '<a class="button" href="{}" style="background-color: #ffc107">Traiter</a>&nbsp;'
                '<a class="button" href="{}" style="background-color: #dc3545">Rejeter</a>',
                f"{obj.id}/marquer-comme-en-traitement/",
                f"{obj.id}/marquer-comme-rejete/"
            )
        elif obj.statut == 'en_traitement':
            return format_html(
                '<a class="button" href="{}" style="background-color: #28a745">Payer</a>&nbsp;'
                '<a class="button" href="{}" style="background-color: #dc3545">Rejeter</a>',
                f"{obj.id}/marquer-comme-paye/",
                f"{obj.id}/marquer-comme-rejete/"
            )
        return "-"
    actions_personnalisees.short_description = "Actions"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/marquer-comme-paye/',
                 self.admin_site.admin_view(self.marquer_comme_paye_view),
                 name='retrait_marquer_comme_paye'),
            path('<path:object_id>/marquer-comme-rejete/',
                 self.admin_site.admin_view(self.marquer_comme_rejete_view),
                 name='retrait_marquer_comme_rejete'),
            path('<path:object_id>/marquer-comme-en-traitement/',
                 self.admin_site.admin_view(self.marquer_comme_en_traitement_view),
                 name='retrait_marquer_comme_en_traitement'),
        ]
        return custom_urls + urls

    def marquer_comme_paye_view(self, request, object_id):
        """Vue pour marquer un retrait comme payé."""
        retrait = Retrait.objects.get(id=object_id)
        retrait.statut = 'paye'
        retrait.traite_le = timezone.now()
        retrait.save()

        self.message_user(request, f"Le retrait #{retrait.id} a été marqué comme payé.")
        return redirect("..")

    def marquer_comme_rejete_view(self, request, object_id):
        """Vue pour marquer un retrait comme rejeté."""
        retrait = Retrait.objects.get(id=object_id)
        retrait.statut = 'rejete'
        retrait.traite_le = timezone.now()
        retrait.save()

        self.message_user(request, f"Le retrait #{retrait.id} a été marqué comme rejeté.")
        return redirect("..")

    def marquer_comme_en_traitement_view(self, request, object_id):
        """Vue pour marquer un retrait comme en traitement."""
        retrait = Retrait.objects.get(id=object_id)
        retrait.statut = 'en_traitement'
        retrait.save()

        self.message_user(request, f"Le retrait #{retrait.id} a été marqué comme en traitement.")
        return redirect("..")

    def marquer_comme_paye(self, request, queryset):
        """Marquer les retraits sélectionnés comme payés."""
        updated = queryset.filter(statut='en_traitement').update(
            statut='paye',
            traite_le=timezone.now()
        )
        self.message_user(request, f"{updated} retrait(s) marqué(s) comme payé(s).")
    marquer_comme_paye.short_description = "Marquer comme payé"

    def marquer_comme_rejete(self, request, queryset):
        """Marquer les retraits sélectionnés comme rejetés."""
        updated = queryset.filter(statut__in=['demande', 'en_traitement']).update(
            statut='rejete',
            traite_le=timezone.now()
        )
        self.message_user(request, f"{updated} retrait(s) marqué(s) comme rejeté(s).")
    marquer_comme_rejete.short_description = "Marquer comme rejeté"

    def marquer_comme_en_traitement(self, request, queryset):
        """Marquer les retraits sélectionnés comme en traitement."""
        updated = queryset.filter(statut='demande').update(
            statut='en_traitement'
        )
        self.message_user(request, f"{updated} retrait(s) marqué(s) comme en traitement.")
    marquer_comme_en_traitement.short_description = "Marquer comme en traitement"


@admin.register(FraisRetrait)
class FraisRetraitAdmin(admin.ModelAdmin):
    """Configuration de l'administration pour le modèle FraisRetrait."""
    list_display = ['nom', 'type_frais', 'montant_min', 'montant_max', 'frais_fixe',
                   'frais_pourcentage', 'frais_minimum', 'frais_maximum', 'actif', 'ordre', 'calculer_exemple']
    list_editable = ['actif', 'ordre']
    list_filter = ['type_frais', 'actif']
    ordering = ['ordre', 'montant_min']
    search_fields = ['nom']

    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'type_frais', 'actif', 'ordre')
        }),
        ('Tranche de montant', {
            'fields': ('montant_min', 'montant_max')
        }),
        ('Calcul des frais', {
            'fields': ('frais_fixe', 'frais_pourcentage')
        }),
        ('Limites des frais', {
            'fields': ('frais_minimum', 'frais_maximum')
        }),
    )

    def calculer_exemple(self, obj):
        """Affiche un exemple de calcul pour cette tranche."""
        if obj.montant_min:
            montant_exemple = obj.montant_min * Decimal('2')
            if obj.montant_max and montant_exemple > obj.montant_max:
                montant_exemple = obj.montant_max

            try:
                frais = obj.calculer_frais(montant_exemple)
                return f"{frais} FC sur {montant_exemple} FC"
            except:
                return "Erreur de calcul"
        return "-"
    calculer_exemple.short_description = "Exemple de calcul"