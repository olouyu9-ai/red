from django.core.management.base import BaseCommand
from applications.produits.models import Achat, GainQuotidien
from applications.portefeuille.models import TransactionPortefeuille
from django.utils import timezone
from decimal import Decimal
# python manage.py verser_gains_quotidiens

class Command(BaseCommand):
    help = 'Calcule et crédite les gains quotidiens pour tous les achats actifs'

    def handle(self, *args, **options):
        aujourdhui = timezone.now().date()
        self.stdout.write(f"Début du traitement des gains quotidiens pour le {aujourdhui}")

        # Parcourir tous les achats actifs
        achats = Achat.objects.filter(statut='actif')
        # Dictionnaire pour suivre les utilisateurs déjà incrémentés
        #utilisateurs_incremente = set()


        for achat in achats:
           if achat.jours_payes < achat.produit.duree_jours:
        #for achat in Achat.objects.filter(statut='actif', jours_payes__lt=achat.produit.duree_jours):
            # Calculer le gain quotidien
            montant = achat.prix_au_moment_achat * achat.produit.taux_quotidien

            # Créer l'enregistrement de gain quotidien
            GainQuotidien.objects.create(
                achat=achat,
                jour=aujourdhui,
                montant=montant,
                poste=True,
                poste_le=timezone.now()
            )

            # Créer la transaction dans le portefeuille
            TransactionPortefeuille.objects.create(
                utilisateur=achat.utilisateur,
                type='gain_quotidien',
                montant=montant,
                reference=f'Gain quotidien pour {achat.produit.nom} (Jour {achat.jours_payes + 1})',
                solde_apres=achat.utilisateur.profil.get_solde() + montant
            )


                            # Incrémenter le compteur global de l'utilisateur une seule fois
            """if achat.utilisateur.id not in utilisateurs_incremente:
                try:
                    control = Control_achat.objects.get(utilisateur=achat.utilisateur)
                    control.jours_payes += 1
                    # Si on atteint 29 jours, on reset et on supprime l'objet
                    if control.jours_payes >= 30:
                        control.delete()
                    else:
                        control.save()
                except Control_achat.DoesNotExist:
                    # On ignore si pas de control existant
                    pass

                utilisateurs_incremente.add(achat.utilisateur.id)"""





            # Mettre à jour l'achat
            achat.jours_payes += 1
            if achat.jours_payes == achat.produit.duree_jours:
                achat.statut = 'expire'
            achat.save()

            self.stdout.write(f"Gain de {montant} FC crédité pour {achat.utilisateur.email}")
               ######################################################
        ######################################################


        self.stdout.write(self.style.SUCCESS("Traitement des gains quotidiens terminé avec succès"))

"""from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from applications.produits.models import Achat, GainQuotidien
from applications.portefeuille.models import TransactionPortefeuille

class Command(BaseCommand):
    help = 'Génère les gains quotidiens pour les achats actifs'

    def handle(self, *args, **options):
        today = timezone.now().date()
        achats_actifs = Achat.objects.filter(
            statut='actif',
            date_fin__gte=today,
        )

        for achat in achats_actifs:
            # Vérifier si un gain quotidien a déjà été généré pour aujourd'hui
            gain_existant = GainQuotidien.objects.filter(achat=achat, jour=today).first()
            if gain_existant:
                self.stdout.write(self.style.WARNING(f'Gain quotidien déjà généré pour l\'achat {achat.id} aujourd\'hui'))
                continue

            # Calculer le gain quotidien pour cet achat spécifique
            gain_quotidien = achat.produit.prix * (achat.produit.taux_quotidien / Decimal('100'))

            # Créer un enregistrement de gain quotidien
            gain = GainQuotidien.objects.create(
                achat=achat,
                jour=today,
                montant=gain_quotidien,
            )

            # Créer une transaction de gain quotidien
            solde_actuel = achat.utilisateur.profil.get_solde()
            nouveau_solde = solde_actuel + gain_quotidien

            TransactionPortefeuille.objects.create(
                utilisateur=achat.utilisateur,
                type='gain_quotidien',
                montant=gain_quotidien,
                reference=f"Gain quotidien pour {achat.produit.nom} (ID: {achat.id})",
                solde_apres=nouveau_solde
            )

            self.stdout.write(self.style.SUCCESS(f'Gain quotidien de {gain_quotidien} FC généré pour {achat.utilisateur.email} (Achat ID: {achat.id})'))

        # Mettre à jour les achats expirés
        achats_expires = Achat.objects.filter(
            statut='actif',
            date_fin__lt=today
        )

        for achat in achats_expires:
            achat.statut = 'expire'
            achat.save()
            self.stdout.write(self.style.WARNING(f"Achat {achat.id} marqué comme expiré pour {achat.utilisateur.email}"))
"""