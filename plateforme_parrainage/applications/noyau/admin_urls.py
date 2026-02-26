from django.urls import path
from . import admin_views

urlpatterns = [
    path('utilisateurs/', admin_views.vue_liste_utilisateurs, name='admin_utilisateurs'),
    path('depots/', admin_views.vue_liste_depots, name='admin_depots'),
    path('retraits/', admin_views.vue_liste_retraits, name='admin_retraits'),
    path('produits/', admin_views.vue_liste_produits_admin, name='admin_produits'),
]
