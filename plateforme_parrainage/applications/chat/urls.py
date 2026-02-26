from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.GroupListView.as_view(), name='group_list'),
    path('create/', views.create_group, name='group_create'),
    path('groups/<uuid:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('groups/<uuid:pk>/send/', views.send_message, name='send_message'),
]
