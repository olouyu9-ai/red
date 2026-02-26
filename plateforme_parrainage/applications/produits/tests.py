
@login_required
def mes_investissements(request):
    """Affiche les produits achetés et les bénéfices générés."""
    achats = Achat.objects.filter(utilisateur=request.user).order_by('-date_debut')

    investissements = []
    for achat in achats:
        # Calculer le total des gains quotidiens pour cet achat spécifique
        total_gains = sum(gain.montant for gain in achat.gains_quotidiens.all())

        # Calculer le bénéfice net pour cet achat
        benefice_net = total_gains - achat.prix_au_moment_achat

        # Calculer les jours restants pour cet achat
        jours_restants = (achat.date_fin - timezone.now().date()).days if achat.statut == 'actif' else 0

        investissements.append({
            'achat': achat,
            'total_gains': total_gains,
            'benefice_net': benefice_net,
            'jours_restants': jours_restants,
            'taux_quotidien': achat.produit.taux_quotidien,
        })

    context = {
        'investissements': investissements,
    }
    return render(request, 'produits/mes_investissements.html', context)
