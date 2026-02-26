from django.urls import path
from . import views

urlpatterns = [
    path('pyramidp20/', views.liste_transactions, name='liste_transactions'),
    path('pyramidp21/', views.afficher_solde, name='afficher_solde'),
]
