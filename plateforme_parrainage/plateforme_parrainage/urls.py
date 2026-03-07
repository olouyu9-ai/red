from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.conf.urls.i18n import i18n_patterns



urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('applications.noyau.urls')),
   
    path('', include('applications.comptes.urls')),
    path('', include('applications.portefeuille.urls')),

    path('', include('applications.paiements.urls')),
    path('', include('applications.produits.urls')),
    path('', include('applications.parrainages.urls')),
    path('', include('applications.shop.urls')),
    path('prets/', include('applications.prets.urls')),
    path('chat/', include('applications.chat.urls')),

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path('i18n/', include('django.conf.urls.i18n')),
]
from django.contrib import admin

# Changer les textes affichés
admin.site.site_header = "Admin INVERTED"
admin.site.site_title = "Admin INVERTED - Tableau de bord   "
admin.site.index_title = "Bienvenue sur l’espace de gestion"
