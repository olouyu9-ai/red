from django.urls import path
from . import views

urlpatterns = [
    path('ramid0001/', views.vue_inscription, name='inscription'),
    path('pyramid0002/', views.vue_ajouter_code_parrain, name='ajouter_parrain'),
    path('pyramid0003/', views.profile_view, name='profile'),
    path('pyramid0004/', views.profile_edit, name='profile_edit'),
]
