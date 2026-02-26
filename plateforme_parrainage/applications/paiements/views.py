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


@login_required
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
                messages.error(request, f"Le montant doit être supérieur à zéro.\nSolde: {solde} CDF")
                return redirect('retrait')

            try:

                if montant < 5000 and int(solde_capital) != 0:
                    messages.error(request, f"Le montant minimum pour un retrait est de 5000 FC.\nSolde: {solde} CDF \n les {solde_capital} CDF est votre capital")
                    return redirect('retrait')

                if solde < montant and int(solde_capital) != 0:
                    messages.error(request, f"Solde insuffisant pour effectuer ce retrait.\nSolde: {solde} CDF . \n les {solde_capital} CDF est votre capital")
                    return redirect('retrait')
            except:
                pass

            if montant < 5000 :
                    messages.error(request, f"Le montant minimum pour un retrait est de 5000 FC.\nSolde: {solde} CDF ")
                    return redirect('retrait')

            if solde < montant :
                    messages.error(request, f"Solde insuffisant pour effectuer ce retrait.\nSolde: {solde} CDF .")
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
            messages.error(request, "Montant invalide. Veuillez entrer un montant valide.")
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
