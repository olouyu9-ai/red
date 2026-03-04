from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from applications.portefeuille.models import TransactionPortefeuille, CapitalClient
from applications.produits.models import Achat
from applications.paiements.models import Depot
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Q
from django.db.models import DecimalField
from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import Coalesce
import uuid
from django.http import FileResponse
import os
from django.conf import settings

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import json
from applications.comptes.models import ProfilUtilisateur, Utilisateur



#######################################################################"
# ######################################################################
# ####################################################################
# #####################################################################"


@login_required(login_url='accueil')
def vue_tableau_de_bord(request):
        #capital, created = CapitalClient.objects.get_or_create(utilisateur=request.user )

        if request.user.is_authenticated:
            try:
                    """Vue pour le tableau de bord utilisateur avec données dynamiques."""
                    from django.db.utils import OperationalError

                    try:
                        capital = CapitalClient.objects.filter(utilisateur=request.user).first()
                        if capital:
                            solde_capital = capital.capital
                        else:
                            solde_capital = 0
                    except OperationalError:
                        # La table n'existe pas encore
                        solde_capital = 0
                    # Récupérer les transactions récentes
                    transactions = TransactionPortefeuille.objects.filter(utilisateur=request.user).order_by('-cree_le')
                    solde = request.user.profil.get_solde()
                    solde_et_solde_capital = float(solde + solde_capital)
                    # capital que l'utilisateur a investit
                    capital_actifs = Achat.objects.filter(
                        utilisateur=request.user,
                        statut='actif',
                        est_reinvesti=False,
                    ).aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0

                    # partie pour gerer les trader inactif et non reinvest

                    today = timezone.now().date()
                    # Filtrer les achats expirés et non réinvestis
                    achats = Achat.objects.filter(
                        utilisateur=request.user,
                        est_reinvesti=False
                    ).filter(
                        Q(statut="expire") | Q(date_fin__lt=today)
                    )
                    # Calculer la somme
                    total_trader_inactif = achats.aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0

                    # dasn le cas ou les deus ont de valeur
                    totaux_gen =  total_trader_inactif + capital_actifs
                    # Calculer le solde (exemple simplifié)
                    #solde = sum(t.montant for t in TransactionPortefeuille.objects.filter(utilisateur=request.user, type__in=['depot', 'gain_quotidien', 'bonus_parrainage'])) - sum(t.montant for t in TransactionPortefeuille.objects.filter(utilisateur=request.user, type='retrait'))

                    # Calculer les gains d'aujourd'hui
                    gains_aujourdhui = sum(t.montant for t in TransactionPortefeuille.objects.filter(utilisateur=request.user, type='gain_quotidien', cree_le__date=timezone.now().date()))

                    # Calculer le total des dépôts
                    total_depots = sum(d.montant for d in Depot.objects.filter(utilisateur=request.user, statut='confirme'))

                    # Récupérer les achats actifs
                    achats_actifs = Achat.objects.filter(utilisateur=request.user, statut='actif')

                    bp_user = Utilisateur.objects.get(username = request.user)
                    
                    return render(request, 'noyau/tableau_de_bord.html', {
                        'transactions': transactions,
                        'solde': solde,
                        'solde_et_solde_capital':solde_et_solde_capital,
                        'gains_aujourdhui': gains_aujourdhui,
                        'total_depots': total_depots,
                        'achats_actifs': achats_actifs,
                        'capital_actifs':capital_actifs,
                        'achats' : achats,
                        'total_trader_inactif':  total_trader_inactif,
                        'totaux_gen': totaux_gen, # gerant tous
                        'bp_user':bp_user,


                    })



            except ProfilUtilisateur.DoesNotExist:
                messages.error(request, "Votre profil est manquant. Il sera créé automatiquement.")
                ProfilUtilisateur.objects.create(utilisateur=request.user)
                solde = 0

            return render(request, 'noyau/tableau_de_bord.html', {'solde': solde})
        else:
             return redirect('accueil')




def vue_connexion(request):
    """Vue pour la connexion des utilisateurs."""
    if request.method == 'POST':
        email = request.POST.get('email')
        mot_de_passe = request.POST.get('mot_de_passe')
        utilisateur = authenticate(request, username=email, password=mot_de_passe)
        if utilisateur is not None:
            login(request, utilisateur)
            return redirect('tableau_de_bord')
        else:
            messages.error(request, "Identifiant ou mot de passe invalide.")
    return render(request, 'noyau/connexion.html')

def vue_deconnexion(request):
    """Vue pour la déconnexion."""
    logout(request)
    return redirect('connexion')







@login_required
def tableau_capital(request):
    # Capital des produits ACTIFS
    capital_actifs = Achat.objects.filter(
        utilisateur=request.user,
        statut='actif',
        date_fin__gte=timezone.now().date()  # Vérifie aussi la date
    ).aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0

    # Capital des produits EXPIRÉS
    capital_expires = Achat.objects.filter(
        utilisateur=request.user,
        statut='expire'
    ).aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0

    # Capital des produits ANNULÉS
    capital_annules = Achat.objects.filter(
        utilisateur=request.user,
        statut='annule'
    ).aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0

    # Capital TOTAL (tous statuts)
    capital_total = Achat.objects.filter(
        utilisateur=request.user
    ).aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0

    context = {
        'capital_actifs': capital_actifs,
        'capital_expires': capital_expires,
        'capital_annules': capital_annules,
        'capital_total': capital_total,
    }

    return render(request, 'noyau/capital.html', context)





@login_required
def get_achats_expirés_non_reinvestis(request):
    today = timezone.now().date()
    #reference = str(uuid.uuid4())
    # Filtrer les achats expirés et non réinvestis
    achats = Achat.objects.filter(
        utilisateur=request.user,
        est_reinvesti=False
    ).filter(
        Q(statut="expire") | Q(date_fin__lt=today)
    )

    # Calculer la somme
    total = achats.aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0
    context = {'achats' : achats, 'total':  total}
    print(total)
    try:
            if total != 0:

                            # partie traiter capital
                control_capital, created = CapitalClient.objects.get_or_create(utilisateur=request.user )
                if control_capital:
                            control_capital.capital += total  # On incrémente correctement
                            control_capital.save()            # On enregistre la modification

                achats.update(est_reinvesti=True)
                return redirect('tableau_de_bord')
            else:
                 return redirect('tableau_de_bord')
    except:
         return render(request, 'noyau/tableau_de_bord.html', context)







# dans views.py
from django.shortcuts import render

def custom_404(request, exception):
    return render(request, "404.html", status=404)


def cache_admin(request):
    return render(request, "404.html")


@login_required
def withdraw_status(request):
    """Return JSON with withdraw permission and referral counts for current user."""
    try:
        from .context_processors import withdraw_permission
        data = withdraw_permission(request)
        payload = {
            'can_withdraw': bool(data.get('can_withdraw', False)),
            'referrals_count': int(data.get('referrals_count', 0)),
            'required_referrals': int(data.get('required_referrals', 3)),
            'remaining_referrals': int(data.get('remaining_referrals', 3)),
            'message': data.get('withdraw_message', '')
        }
    except Exception:
        payload = {'can_withdraw': True, 'referrals_count': 0, 'required_referrals': 3, 'remaining_referrals': 0, 'message': ''}
    return JsonResponse(payload)







def download_app(request):
    # Chemin complet vers ton fichier
    filepath = os.path.join(settings.BASE_DIR, "apps_genius", "Genius_africa.apk")

    # Ouvrir le fichier et le renvoyer en téléchargement
    return FileResponse(open(filepath, "rb"), as_attachment=True, filename="Genius_africa.apk")








##################################################################################
##################################################################################



