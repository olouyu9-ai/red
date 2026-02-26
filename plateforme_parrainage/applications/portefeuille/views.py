from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import TransactionPortefeuille

@login_required
def liste_transactions(request):
    """Affiche la liste des transactions de l'utilisateur connecté."""
    transactions = TransactionPortefeuille.objects.filter(utilisateur=request.user).order_by('-cree_le')
    return render(request, 'portefeuille/transactions.html', {'transactions': transactions})

@login_required
def afficher_solde(request):
    """Affiche le solde actuel de l'utilisateur connecté."""
    # Logique pour calculer le solde (exemple simplifié)
    depots = sum(t.montant for t in TransactionPortefeuille.objects.filter(utilisateur=request.user, type='depot'))
    gains = sum(t.montant for t in TransactionPortefeuille.objects.filter(utilisateur=request.user, type='gain_quotidien'))
    bonus = sum(t.montant for t in TransactionPortefeuille.objects.filter(utilisateur=request.user, type='bonus_parrainage'))
    retraits = sum(t.montant for t in TransactionPortefeuille.objects.filter(utilisateur=request.user, type='retrait'))

    solde = (depots + gains + bonus) - retraits

    return render(request, 'portefeuille/solde.html', {'solde': solde})
