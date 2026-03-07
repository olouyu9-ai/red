from django import template
from applications.prets.utils import VerificateurEligibilite, GestionnaireRemboursement
from applications.prets.models import RetraitCredit

register = template.Library()

@register.filter
def can_withdraw_credit(user):
    """Retourne True si l'utilisateur peut demander un retrait crédit."""
    is_eligible, _, _ = VerificateurEligibilite.verifier_utilisateur(user)
    return is_eligible

@register.filter
def filleuls_info(user):
    """Nombre de filleuls valides / requis."""
    is_eligible, nb, requis = VerificateurEligibilite.verifier_utilisateur(user)
    return f"{nb}/{requis}"

@register.filter
def montant_max_retrait(user):
    """Montant maximum autorisé formaté."""
    montant = VerificateurEligibilite.obtenir_montant_max_autorise(user)
    return f"{montant}$"

@register.filter
def filleuls_manquants(user):
    """Nombre de filleuls manquants pour atteindre l'éligibilité."""
    is_eligible, nb, requis = VerificateurEligibilite.verifier_utilisateur(user)
    return max(0, requis - nb)

@register.filter
def retrait_actif(user):
    """Renvoie le retrait en cours si présent."""
    return RetraitCredit.objects.filter(
        utilisateur=user,
        statut__in=['demande', 'approuve', 'en_remboursement']
    ).first()

@register.filter
def progression_retrait(retrait):
    """Progression du remboursement en pourcentage."""
    if not retrait:
        return 0
    return GestionnaireRemboursement.calculer_progression(retrait)
