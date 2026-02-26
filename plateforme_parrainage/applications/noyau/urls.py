from django.urls import path
from . import views
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static





urlpatterns = [
    path('admin/', views.admin_fonction, name='genius_admin'),
    path('accueil', views.vue_accueil, name='accueil'),
    path('tableau_de_bord', views.vue_tableau_de_bord, name='tableau_de_bord'),
    path('connexion/', views.vue_connexion, name='connexion'),
    path('deconnexion/', views.vue_deconnexion, name='deconnexion'),
    path('tableau_capital', views.tableau_capital, name='tableau_capital'),
    path('retirer_capital', views.get_achats_expirés_non_reinvestis, name='retirer_capital'),
    # partie de renseignement
    path('faq', views.faq, name='faq'),
    path('condition_utilisation', views.condition_utilisation, name='condition_utilisation'),
    path('politique_confid', views.politique_confid, name='politique_confid'),
    path('comment_faire_un_depot', views.comment_faire_un_depot, name='comment_faire_un_depot'),
    path('resilier_contrat',  views.resilier_contrat, name='resilier_contrat'),
    path("download/", views.download_app, name="download_app"),
    path('api/withdraw_status/', views.withdraw_status, name='api_withdraw_status'),

      # annonce plateforme



]
