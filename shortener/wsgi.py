"""
WSGI config for shortener project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# get DJANGO_SETTINGS_MODULE from environment
# Fallback to prod if not set
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shortener.settings.prod')

application = get_wsgi_application()
