"""
Décorateurs et mixins pour protéger les fonctionnalités de retrait crédit.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden

from .models import RetraitCredit
from .utils import VerificateurEligibilite, GestionnairePret


def requerir_eligibilite_retrait(vue_func):
    """
    Décorateur qui vérifie l'éligibilité avant d'accéder à une vue de retrait.
    """
    @wraps(vue_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        is_eligible, nb_filleuls, nb_requis = VerificateurEligibilite.verifier_utilisateur(request.user)
        
        if not is_eligible:
            messages.error(
                request,
                f"❌ Vous n'êtes pas éligible au retrait crédit. "
                f"Filleuls valides: {nb_filleuls}/{nb_requis} (minimum 5 requis)"
            )
            return redirect('tableau_de_bord')
        
        return vue_func(request, *args, **kwargs)
    
    return wrapper


def api_requerir_eligibilite_retrait(vue_func):
    """
    Décorateur API qui vérifie l'éligibilité avant l'accès.
    """
    @wraps(vue_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Non authentifié'}, status=401)
        
        is_eligible, nb_filleuls, nb_requis = VerificateurEligibilite.verifier_utilisateur(request.user)
        
        if not is_eligible:
            return JsonResponse({
                'error': 'Non éligible',
                'message': f"Filleuls valides: {nb_filleuls}/{nb_requis} (minimum 5 requis)",
                'nb_filleuls': nb_filleuls,
                'nb_requis': nb_requis
            }, status=403)
        
        return vue_func(request, *args, **kwargs)
    
    return wrapper


class EligibiliteRetraitMixin:
    """
    Mixin pour les vues basées sur les classes.
    Protège l'accès aux vues de demande de retrait crédit.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        is_eligible, nb_filleuls, nb_requis = VerificateurEligibilite.verifier_utilisateur(request.user)
        
        if not is_eligible:
            messages.error(
                request,
                f"❌ Vous n'êtes pas éligible au retrait crédit. "
                f"Vous avez {nb_filleuls} filleul(s) valide(s), "
                f"minimum {nb_requis} requis."
            )
            return redirect('tableau_de_bord')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_eligible, nb_filleuls, nb_requis = VerificateurEligibilite.verifier_utilisateur(self.request.user)
        montant_max = VerificateurEligibilite.obtenir_montant_max_autorise(self.request.user)
        
        context.update({
            'nb_filleuls_valides': nb_filleuls,
            'nb_filleuls_requis': nb_requis,
            'montant_max_autorise': montant_max,
            'is_eligible': is_eligible,
        })
        
        return context


def verifier_eligibilite_montant(montant_demande):
    """
    Fonction pour vérifier si un montant spécifique est autorisé.
    """
    from decimal import Decimal
    
    montant = Decimal(str(montant_demande))
    
    # Vérifier contre les montants d'éligibilité définis
    montants_autorises = list(VerificateurEligibilite.MONTANTS_ELIGIBILITE.keys())
    
    return montant in montants_autorises


def obtenir_infos_eligibilite_complet(utilisateur):
    """
    Retourne les informations complètes d'éligibilité d'un utilisateur.
    """
    is_eligible, nb_filleuls, nb_requis = VerificateurEligibilite.verifier_utilisateur(utilisateur)
    montant_max = VerificateurEligibilite.obtenir_montant_max_autorise(utilisateur)
    
    return {
        'is_eligible': is_eligible,
        'nombre_filleuls_valides': nb_filleuls,
        'nombre_filleuls_requis': nb_requis,
        'montant_maximum_autorise': montant_max,
        'peut_emprunter': is_eligible,
        'filleuls_manquants': max(0, nb_requis - nb_filleuls),
        'statut': 'Éligible ✅' if is_eligible else f'Non éligible ❌ ({nb_filleuls}/{nb_requis})',
    }

