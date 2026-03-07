# applications/noyau/middleware.py
from django.shortcuts import redirect
from django.urls import reverse

class AdminAccessMiddleware:
    """
    Bloque l'accès au /admin/ pour tous les utilisateurs non autorisés.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            user = request.user
            # Vérifie si l'utilisateur n'est pas staff ou superuser
            if not user.is_authenticated or not user.is_staff:
                #return redirect('/')  # ou une page "accès refusé"
                return redirect('admin.')  # ou une page "accès refusé"
        response = self.get_response(request)
        return response