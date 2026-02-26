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

from .models import Order, PaymentMessage


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Administration des commandes."""
    
    list_display = ("reference_code", "customer_name", "user", "amount", "is_paid", "created_at")
    search_fields = ("reference_code", "customer_name", "user__email")
    list_filter = ("is_paid", "created_at")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    actions = ["exporter_pdf_commandes", "marquer_comme_paye", "marquer_comme_non_paye"]
    change_list_template = "order_change_list.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user")

    def changelist_view(self, request, extra_context=None):
        """Injecter les totaux dans le contexte admin."""
        response = super().changelist_view(request, extra_context=extra_context)
        
        if hasattr(response, 'context_data') and response.context_data is not None:
            try:
                qs = response.context_data["cl"].queryset
                totals = qs.aggregate(
                    total_commandes=Count("id"),
                    total_montant=Sum("amount"),
                    total_paye=Sum("amount", filter=Q(is_paid=True)),
                    total_non_paye=Sum("amount", filter=Q(is_paid=False)),
                    commandes_payees=Count("id", filter=Q(is_paid=True)),
                    commandes_en_attente=Count("id", filter=Q(is_paid=False)),
                )
                response.context_data["totaux"] = totals
            except (AttributeError, KeyError):
                totals = {}
                response.context_data["totaux"] = totals
            
        return response

    def marquer_comme_paye(self, request, queryset):
        """Marquer les commandes sélectionnées comme payées."""
        updated = queryset.update(is_paid=True)
        self.message_user(request, f"{updated} commande(s) marquée(s) comme payée(s).")
    marquer_comme_paye.short_description = "Marquer comme payé"

    def marquer_comme_non_paye(self, request, queryset):
        """Marquer les commandes sélectionnées comme non payées."""
        updated = queryset.update(is_paid=False)
        self.message_user(request, f"{updated} commande(s) marquée(s) comme non payée(s).")
    marquer_comme_non_paye.short_description = "Marquer comme non payé"

    def exporter_pdf_commandes(self, request, queryset):
        """Exporter un rapport des commandes en PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=30)
        elements = []
        styles = getSampleStyleSheet()
        
        # Titre
        title = Paragraph("Rapport des Commandes", styles['Title'])
        elements.append(title)
        
        # Date de génération
        date_str = f"Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        date_para = Paragraph(date_str, styles['Normal'])
        elements.append(date_para)
        
        elements.append(Paragraph("<br/>", styles['Normal']))
        
        # Préparer les données du tableau
        data = [['Référence', 'Client', 'Utilisateur', 'Montant', 'Statut', 'Date']]
        
        total_montant = 0
        for obj in queryset:
            data.append([
                obj.reference_code or "-",
                obj.customer_name or "-",
                str(obj.user) if obj.user else "-",
                f"{obj.amount:.2f} CDF",
                "PAYÉ" if obj.is_paid else "EN ATTENTE",
                obj.created_at.strftime('%d/%m/%Y %H:%M')
            ])
            total_montant += obj.amount
        
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
        elements.append(Paragraph(f"Nombre total de commandes : {queryset.count()}", styles['Normal']))
        elements.append(Paragraph(f"Montant total : {total_montant:.2f} CDF", styles['Normal']))
        
        payees = queryset.filter(is_paid=True).count()
        elements.append(Paragraph(f"Commandes payées : {payees}", styles['Normal']))
        elements.append(Paragraph(f"Commandes en attente : {queryset.count() - payees}", styles['Normal']))
        
        # Générer le PDF
        doc.build(elements)
        buffer.seek(0)
        
        return FileResponse(buffer, as_attachment=True, filename="rapport_commandes.pdf")

    exporter_pdf_commandes.short_description = "Exporter les commandes en PDF"


@admin.register(PaymentMessage)
class PaymentMessageAdmin(admin.ModelAdmin):
    """Administration des messages de paiement."""
    
    list_display = ("reference", "sender", "amount", "processed", "received_at")
    search_fields = ("reference", "sender", "sms_text")
    list_filter = ("processed", "received_at")
    ordering = ("-received_at",)
    readonly_fields = ("received_at", "sms_text", "sender", "amount", "reference")
    actions = ["exporter_pdf_messages", "marquer_comme_traite", "marquer_comme_non_traite"]
    change_list_template = "paymentmessage_change_list.html"

    def changelist_view(self, request, extra_context=None):
        """Injecter les totaux dans le contexte admin."""
        response = super().changelist_view(request, extra_context=extra_context)
        
        if hasattr(response, 'context_data') and response.context_data is not None:
            try:
                qs = response.context_data["cl"].queryset
                totals = qs.aggregate(
                    total_messages=Count("id"),
                    total_montant=Sum("amount"),
                    total_traites=Count("id", filter=Q(processed=True)),
                    total_non_traites=Count("id", filter=Q(processed=False)),
                    montant_traite=Sum("amount", filter=Q(processed=True)),
                    montant_non_traite=Sum("amount", filter=Q(processed=False)),
                )
                response.context_data["totaux"] = totals
            except (AttributeError, KeyError):
                totals = {}
                response.context_data["totaux"] = totals
            
        return response

    def marquer_comme_traite(self, request, queryset):
        """Marquer les messages sélectionnés comme traités."""
        updated = queryset.update(processed=True)
        self.message_user(request, f"{updated} message(s) marqué(s) comme traité(s).")
    marquer_comme_traite.short_description = "Marquer comme traité"

    def marquer_comme_non_traite(self, request, queryset):
        """Marquer les messages sélectionnés comme non traités."""
        updated = queryset.update(processed=False)
        self.message_user(request, f"{updated} message(s) marqué(s) comme non traité(s).")
    marquer_comme_non_traite.short_description = "Marquer comme non traité"

    def exporter_pdf_messages(self, request, queryset):
        """Exporter un rapport des messages en PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=30)
        elements = []
        styles = getSampleStyleSheet()
        
        # Titre
        title = Paragraph("Rapport des Messages de Paiement", styles['Title'])
        elements.append(title)
        
        # Date de génération
        date_str = f"Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        date_para = Paragraph(date_str, styles['Normal'])
        elements.append(date_para)
        
        elements.append(Paragraph("<br/>", styles['Normal']))
        
        # Préparer les données du tableau
        data = [['Référence', 'Expéditeur', 'Montant', 'Traité', 'Date', 'Erreur']]
        
        total_montant = 0
        for obj in queryset:
            data.append([
                obj.reference or "-",
                obj.sender or "-",
                f"{obj.amount:.2f} CDF" if obj.amount else "-",
                "OUI" if obj.processed else "NON",
                obj.received_at.strftime('%d/%m/%Y %H:%M'),
                obj.error[:50] + "..." if obj.error and len(obj.error) > 50 else obj.error or "-"
            ])
            if obj.amount:
                total_montant += obj.amount
        
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
        elements.append(Paragraph(f"Nombre total de messages : {queryset.count()}", styles['Normal']))
        elements.append(Paragraph(f"Montant total : {total_montant:.2f} CDF", styles['Normal']))
        
        traites = queryset.filter(processed=True).count()
        elements.append(Paragraph(f"Messages traités : {traites}", styles['Normal']))
        elements.append(Paragraph(f"Messages non traités : {queryset.count() - traites}", styles['Normal']))
        
        # Générer le PDF
        doc.build(elements)
        buffer.seek(0)
        
        return FileResponse(buffer, as_attachment=True, filename="rapport_messages_paiement.pdf")

    exporter_pdf_messages.short_description = "Exporter les messages en PDF"