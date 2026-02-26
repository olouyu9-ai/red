"""
ASGI config for plateforme_parrainage project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

# Ensure settings are configured before importing Django modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_parrainage.settings')

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from importlib import import_module

# Initialize Django ASGI application first (this loads app registry)
django_asgi_app = get_asgi_application()

# Import app routing after apps are loaded to avoid AppRegistryNotReady
chat_routing = import_module('applications.chat.routing')

application = ProtocolTypeRouter({
	"http": django_asgi_app,
	"websocket": AuthMiddlewareStack(
		URLRouter(
			chat_routing.websocket_urlpatterns
		)
	),
})
