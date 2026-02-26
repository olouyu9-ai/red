# payments/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.conf import settings
from decimal import Decimal
from applications.shop.models import Order, PaymentMessage
from applications.shop.sms_parser import parse_payment_sms
from django.contrib.auth.decorators import login_required
import json
from django.contrib import messages
from django.db import transaction
from django.db import IntegrityError
from django.contrib import messages
from applications.portefeuille.models import TransactionPortefeuille
from applications.paiements.models import Depot


@csrf_exempt
def get_post_body(request):
    """
    Supporte application/json ET form-encoded.
    Retourne un dict avec au moins 'message' si possible.
    """
    if request.content_type and "application/json" in request.content_type:
        try:
            data = json.loads(request.body.decode("utf-8"))
            print(data)
        except Exception:
            return {}
    else:
        data = request.POST.dict()
    return data

@csrf_exempt
def sms_webhook(request):

    data = get_post_body(request)
    #sms_text = data.get("message") or data.get("sms") or data.get("body")
    #sender = data.get("from") or data.get("sender") or ""

    sms_text = data.get("message") or data.get("message_content") or data.get("sms") or data.get("body")
    sender = data.get("from") or data.get("sender") or data.get("sender_number") or ""

    if not sms_text:
      return HttpResponseBadRequest("No message provided (aucun message reçu ou conf json)")

    # 2) Sauvegarder le SMS brut (traçabilité)
    msg = PaymentMessage.objects.create(sms_text=sms_text, sender=sender)

    # 3) Extraire montant + référence
    amount, reference = parse_payment_sms(sms_text)
    if not amount or not reference:
        msg.error = "Impossible d'extraire montant/référence"
        msg.save()
        return JsonResponse({"status": "ignored", "reason": "parse_failed"})

    # Remplir et dédupliquer par référence (si le même SMS arrive 2x)
    msg.amount = amount
    msg.reference = reference
    try:
        msg.save()  # échouera si reference déjà prise (unique)
    except Exception:
        # déjà traité avant
        return JsonResponse({"status": "duplicate", "reference": reference})

    # 4) Tenter de valider une commande correspondante
    try:
        order = Order.objects.get(reference_code=reference, is_paid=False)
        # Créer le dépôt
        depot = Depot.objects.create(
                utilisateur=order.user,
                montant=order.amount,
                methode=order.customer_name,
                reference=reference
                        )

                        # Créditer le portefeuille de l'utilisateur
        nouveau_solde = order.user.profil.get_solde() + order.amount
        TransactionPortefeuille.objects.create(
                utilisateur=order.user,
                type='depot',
                montant=order.amount,
                reference=f"{depot.reference}",
                solde_apres=nouveau_solde
                        )
    except Order.DoesNotExist:
        # Pas encore de commande avec ce code -> on garde le SMS en stock
        return JsonResponse({"status": "stored", "reference": reference, "note": "order_not_found_yet"})

    # Vérifier montant strictement égal
    if order.amount == amount:
        order.is_paid = True
        order.save()
        msg.processed = True
        msg.save()
        return JsonResponse({"status": "ok", "message": "Commande validée", "reference": reference})
    else:
        msg.error = f"Montant SMS {amount} != commande {order.amount}"
        msg.save()
        return JsonResponse({"status": "mismatch_amount", "reference": reference})

@login_required
@csrf_exempt
def create_orde(request):
    """
    Formulaire minimal pour créer une commande:
    montant + nom client
    """
    if request.method == "POST":
        amount = Decimal(request.POST.get("amount"))
        name = request.POST.get("name") or ""
        reference = request.POST.get("reference") or ""
        order = Order.objects.create(customer_name=name, reference_code=reference, amount=amount, user=request.user )

        # Stocker l'ID de la commande dans la session pour la récupérer plus tard
        
        
        #return render(request, "created.html", {"order": order})

    return render(request, "create.html")

##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################
##################################################################################################


@login_required
@csrf_exempt
def create_order(request):
    if request.method == "POST":
        amount_raw = request.POST.get("amount")
        name = request.POST.get("name", "").strip()
        refc = request.POST.get("reference_code", "").strip()
        ref = refc + "."  # Ta logique spécifique

        # 1. Validation de base
        if not amount_raw or not refc:
            messages.error(request, "montant et référence sont obligatoires.")
            return render(request, "deposit_form.html")

        if True:
            amount = Decimal(amount_raw)
            
            # Vérifier si cette référence est déjà utilisée dans une commande payée
            if Order.objects.filter(reference_code=ref, is_paid=True).exists():
                messages.error(request, "référence déjà été validée.")
                return render(request, "deposit_form.html")
            
            # Vérifier si cette référence est déjà utilisée dans une commande non payé
            if Order.objects.filter(reference_code=ref, is_paid=False).exists():
                messages.error(request, " référence est déjà utilisée .")
                return render(request, "deposit_form.html")
            try:
                    with transaction.atomic():
                        # 2. Création immédiate de la commande (Order)
                        order = Order.objects.create(
                            customer_name=name,
                            amount=amount,
                            reference_code=ref,
                            user=request.user,
                            is_paid=False
                        )

                        # 3. Recherche du message de paiement (PaymentMessage)
                        # On cherche soit avec le point, soit sans le point
                        msg = PaymentMessage.objects.filter(
                            reference__in=[ref, refc], 
                            processed=False
                        ).order_by("-received_at").first()

                        if msg:
                            # Vérification du montant
                            if float(msg.amount) == float(order.amount):
                                # --- LE PAIEMENT EST VALIDE ---
                                order.is_paid = True
                                order.save()

                                msg.processed = True
                                msg.save()

                                # Création du dépôt officiel
                                depot = Depot.objects.create(
                                    utilisateur=request.user,
                                    montant=order.amount,
                                    methode=name or "Mobile Money",
                                    reference=ref
                                )

                                # Créditer le portefeuille
                                profil = request.user.profil
                                nouveau_solde = profil.get_solde() + order.amount
                                
                                TransactionPortefeuille.objects.create(
                                    utilisateur=request.user,
                                    type='depot',
                                    montant=order.amount,
                                    reference=ref,
                                    solde_apres=nouveau_solde
                                )

                                messages.success(request, "Succès !.")
                                return render(request, "paid.html", {"order": order, "depot": depot})
                            
                            else:
                                # Montant incorrect
                                messages.error(request, f"Le montant  ({msg.amount}) ne correspond pas à votre saisie ({order.amount}).")
                                return render(request, "deposit_form.html")
                        
                        else:
                            # Message non trouvé (le SMS n'est pas encore arrivé dans la base)
                            # On stocke l'ID en session pour que l'utilisateur puisse suivre l'attente
                            request.session['last_order_id'] = order.id
                            return render(request, "waiting.html", {"order": order})
            except IntegrityError:
                messages.error(request, "Veuillez réessayer.")
        

    return render(request, "deposit_form.html")

