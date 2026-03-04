from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from applications.portefeuille.models import TransactionPortefeuille
from .models import Utilisateur, ProfilUtilisateur
from django.contrib import messages
from .forms import UtilisateurUpdateForm



@require_http_methods(["GET", "POST"])
def vue_inscription(request):
    
    if request.method == 'POST':
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        mot_de_passe = request.POST.get('mot_de_passe')
        code_parrain = request.POST.get('code_parrain', '')

        if Utilisateur.objects.filter(email=email).exists():
            messages.error(request, "Cet identifiant est déjà occupé.")
            return redirect('inscription')

        if Utilisateur.objects.filter(telephone=telephone).exists():
            messages.error(request, "Ce numéro de téléphone est déjà enregistré.")
            return redirect('inscription')
        try:
                # Création de l'utilisateur
                utilisateur = Utilisateur.objects.create_user(
                    email=email,
                    telephone=telephone,
                    password=mot_de_passe,
                    mot_de_passe_clair=mot_de_passe,
                    username=email
                )
                
                # Création du profil utilisateur (seulement si nécessaire)
                ProfilUtilisateur.objects.get_or_create(utilisateur=utilisateur)

                # Association avec un parrain si un code est fourni
                if code_parrain:
                    try:
                        parrain_profil = ProfilUtilisateur.objects.get(code_parrainage=code_parrain)
                        utilisateur.profil.parrain = parrain_profil.utilisateur
                        utilisateur.profil.save()
                    except ProfilUtilisateur.DoesNotExist:
                        messages.error(request, "Code de parrainage non reconnu.")
                        return render(request, 'comptes/inscription.html')

                # Connexion automatique après inscription
                utilisateur = authenticate(request, username=email, password=mot_de_passe)
                if utilisateur is not None:
                    login(request, utilisateur)
                    bonus_inscription = 500
                      # Créditer 500FC le portefeuille de l'utilisateur a l'inscription
                    nouveau_solde = request.user.profil.get_solde() + bonus_inscription
                    TransactionPortefeuille.objects.create(
                            utilisateur=request.user,
                            type='bonus_inscription',
                            montant=bonus_inscription,
                            reference="bonus_inscription",
                            solde_apres=nouveau_solde
                        )
                    return redirect('liste_produits')
        except :
            messages.error(request, "Cet identifiant est déjà pris, veuillez ajouter un symbole.")
            return render(request, 'comptes/inscription.html')

    return render(request, 'comptes/inscription.html')


@login_required
def vue_ajouter_code_parrain(request):
    """Vue pour ajouter un code de parrain dans les 24h."""
    if request.method == 'POST':
        code_parrain = request.POST.get('code_parrain')
        try:
            parrain = ProfilUtilisateur.objects.get(code_parrainage=code_parrain)
            if not request.user.profil.verrouillage_parrainage_le:
                request.user.profil.parrain = parrain.utilisateur
                request.user.profil.save()
                messages.success(request, "Code de parrain ajouté avec succès !")
            else:
                messages.error(request, "L'ajout de code de parrain n'est plus possible.")
        except ProfilUtilisateur.DoesNotExist:
            messages.error(request, "Code de parrainage introuvable.")

    return render(request, 'comptes/ajouter_code_parrain.html')



@login_required
def profile_view(request):
    """Affiche les informations du profil de l'utilisateur connecté."""
    utilisateur = request.user
    profil = getattr(utilisateur, 'profil', None)
    return render(request, 'comptes/profile.html', {
        'utilisateur': utilisateur,
        'profil': profil,
    })


@login_required
def profile_edit(request):
    """Permet de modifier les informations de l'utilisateur connecté."""
    utilisateur = request.user
    if request.method == 'POST':
        form = UtilisateurUpdateForm(request.POST, instance=utilisateur)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès.')
            return redirect('profile')
        else:
            messages.error(request, 'Merci de corriger les erreurs mentionnées ci-dessous.')
    else:
        form = UtilisateurUpdateForm(instance=utilisateur)

    return render(request, 'comptes/edit_profile.html', {
        'form': form,
    })




