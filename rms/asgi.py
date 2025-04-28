"""
ASGI config for rms project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django  # <-- Add this

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rms.settings")
django.setup()  # <-- Add this to initialize Django before importing anything else

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import dashboard.routing  # Ensure this module does not import models before settings are configured

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(dashboard.routing.websocket_urlpatterns)
    ),
})
