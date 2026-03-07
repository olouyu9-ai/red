"""
Utilitaires pour la gestion des retraits crédit et remboursements.
"""

from decimal import Decimal
from django.utils import timezone
from django.db.models import Count, Q, F
from datetime import timedelta

from .models import RetraitCredit, AjustementRemboursement, EligibiliteRetrait, Pret
from applications.parrainages.models import BonusParrainage
from applications.produits.models import Produit, GainQuotidien, Achat


class VerificateurEligibilite:
    """
    Vérifie l'éligibilité d'un utilisateur pour effectuer un retrait crédit.
    """
    
    # Configuration des montants et leurs exigences de filleuls
    MONTANTS_ELIGIBILITE = {
        Decimal('50'): 5,
        Decimal('100'): 10,
        Decimal('150'): 15,
        Decimal('200'): 20,
    }
    
    # Montants de produits éligi bles
    MONTANTS_PRODUITS_ELIGIBLES = [Decimal('20'), Decimal('100')]
    
    @classmethod
    def verifier_utilisateur(cls, utilisateur):
        """
        Vérifie si l'utilisateur peut faire un retrait crédit.
        Retourne (is_eligible, nombre_filleuls_valides, nombre_requis).
        """
        nombre_filleuls_valides = cls.compter_filleuls_valides(utilisateur)
        nombre_filleuls_requis = 5  # Par défaut
        
        return (
            nombre_filleuls_valides >= nombre_filleuls_requis,
            nombre_filleuls_valides,
            nombre_filleuls_requis
        )
    
    @classmethod
    def compter_filleuls_valides(cls, utilisateur):
        """
        Compte le nombre de filleuls uniques qui ont acheté les produits élégibles.
        """
        produits_eligibles = Produit.objects.filter(
            prix__in=cls.MONTANTS_PRODUITS_ELIGIBLES
        )
        
        filleuls_valides = BonusParrainage.objects.filter(
            parrain=utilisateur,
            achat__produit__in=produits_eligibles,
            achat__statut='actif'
        ).values('filleul').distinct().count()
        
        return filleuls_valides
    
    @classmethod
    def obtenir_montant_max_autorise(cls, utilisateur):
        """
        Détermine le montant maximum qu'un utilisateur peut emprunter.
        Basé sur le nombre de filleuls valides.
        """
        nombre_filleuls = cls.compter_filleuls_valides(utilisateur)
        
        montant_max = Decimal('50')
        for montant, requis in sorted(cls.MONTANTS_ELIGIBILITE.items()):
            if nombre_filleuls >= requis:
                if montant <= Decimal('0.00'):
                    montant_max = montant_max
                elif montant >= montant_max:
                    montant_max = montant          
        
        return montant_max
    
    @classmethod
    def obtenir_nombre_filleuls_requis(cls, montant_demande):
        """
        Détermine le nombre de filleuls requis pour un montant donné.
        """
        montant_demande = Decimal(str(montant_demande))
        
        for montant, requis in sorted(cls.MONTANTS_ELIGIBILITE.items(), reverse=True):
            if montant_demande <= montant:
                return requis
        
        return 20  # Défaut pour amounts > 5000


class GestionnaireRemboursement:
    """
    Gère le remboursement automatique des retraits crédit.
    """
    
    @staticmethod
    def creer_ajustement_depuis_gain(gain_quotidien, retrait_credit=None):
        """
        Crée un ajustement de remboursement quand un gain quotidien est généré.
        """
        if retrait_credit is None:
            # Chercher les retraits en cours de remboursement pour cet utilisateur
            retraits_actifs = RetraitCredit.objects.filter(
                utilisateur=gain_quotidien.achat.utilisateur,
                statut='en_remboursement'
            )
        else:
            retraits_actifs = [retrait_credit]
        
        ajustements_crees = []
        
        for retrait in retraits_actifs:
            # Calculer le montant à rembourser
            montant_rembourse = (
                gain_quotidien.montant * retrait.pourcentage_remboursement / Decimal('100')
            )
            
            # Créer l'ajustement
            ajustement = AjustementRemboursement.objects.create(
                retrait_credit=retrait,
                gain_quotidien=gain_quotidien,
                montant_gain=gain_quotidien.montant,
                montant_rembourse=montant_rembourse,
                pourcentage_applique=retrait.pourcentage_remboursement
            )
            
            ajustement.appliquer()
            ajustements_crees.append(ajustement)
        
        return ajustements_crees
    
    @staticmethod
    def appliquer_remboursements_en_attente(retrait_credit):
        """
        Applique tous les remboursements en attente d'un retrait.
        """
        ajustements = AjustementRemboursement.objects.filter(
            retrait_credit=retrait_credit,
            statut='en_attente'
        )
        
        for ajustement in ajustements:
            ajustement.appliquer()
        
        return ajustements.count()
    
    @staticmethod
    def calculer_progression(retrait_credit):
        """
        Calcule la progression du remboursement en pourcentage.
        """
        if retrait_credit.montant_approuve == Decimal('0.00'):
            return 0
        
        pourcentage = (
            (retrait_credit.montant_rembourse / retrait_credit.montant_approuve) * 100
        )
        
        return min(Decimal('100'), pourcentage)
    
    @staticmethod
    def obtenir_infos_remboursement(retrait_credit):
        """
        Retourne les infos complètes du remboursement.
        """
        return {
            'montant_initial': retrait_credit.montant_demande,
            'montant_approuve': retrait_credit.montant_approuve,
            'montant_rembourse': retrait_credit.montant_rembourse,
            'montant_restant': retrait_credit.montant_restant,
            'pourcentage_rembourse': GestionnaireRemboursement.calculer_progression(retrait_credit),
            'pourcentage_prelevement': retrait_credit.pourcentage_remboursement,
            'statut': retrait_credit.get_statut_display(),
            'date_debut': retrait_credit.debute_le,
            'date_fin_estimee': retrait_credit.pret.date_echeance if retrait_credit.pret else None,
        }


class GestionnairePret:
    """
    Gère la création et validation des demandes de prêt.
    """
    
    @staticmethod
    def demander_retrait_credit(utilisateur, montant, duree_mois=12, taux_annuel=0):
        """
        Crée une demande de retrait crédit.
        """
        # Vérifier l'éligibilité
        is_eligible, nb_filleuls, nb_requis = VerificateurEligibilite.verifier_utilisateur(utilisateur)
        
        if not is_eligible:
            return None, f"Non éligible: {nb_filleuls} filleuls, {nb_requis} requis"
        
        # Vérifier le montant maximum
        montant_max = VerificateurEligibilite.obtenir_montant_max_autorise(utilisateur)
        if Decimal(str(montant)) > montant_max:
            return None, f"Montant maximum autorisé: {montant_max}$, demandé: {montant}$"
        
        # Créer le prêt
        pret = Pret.objects.create(
            utilisateur=utilisateur,
            montant=Decimal(str(montant)),
            taux_annuel=Decimal(str(taux_annuel)),
            duree_mois=duree_mois,
            statut='en_attente'
        )
        
        # Créer la demande de retrait crédit
        retrait = RetraitCredit.objects.create(
            utilisateur=utilisateur,
            pret=pret,
            montant_demande=Decimal(str(montant)),
            nombre_filleuls_valides=nb_filleuls,
            nombre_filleuls_requis=nb_requis,
            est_eligible=True
        )
        
        return retrait, "Demande créée avec succès"
    
    @staticmethod
    def approuver_retrait(retrait_credit):
        """
        Approuve un retrait crédit.
        """
        success = retrait_credit.approuver()
        
        if success:
            return True, "Retrait approuvé et activé"
        else:
            return False, f"Erreur: {retrait_credit.raison_rejet}"
    
    @staticmethod
    def rejeter_retrait(retrait_credit, raison):
        """
        Rejette un retrait crédit.
        """
        retrait_credit.rejeter(raison)
        return True, "Retrait rejeté"

