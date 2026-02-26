# applications/produits/management/commands/corriger_references_transactions.py
from django.core.management.base import BaseCommand
from applications.portefeuille.models import TransactionPortefeuille
from applications.produits.models import Achat

class Command(BaseCommand):
    help = 'Corrige les références des transactions de gains quotidiens'

    def handle(self, *args, **options):
        transactions = TransactionPortefeuille.objects.filter(type='gain_quotidien')

        for transaction in transactions:
            # Extraire l'ID de l'achat de la référence si possible
            if "ID: " in transaction.reference:
                continue  # La référence est déjà correcte

            # Trouver l'achat correspondant (exemple simplifié, à adapter selon votre logique)
            achats = Achat.objects.filter(utilisateur=transaction.utilisateur, produit__nom__icontains=transaction.reference.split("pour ")[-1].split(" (")[0])
            if achats.exists():
                achat = achats.first()
                transaction.reference = f"Gain quotidien pour {achat.produit.nom} (ID: {achat.id})"
                transaction.save()
                self.stdout.write(self.style.SUCCESS(f'Référence corrigée pour la transaction {transaction.id}'))

        self.stdout.write(self.style.SUCCESS('Correction des références terminée'))
