# applications/noyau/decorators.py
from functools import wraps
from django.shortcuts import redirect
from applications.noyau.context_processors import withdraw_permission

def can_withdraw_required(view_func):
    """
    Décorateur pour protéger la vue retrait.
    Redirige vers une page d'information si la tâche n'est pas accomplie.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        context = withdraw_permission(request)
        if not context.get('can_withdraw', False):
            # Redirige vers une page qui explique ce qu'il doit accomplir
            # ou affiche un message d'erreur
            return redirect('tableau_de_bord')  # tu peux créer une page 'page_tache'
              
        return view_func(request, *args, **kwargs)
    return _wrapped_view