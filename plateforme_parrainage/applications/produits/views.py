import uuid
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from applications.paiements.models import Depot
from applications.produits.models import Produit, Achat
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone
from applications.portefeuille.models import CapitalClient, TransactionPortefeuille
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from applications.portefeuille.models import TransactionPortefeuille
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum
from django.shortcuts import render
from decimal import Decimal
from django.db.utils import OperationalError





"""def vue_liste_produits(request):

    capital_actifs = Achat.objects.filter(
        utilisateur=request.user,
        statut='actif',
        date_fin__gte=timezone.now().date()  # Vérifie aussi la date
    ).aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0
    produits = Produit.objects.filter(est_actif=True)
    return render(request, 'produits/liste.html', {'produits': produits, 'capital_actifs': capital_actifs})
"""




@login_required
def vue_liste_produits(request):
    capital_actifs = Achat.objects.filter(
        utilisateur=request.user,
        statut='actif',
        date_fin__gte=timezone.now().date()  # Vérifie aussi la date
    ).aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0
    # Récupération du nombre de jours (par ex. via GET ?jours=)

    produits = Produit.objects.filter(est_actif=True)

    produits_data = []
    for produit in produits:
        # calcul du bénéfice avec la durée propre du produit
        benefice = int(produit.prix * produit.taux_quotidien * produit.duree_jours)
        gains_conv =  float(produit.taux_quotidien*100)


        produits_data.append({
            "id": produit.id,
            "nom": produit.nom,
            "description": produit.description,
            "prix": produit.prix,
            "duree_jours": produit.duree_jours,
            "taux_quotidien": gains_conv,
            "benefice": benefice,
            "image": produit.image.url if produit.image else None,
        })




    return render(request, 'produits/liste.html', {
        "produits": produits_data,
        'capital_actifs': capital_actifs,

    })




@login_required
def vue_achat(request, produit_id):


    capital_actifs = Achat.objects.filter(
        utilisateur=request.user,
        statut='actif',
        date_fin__gte=timezone.now().date()  # Vérifie aussi la date
    ).aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0
    # Récupération du nombre de jours (par ex. via GET ?jours=)

    if capital_actifs == 0:
            produit = get_object_or_404(Produit, id=produit_id)
            gain_a = float(produit.prix) * float(produit.taux_quotidien)
            gain = int(gain_a)
            gain_total_b = float(produit.prix) * float(produit.taux_quotidien) * float(produit.duree_jours)
            gain_total = int(gain_total_b)
            solde = request.user.profil.get_solde()

            # traitement capital


            try:
                capital = CapitalClient.objects.filter(utilisateur=request.user).first()
                if capital:
                    solde_capital = capital.capital
                else:
                    solde_capital = 0
            except OperationalError:
                # La table n'existe pas encore
                solde_capital = 0
            solde_et_solde_capital = float(solde + solde_capital)

            if request.method == 'POST':

                # Vérifier que
                if produit.prix < int(solde_capital):
                    messages.error(request, "Vous ne pouvez pas signer un contrat plus bas que votre capital de base.")
                    #return redirect('liste_produits')
                    return render(request, 'produits/achat.html', {'produit': produit, 'solde': solde_et_solde_capital, 'gain':gain, 'gain_total':gain_total})


                # Vérifier que le solde est suffisant
                if solde_et_solde_capital < produit.prix:
                    messages.error(request, f"Solde insuffisant pour signer ce contrat. {solde_et_solde_capital} FC")
                    #return redirect('liste_produits')
                    return render(request, 'produits/achat.html', {'produit': produit, 'solde': solde_et_solde_capital, 'gain':gain, 'gain_total':gain_total})

                # Vérifier que le prix est supérieur à 0
                if produit.prix <= 0:
                    messages.error(request, "Le prix du contrat est invalide.")
                    #return redirect('liste_produits')
                    return render(request, 'produits/achat.html', {'produit': produit, 'solde': solde_et_solde_capital, 'gain':gain, 'gain_total':gain_total})


                # traitement capital




                try:
                    #if solde_et_solde_capital >= produit.prix and int(solde_capital) != 0 and solde < produit.prix :
                    if solde_et_solde_capital >= produit.prix and int(solde_capital) != 0  :


                            TransactionPortefeuille.objects.create(
                                utilisateur=request.user,
                                type='capital',
                                montant=solde_capital,
                                reference = 'capital_via_genius_africa'
                            )
                            # enlever la somme
                            capital.capital = 0   # On soustrait le montant
                            capital.save()
                except:
                    pass



                # Créer l'achat
                achat = Achat.objects.create(
                    utilisateur=request.user,
                    produit=produit,
                    prix_au_moment_achat=produit.prix,
                    date_fin=timezone.now().date() + timezone.timedelta(days=produit.duree_jours)
                )

                # Créer une transaction pour déduire le montant du solde
                nouveau_solde = solde - produit.prix
                TransactionPortefeuille.objects.create(
                    utilisateur=request.user,
                    type='achat',
                    montant=-produit.prix,  # Montant négatif pour indiquer une sortie
                    reference=f"Achat de {produit.nom} (ID: {achat.id})",
                    solde_apres=nouveau_solde
                )

                #control, created = Control_achat.objects.get_or_create(  utilisateur=request.user)
                """if control.jours_payes == 0:
                    control.jours_payes = 1
                    control.save()"""
                # permet de visualiser le fond que l'utilisateur a investit
                messages.success(request, f"le contrat de {produit.nom} effectué avec succès !")
                return redirect('mes_investissements')

            return render(request, 'produits/achat.html', {'produit': produit, 'solde': solde_et_solde_capital, 'gain':gain, 'gain_total':gain_total})
    else:
        return redirect('liste_produits')



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

    total_investi = sum(Decimal(achat.prix_au_moment_achat) for achat in achats)
    total_benefices = sum(inv['total_gains'] for inv in investissements)

    # Calculer le rendement en pourcentage
    rendement = 0
    if total_investi > 0:
        rendement = float(total_benefices) / float(total_investi) * 100

    context = {
        'investissements': investissements,
        'total_benefices': total_benefices,
        'total_investi': total_investi,
        'rendement': rendement,
    }
    return render(request, 'produits/mes_investissements.html', context)
