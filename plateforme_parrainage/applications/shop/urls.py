
from django.urls import path
from applications.shop.views import sms_webhook, create_order

urlpatterns = [
   
    path('pyramid1', sms_webhook, name='sms_webhook'),
    path('pyramid2', create_order, name='create_order'),          
     
]
