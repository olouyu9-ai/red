"""from django.contrib import admin
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
from django.db.models import Max, Min


from .models import BonusParrainage


@admin.register(BonusParrainage)
class BonusParrainageAdmin(admin.ModelAdmin):
   
    
    list_display = ("parrain", "filleul", "montant", "cree_le", "depot")
    search_fields = ("parrain__email", "filleul__email", "depot__reference")
    list_filter = ("cree_le",)
    ordering = ("-cree_le",)
    readonly_fields = ("cree_le",)
    actions = ["exporter_pdf_bonus", "exporter_bonus_parrain"]
    change_list_template = "bonusparrainage_change_list.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("parrain", "filleul", "depot")

    def changelist_view(self, request, extra_context=None):
      
        response = super().changelist_view(request, extra_context=extra_context)
        
        if hasattr(response, 'context_data') and response.context_data is not None:
            try:
                qs = response.context_data["cl"].queryset
                totals = qs.aggregate(
                    total_bonus=Count("id"),
                    total_montant=Sum("montant"),
                    bonus_par_parrain=Count("id", distinct="parrain"),
                    bonus_par_filleul=Count("id", distinct="filleul"),
                    montant_moyen=Sum("montant") / Count("id"),
                    montant_max=Max("montant"),
                    montant_min=Min("montant"),
                )
                response.context_data["totaux"] = totals
            except (AttributeError, KeyError):
                totals = {}
                response.context_data["totaux"] = totals
            
        return response

    def exporter_bonus_parrain(self, request, queryset):
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=30)
        elements = []
        styles = getSampleStyleSheet()
        
        # Titre
        title = Paragraph("Rapport des Bonus par Parrain", styles['Title'])
        elements.append(title)
        
        # Date de génération
        date_str = f"Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        date_para = Paragraph(date_str, styles['Normal'])
        elements.append(date_para)
        
        elements.append(Paragraph("<br/>", styles['Normal']))
        
        # Grouper les bonus par parrain
        from django.db.models import Sum, Count
        bonus_par_parrain = queryset.values('parrain__email').annotate(
            total_montant=Sum('montant'),
            nombre_filleuls=Count('id'),
            nombre_filleuls_uniques=Count('filleul', distinct=True)
        ).order_by('-total_montant')
        
        # Préparer les données du tableau
        data = [['Parrain', 'Montant Total', 'Nombre Filleuls', 'Filleuls Uniques']]
        
        total_general = 0
        for bonus in bonus_par_parrain:
            data.append([
                bonus['parrain__email'],
                f"{bonus['total_montant']:.2f} FC",
                str(bonus['nombre_filleuls']),
                str(bonus['nombre_filleuls_uniques'])
            ])
            total_general += bonus['total_montant']
        
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
        elements.append(Paragraph(f"Nombre total de parrains : {len(bonus_par_parrain)}", styles['Normal']))
        elements.append(Paragraph(f"Montant total des bonus : {total_general:.2f} FC", styles['Normal']))
        elements.append(Paragraph(f"Bonus moyen par parrain : {total_general/len(bonus_par_parrain):.2f} FC", styles['Normal']))
        
        # Générer le PDF
        doc.build(elements)
        buffer.seek(0)
        
        return FileResponse(buffer, as_attachment=True, filename="rapport_bonus_par_parrain.pdf")

    exporter_bonus_parrain.short_description = "Exporter les bonus par parrain"

    def exporter_pdf_bonus(self, request, queryset):
    
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=30)
        elements = []
        styles = getSampleStyleSheet()
        
        # Titre
        title = Paragraph("Rapport des Bonus de Parrainage", styles['Title'])
        elements.append(title)
        
        # Date de génération
        date_str = f"Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        date_para = Paragraph(date_str, styles['Normal'])
        elements.append(date_para)
        
        elements.append(Paragraph("<br/>", styles['Normal']))
        
        # Préparer les données du tableau
        data = [['Parrain', 'Filleul', 'Montant', 'Date', 'Dépôt']]
        
        total_montant = 0
        for obj in queryset:
            data.append([
                str(obj.parrain),
                str(obj.filleul),
                f"{obj.montant:.2f} FC",
                obj.cree_le.strftime('%d/%m/%Y %H:%M'),
                str(obj.depot.reference) if obj.depot and obj.depot.reference else "-"
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
        elements.append(Paragraph(f"Nombre total de bonus : {queryset.count()}", styles['Normal']))
        elements.append(Paragraph(f"Montant total : {total_montant:.2f} FC", styles['Normal']))
        
        # Statistiques supplémentaires
        parrains_uniques = queryset.values('parrain').distinct().count()
        filleuls_uniques = queryset.values('filleul').distinct().count()
        
        elements.append(Paragraph(f"Parrains uniques : {parrains_uniques}", styles['Normal']))
        elements.append(Paragraph(f"Filleuls uniques : {filleuls_uniques}", styles['Normal']))
        elements.append(Paragraph(f"Bonus moyen : {total_montant/queryset.count():.2f} FC", styles['Normal']))
        
        # Générer le PDF
        doc.build(elements)
        buffer.seek(0)
        
        return FileResponse(buffer, as_attachment=True, filename="rapport_bonus_parrainage.pdf")

    exporter_pdf_bonus.short_description = "Exporter les bonus en PDF"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('statistiques/', self.admin_site.admin_view(self.statistiques_view),
                 name='bonusparrainage_statistiques'),
        ]
        return custom_urls + urls

    def statistiques_view(self, request):
        
        # Récupérer tous les bonus
        bonus = BonusParrainage.objects.all()
        
        # Calculer les statistiques
        stats = bonus.aggregate(
            total_bonus=Count("id"),
            total_montant=Sum("montant"),
            bonus_par_parrain=Count("id", distinct="parrain"),
            bonus_par_filleul=Count("id", distinct="filleul"),
            montant_moyen=Sum("montant") / Count("id"),
            montant_max=Max("montant"),
            montant_min=Min("montant"),
        )
        
        # Par parrain
        par_parrain = bonus.values('parrain__email').annotate(
            total=Sum('montant'),
            count=Count('id'),
            filleuls_uniques=Count('filleul', distinct=True)
        ).order_by('-total')
        
        # Par mois
        from django.db.models.functions import TruncMonth
        par_mois = bonus.annotate(mois=TruncMonth('cree_le')).values('mois').annotate(
            total=Sum('montant'),
            count=Count('id')
        ).order_by('mois')
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Statistiques des bonus de parrainage',
            'stats': stats,
            'par_parrain': par_parrain,
            'par_mois': par_mois,
            'opts': self.model._meta,
        }
        
        return TemplateResponse(request, 'bonusparrainage_statistiques.html', context)"""





from django.contrib import admin
from .models import BonusParrainage


@admin.register(BonusParrainage)
class BonusParrainageAdmin(admin.ModelAdmin):
    list_display = (
        "parrain",
        "filleul",
        "achat",
        "montant",
        "pourcentage",
        "est_premier_achat",
        "cree_le",
    )
    list_filter = ("est_premier_achat", "cree_le")
    search_fields = ("parrain__email", "filleul__email", "achat__id")
    ordering = ("-cree_le",)
    readonly_fields = ("cree_le",)

    fieldsets = (
        ("Informations Parrainage", {
            "fields": ("parrain", "filleul", "achat"),
        }),
        ("Bonus", {
            "fields": ("montant", "pourcentage", "est_premier_achat"),
        }),
        ("Suivi", {
            "fields": ("cree_le",),
        }),
    )
