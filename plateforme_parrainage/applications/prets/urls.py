from django.urls import path
from . import views

app_name = 'prets'

urlpatterns = [
    path('pyramid100', views.pret_list, name='list'),
    path('demander/', views.demander_pret, name='demander'),
    path('<int:pk>/', views.pret_detail, name='detail'),
]
