from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Pret, RetraitCredit
from .forms import DemandePretForm

# utilitaires et décorateurs pour les retraits crédit
from .decorators import requerir_eligibilite_retrait
from .utils import GestionnairePret, GestionnaireRemboursement, VerificateurEligibilite





# ---------------------------------------------------------------------------
# Vues liées au retrait crédit
# ---------------------------------------------------------------------------

@login_required
@requerir_eligibilite_retrait
def demander_retrait_credit(request):
    """Permet à un utilisateur éligible de créer une demande de retrait crédit."""
    if request.method == 'POST':
        montant = request.POST.get('montant')
        duree = request.POST.get('duree', 12)
        taux = request.POST.get('taux', 0)

        retrait, message = GestionnairePret.demander_retrait_credit(
            utilisateur=request.user,
            montant=montant,
            duree_mois=int(duree),
            taux_annuel=taux,
        )

        if retrait:
            messages.success(request, f"✅ {message}")
            return redirect('prets:voir_retraits')
        else:
            messages.error(request, f"❌ {message}")

    # vue GET ou échec de validation : afficher formulaire simple
    return render(request, 'prets/demander_retrait.html')


@login_required
@requerir_eligibilite_retrait
def voir_retraits(request):
    """Affiche la liste des retraits effectués par l'utilisateur."""
    retraits = RetraitCredit.objects.filter(utilisateur=request.user).order_by('-demande_le')
    return render(request, 'prets/voir_retraits.html', {'retraits': retraits})


# ---------------------------------------------------------------------------
# Vues API (JSON) pour vérifications et actions
# ---------------------------------------------------------------------------

from django.http import JsonResponse
import json

@login_required
def api_verifier_eligibilite(request):
    """Retourne un objet JSON décrivant l'éligibilité de l'utilisateur."""
    infos = VerificateurEligibilite.verifier_utilisateur(request.user)  # tuple
    is_eligible, nb, requis = infos
    montant_max = VerificateurEligibilite.obtenir_montant_max_autorise(request.user)
    
    return JsonResponse({
        'success': True,
        'data': {
            'est_eligible': is_eligible,
            'nb_filleuls_valides': nb,
            'nb_filleuls_requis': requis,
            'montant_max': str(montant_max),
            'filleuls_manquants': max(0, requis - nb),
        }
    })


@login_required
@requerir_eligibilite_retrait
def api_demander_retrait(request):
    """API qui permet à un utilisateur éligible de déposer une demande."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)

    montant = data.get('montant')
    if montant is None:
        return JsonResponse({'error': 'Montant requis'}, status=400)

    retrait, msg = GestionnairePret.demander_retrait_credit(request.user, montant)
    if retrait:
        return JsonResponse({'success': True, 'message': msg, 'retrait_id': retrait.id})
    else:
        return JsonResponse({'success': False, 'error': msg}, status=400)


@login_required
def api_infos_remboursement(request, retrait_id):
    """Retourne les informations de remboursement d'un retrait donné."""
    try:
        retrait = RetraitCredit.objects.get(id=retrait_id, utilisateur=request.user)
    except RetraitCredit.DoesNotExist:
        return JsonResponse({'error': 'Retrait non trouvé'}, status=404)

    infos = GestionnaireRemboursement.obtenir_infos_remboursement(retrait)
    
    return JsonResponse({'success': True, 'data': infos})
