from django.urls import path
from django.urls import path
from . import views

urlpatterns = [
    path('pyramid30/', views.afficher_code_parrainage, name='mon_code_parrainage'),
    path('pyramid31/', views.liste_filleuls, name='liste_filleuls'),
    path('pyramid32/', views.liste_bonus_parrainage, name='liste_bonus_parrainage'),
]
