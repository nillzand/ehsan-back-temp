
import os

from django.core.wsgi import get_wsgi_application

# This line points to your project's settings file.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# core/wsgi.py (Corrected)
application = get_wsgi_application()