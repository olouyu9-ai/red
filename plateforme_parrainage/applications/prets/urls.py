from django.urls import path
from . import views

app_name = 'prets'

urlpatterns = [

    # pages pour retraits crédit
    path('retraits/', views.voir_retraits, name='voir_retraits'),
    path('retraits/demander/', views.demander_retrait_credit, name='demander_retrait_credit'),

    # API JSON (usage AJAX ou mobile)
    path('api/verifier-eligibilite/', views.api_verifier_eligibilite, name='api_verifier_eligibilite'),
    path('api/demander-retrait/', views.api_demander_retrait, name='api_demander_retrait'),
    path('api/remboursement/<int:retrait_id>/', views.api_infos_remboursement, name='api_infos_remboursement'),
]
