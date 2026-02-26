from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from applications.comptes.models import ProfilUtilisateur
from .models import BonusParrainage
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import BonusParrainage

@login_required
def afficher_code_parrainage(request):
    """Affiche le code de parrainage de l'utilisateur connecté."""
    # On suppose que chaque utilisateur a un profil lié contenant son code_parrainage
    code_parrainage = request.user.profil.code_parrainage
    lien_parrainage = f"{request.scheme}://{request.get_host()}/comptes/inscription/?code_parrain={code_parrainage}"

    return render(request, 'parrainages/mon_code.html', {
        'code_parrainage': code_parrainage,
        'lien_parrainage': lien_parrainage
    })


@login_required
def liste_filleuls(request):
    """Affiche la liste des filleuls et leurs bonus pour l'utilisateur connecté."""
    filleuls_bonus = (
        BonusParrainage.objects
        .filter(parrain=request.user)
        .select_related("filleul", "achat")  # optimisation
        .order_by("-cree_le")
    )

    return render(request, 'parrainages/mes_invites.html', {
        'filleuls_bonus': filleuls_bonus,
    })


@login_required
def liste_bonus_parrainage(request):
    """Affiche la liste des bonus de parrainage de l'utilisateur connecté."""
    bonus = BonusParrainage.objects.filter(parrain=request.user).order_by('-cree_le')
    total_bonus = sum(b.montant for b in bonus)

    return render(request, 'parrainages/bonus.html', {
        'bonus': bonus,
        'total_bonus': total_bonus
    })
