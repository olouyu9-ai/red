"""
Tests pour le système de retrait crédit avec protection d'éligibilité.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta

from applications.prets.models import Pret, RetraitCredit, AjustementRemboursement, EligibiliteRetrait
from applications.prets.utils import (
    VerificateurEligibilite,
    GestionnairePret,
    GestionnaireRemboursement,
)
from applications.produits.models import Produit, Achat, GainQuotidien
from applications.parrainages.models import BonusParrainage

User = get_user_model()


class VerificateurEligibiliteTestCase(TestCase):
    """Tests pour la vérification d'éligibilité."""
    
    def setUp(self):
        """Créer les utilisateurs et produits nécessaires."""
        self.parrain = User.objects.create_user(
            email='parrain@test.com',
            password='test123'
        )
        
        self.filleuls = [
            User.objects.create_user(email=f'filleul{i}@test.com', password='test123')
            for i in range(6)
        ]
        
        # Créer les produits élégibles
        self.produit_20 = Produit.objects.create(
            nom='Produit 20$',
            description='Test',
            prix=Decimal('20'),
            duree_jours=30
        )
        
        self.produit_100 = Produit.objects.create(
            nom='Produit 100$',
            description='Test',
            prix=Decimal('100'),
            duree_jours=30
        )
    
    def test_utilisateur_non_eligible_sans_filleuls(self):
        """Test qu'un utilisateur sans filleuls n'est pas éligible."""
        is_eligible, nb_filleuls, nb_requis = VerificateurEligibilite.verifier_utilisateur(self.parrain)
        
        self.assertFalse(is_eligible)
        self.assertEqual(nb_filleuls, 0)
        self.assertEqual(nb_requis, 5)
    
    def test_utilisateur_non_eligible_avec_3_filleuls(self):
        """Test qu'un utilisateur avec 3 filleuls n'est pas éligible."""
        for i in range(3):
            achat = Achat.objects.create(
                utilisateur=self.filleuls[i],
                produit=self.produit_20,
                prix_au_moment_achat=Decimal('20'),
                date_fin=date.today() + timedelta(days=30),
                statut='actif'
            )
            
            BonusParrainage.objects.create(
                parrain=self.parrain,
                filleul=self.filleuls[i],
                achat=achat,
                montant=Decimal('2')
            )
        
        is_eligible, nb_filleuls, nb_requis = VerificateurEligibilite.verifier_utilisateur(self.parrain)
        
        self.assertFalse(is_eligible)
        self.assertEqual(nb_filleuls, 3)
    
    def test_utilisateur_eligible_avec_5_filleuls(self):
        """Test qu'un utilisateur avec 5 filleuls est éligible."""
        for i in range(5):
            achat = Achat.objects.create(
                utilisateur=self.filleuls[i],
                produit=self.produit_20,
                prix_au_moment_achat=Decimal('20'),
                date_fin=date.today() + timedelta(days=30),
                statut='actif'
            )
            
            BonusParrainage.objects.create(
                parrain=self.parrain,
                filleul=self.filleuls[i],
                achat=achat,
                montant=Decimal('2')
            )
        
        is_eligible, nb_filleuls, nb_requis = VerificateurEligibilite.verifier_utilisateur(self.parrain)
        
        self.assertTrue(is_eligible)
        self.assertEqual(nb_filleuls, 5)
    
    def test_montant_max_autorise(self):
        """Test le montant maximum autorisé selon le nombre de filleuls."""
        # Avec 5 filleuls
        for i in range(5):
            achat = Achat.objects.create(
                utilisateur=self.filleuls[i],
                produit=self.produit_20,
                prix_au_moment_achat=Decimal('20'),
                date_fin=date.today() + timedelta(days=30),
                statut='actif'
            )
            BonusParrainage.objects.create(
                parrain=self.parrain,
                filleul=self.filleuls[i],
                achat=achat,
                montant=Decimal('2')
            )
        
        montant_max = VerificateurEligibilite.obtenir_montant_max_autorise(self.parrain)
        self.assertEqual(montant_max, Decimal('100'))
        
        # Avec 6 filleuls
        achat = Achat.objects.create(
            utilisateur=self.filleuls[5],
            produit=self.produit_100,
            prix_au_moment_achat=Decimal('100'),
            date_fin=date.today() + timedelta(days=30),
            statut='actif'
        )
        BonusParrainage.objects.create(
            parrain=self.parrain,
            filleul=self.filleuls[5],
            achat=achat,
            montant=Decimal('10')
        )
        
        # Vérifier à nouveau
        montant_max = VerificateurEligibilite.obtenir_montant_max_autorise(self.parrain)
        # Le montant max ne change qu'avec 10 filleuls
        self.assertEqual(montant_max, Decimal('100'))


class GestionnairePretTestCase(TestCase):
    """Tests pour la gestion des demandes de prêt."""
    
    def setUp(self):
        """Configuration initiale."""
        self.parrain = User.objects.create_user(
            email='parrain@test.com',
            password='test123'
        )
        
        self.filleuls = [
            User.objects.create_user(email=f'filleul{i}@test.com', password='test123')
            for i in range(5)
        ]
        
        self.produit_20 = Produit.objects.create(
            nom='Produit 20$',
            description='Test',
            prix=Decimal('20'),
            duree_jours=30
        )
        
        # Créer les achats et bonus
        for i in range(5):
            achat = Achat.objects.create(
                utilisateur=self.filleuls[i],
                produit=self.produit_20,
                prix_au_moment_achat=Decimal('20'),
                date_fin=date.today() + timedelta(days=30),
                statut='actif'
            )
            
            BonusParrainage.objects.create(
                parrain=self.parrain,
                filleul=self.filleuls[i],
                achat=achat,
                montant=Decimal('2')
            )
    
    def test_demander_retrait_credit_eligible(self):
        """Test la création d'une demande de retrait pour un utilisateur éligible."""
        retrait, message = GestionnairePret.demander_retrait_credit(
            utilisateur=self.parrain,
            montant=100,
            duree_mois=12,
            taux_annuel=5
        )
        
        self.assertIsNotNone(retrait)
        self.assertEqual(retrait.montant_demande, Decimal('100'))
        self.assertEqual(retrait.statut, 'demande')
        self.assertTrue(retrait.est_eligible)
    
    def test_demander_retrait_credit_non_eligible(self):
        """Test la création d'une demande pour un utilisateur non éligible."""
        utilisateur_non_eligible = User.objects.create_user(
            email='non_eligible@test.com',
            password='test123'
        )
        
        retrait, message = GestionnairePret.demander_retrait_credit(
            utilisateur=utilisateur_non_eligible,
            montant=100
        )
        
        self.assertIsNone(retrait)
        self.assertIn('Non éligible', message)
    
    def test_demander_retrait_montant_trop_eleve(self):
        """Test qu'on ne peut pas demander plus que le montant max."""
        retrait, message = GestionnairePret.demander_retrait_credit(
            utilisateur=self.parrain,
            montant=500  # Max est 100 avec 5 filleuls
        )
        
        self.assertIsNone(retrait)
        self.assertIn('maximum', message.lower())


class GestionnaireRemboursementTestCase(TestCase):
    """Tests pour la gestion des remboursements."""
    
    def setUp(self):
        """Configuration initiale."""
        self.utilisateur = User.objects.create_user(
            email='user@test.com',
            password='test123'
        )
        
        self.parrain = User.objects.create_user(
            email='parrain@test.com',
            password='test123'
        )
        
        # Créer un filleul éligible
        achat = Achat.objects.create(
            utilisateur=self.utilisateur,
            produit=Produit.objects.create(
                nom='Produit',
                description='Test',
                prix=Decimal('20'),
                duree_jours=30
            ),
            prix_au_moment_achat=Decimal('20'),
            date_fin=date.today() + timedelta(days=30),
            statut='actif'
        )
        
        BonusParrainage.objects.create(
            parrain=self.parrain,
            filleul=self.utilisateur,
            achat=achat,
            montant=Decimal('2')
        )
        
        # Pour faciliter, créer directement un retrait
        pret = Pret.objects.create(
            utilisateur=self.parrain,
            montant=Decimal('100'),
            statut='actif'
        )
        
        self.retrait = RetraitCredit.objects.create(
            utilisateur=self.parrain,
            pret=pret,
            montant_demande=Decimal('100'),
            montant_approuve=Decimal('100'),
            statut='en_remboursement',
            pourcentage_remboursement=Decimal('10')
        )
    
    def test_calculer_progression(self):
        """Test le calcul de la progression du remboursement."""
        self.retrait.montant_rembourse = Decimal('25')
        self.retrait.save()
        
        progression = GestionnaireRemboursement.calculer_progression(self.retrait)
        
        self.assertEqual(float(progression), 25.0)
    
    def test_obtenir_infos_remboursement(self):
        """Test l'obtention des infos de remboursement."""
        self.retrait.montant_rembourse = Decimal('50')
        self.retrait.montant_restant = Decimal('50')
        self.retrait.save()
        
        infos = GestionnaireRemboursement.obtenir_infos_remboursement(self.retrait)
        
        self.assertEqual(infos['montant_initial'], Decimal('100'))
        self.assertEqual(infos['montant_rembourse'], Decimal('50'))
        self.assertEqual(infos['montant_restant'], Decimal('50'))
        self.assertEqual(float(infos['pourcentage_rembourse']), 50.0)


class RetraitCreditModelTestCase(TestCase):
    """Tests pour le modèle RetraitCredit."""
    
    def setUp(self):
        """Configuration initiale."""
        self.utilisateur = User.objects.create_user(
            email='user@test.com',
            password='test123'
        )
        
        self.pret = Pret.objects.create(
            utilisateur=self.utilisateur,
            montant=Decimal('100'),
            statut='en_attente'
        )
    
    def test_creer_retrait_credit(self):
        """Test la création d'un retrait crédit."""
        retrait = RetraitCredit.objects.create(
            utilisateur=self.utilisateur,
            pret=self.pret,
            montant_demande=Decimal('100'),
            nombre_filleuls_requis=5
        )
        
        self.assertEqual(retrait.statut, 'demande')
        self.assertEqual(retrait.montant_restant, Decimal('100'))
    
    def test_approuver_retrait(self):
        """Test l'approbation d'un retrait."""
        retrait = RetraitCredit.objects.create(
            utilisateur=self.utilisateur,
            pret=self.pret,
            montant_demande=Decimal('100'),
            nombre_filleuls_valides=5,
            nombre_filleuls_requis=5,
            est_eligible=True
        )
        
        retrait.approuver()
        retrait.refresh_from_db()
        self.pret.refresh_from_db()
        
        self.assertEqual(retrait.statut, 'en_remboursement')
        self.assertEqual(self.pret.statut, 'actif')

