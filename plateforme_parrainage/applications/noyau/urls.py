from django.urls import path
from . import views
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static





urlpatterns = [
    
  
    path('tableau_de_bord', views.vue_tableau_de_bord, name='tableau_de_bord'),
    path('connexion/', views.vue_connexion, name='connexion'),
    path('deconnexion/', views.vue_deconnexion, name='deconnexion'),
    path('tableau_capital', views.tableau_capital, name='tableau_capital'),
    path('retirer_capital', views.get_achats_expirés_non_reinvestis, name='retirer_capital'),
    # partie de renseignement
   
    path("download/", views.download_app, name="download_app"),
    path('api/withdraw_status/', views.withdraw_status, name='api_withdraw_status'),
    path('admin./', views.cache_admin, name='admin.'),  # Cache l'admin derrière une fausse page 404

      # annonce plateforme



]
