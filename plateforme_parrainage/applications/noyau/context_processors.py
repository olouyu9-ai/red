from django.db.models import Count

def withdraw_permission(request):
    """Context processor that exposes whether the current user can withdraw.

    Logic:
    - If user has at least one `Achat`, take their most recent `Achat`.
    - Require `required_referrals` (3) BonusParrainage records where the parrain is the user
      and the referred `achat` is for the same product as the user's achat.
    - Expose `can_withdraw` (bool) and `withdraw_message` (str).
    """
    user = getattr(request, 'user', None)
    context = {'can_withdraw': True, 'withdraw_message': '', 'referrals_count': 0, 'required_referrals': 3, 'remaining_referrals': 3}

    if not user or not getattr(user, 'is_authenticated', False):
        context['can_withdraw'] = False
        context['withdraw_message'] = 'Connectez-vous pour accéder au retrait.'
        return context

    try:
        from applications.produits.models import Achat
        from applications.parrainages.models import BonusParrainage
    except Exception:
        context['can_withdraw'] = True
        return context

    # Ensure we pick the most recently created Achat: order by date then id to
    # disambiguate multiple achats on the same day.
    latest_achat = Achat.objects.filter(utilisateur=user).order_by('-date_debut', '-id').first()
    if not latest_achat:
        context['can_withdraw'] = False
        context['withdraw_message'] = "Vous devez d'abord procéder à l'allocation d'un serveur afin d'activer le retrait."
        return context

    required_referrals = 3
    # Count only referrals (their achat) that happened on/after the user's latest achat.
    # This ensures that if the user buys a new product, previous referrals do not
    # automatically unlock the withdraw button for the new purchase.
    # Use the referred achat id to determine ordering: only referrals whose
    # achat was created after the user's latest achat should count. This avoids
    # problems when multiple achats occur on the same date.
    count = BonusParrainage.objects.filter(
        parrain=user,
        achat__produit=latest_achat.produit,
        achat__id__gt=latest_achat.id
    ).count()
    remaining = max(0, required_referrals - count)

    context['referrals_count'] = count
    context['required_referrals'] = required_referrals
    context['remaining_referrals'] = remaining

    if count < required_referrals:
        context['can_withdraw'] = False
        context['withdraw_message'] = f"Invitez {required_referrals} Utilisateurs ayant effectué la même allocation de serveur ({latest_achat.produit.nom}). ({count}/{required_referrals})"
    else:
        context['can_withdraw'] = True
    return context
