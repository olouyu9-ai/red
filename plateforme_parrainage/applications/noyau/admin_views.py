from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from applications.comptes.models import Utilisateur, ProfilUtilisateur
from applications.paiements.models import Depot, Retrait
from applications.produits.models import Produit

@user_passes_test(lambda u: u.is_staff)
def vue_liste_utilisateurs(request):
    """Vue pour lister tous les utilisateurs (réservée aux administrateurs)."""
    utilisateurs = Utilisateur.objects.all()
    return render(request, 'noyau/admin/utilisateurs.html', {'utilisateurs': utilisateurs})

@user_passes_test(lambda u: u.is_staff)
def vue_liste_depots(request):
    """Vue pour lister tous les dépôts (réservée aux administrateurs)."""
    depots = Depot.objects.all().order_by('-cree_le')
    return render(request, 'noyau/admin/depots.html', {'depots': depots})

@user_passes_test(lambda u: u.is_staff)
def vue_liste_retraits(request):
    """Vue pour lister tous les retraits (réservée aux administrateurs)."""
    retraits = Retrait.objects.all().order_by('-cree_le')
    return render(request, 'noyau/admin/retraits.html', {'retraits': retraits})

@user_passes_test(lambda u: u.is_staff)
def vue_liste_produits_admin(request):
    """Vue pour gérer les produits (réservée aux administrateurs)."""
    produits = Produit.objects.all()
    return render(request, 'noyau/admin/produits.html', {'produits': produits})
