from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from applications.shop.models import Order
from .models import Depot, Retrait
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Depot
from applications.portefeuille.models import TransactionPortefeuille, CapitalClient
from django.contrib import messages
from django.db import IntegrityError
import uuid


# applications/paiements/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from applications.noyau.decorators import can_withdraw_required



@login_required
@can_withdraw_required
def vue_retrait(request):
    """Vue pour créer une demande de retrait."""
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
    solde = request.user.profil.get_solde()

    if request.method == 'POST':
        try:
            montant = Decimal(request.POST.get('montant', 0))
            methode = request.POST.get('methode')
            destination = request.POST.get('destination')

            # Vérifications de base
            if montant <= 0:
                messages.error(request, f"La somme doit être positive.\nSolde: {solde} CDF")
                return redirect('retrait')

            try:

                if montant < 5 and int(solde_capital) != 0:
                    messages.error(request, f"Le montant minimum requis pour un retrait est de 5 $.\nSolde: {solde} CDF \n ")
                    return redirect('retrait')

                if solde < montant and int(solde_capital) != 0:
                    messages.error(request, f"Vos ressources sont insuffisantes pour effectuer ce retrait.\nSolde: {solde} CDF .")
                    return redirect('retrait')
            except:
                pass

            if montant < 5 :
                    messages.error(request, f"La somme requise minimale pour un retrait est de 5 $.\nSolde: {solde} $ ")
                    return redirect('retrait')

            if solde < montant :
                    messages.error(request, f"Le solde n'est pas suffisant pour effectuer ce retrait.\nSolde: {solde} $ .")
                    return redirect('retrait')

            # Création du retrait
            retrait = Retrait.objects.create(
                utilisateur=request.user,
                montant=montant,
                methode=methode,
                destination=destination
            )

            # Enregistrement dans le portefeuille
            TransactionPortefeuille.objects.create(
                utilisateur=request.user,
                type='retrait',
                montant=montant,
                details=f"Retrait via {methode} vers {destination}, id retrait: {retrait.id}",
                reference = 'retrait'+str(uuid.uuid4())
            )

            messages.success(request, "Demande de retrait envoyée avec succès !")
            return redirect('liste_retraits')

        except ValueError:
            messages.error(request, "Montant non valide. Merci de saisir un montant valide.")
            return redirect('retrait')

    return render(request, 'paiements/retrait.html', {'solde': solde})




@login_required
def liste_depots(request):
    """Affiche la liste des dépôts de l'utilisateur connecté."""
    depots = Depot.objects.filter(utilisateur=request.user).order_by('-cree_le')
    return render(request, 'paiements/liste_depots.html', {'depots': depots})


@login_required
def liste_retraits(request):
    retraits = Retrait.objects.filter(utilisateur=request.user).order_by('-cree_le')
    return render(request, 'paiements/liste_retraits.html', {'retraits': retraits})
