"""
ASGI config for api project.
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

application = get_asgi_application()

# Make sure application is available at module level
__all__ = ['application'] 