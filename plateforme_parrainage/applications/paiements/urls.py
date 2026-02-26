from django.urls import path
from . import views



urlpatterns = [
    #path('depot/', views.vue_depot, name='depot'),
    path('pyramid40/', views.vue_retrait, name='retrait'),
    path('pyramid41/', views.liste_depots, name='liste_depots'),
    path('pyramid42/', views.liste_retraits, name='liste_retraits'),  # Assurez-vous que cette ligne est présente
]
