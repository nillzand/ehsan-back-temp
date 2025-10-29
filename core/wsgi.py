# core/wsgi.py

import os
from django.core.wsgi import get_wsgi_application
# [NEW] Import necessary settings
from django.conf import settings
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Get the base Django application
application = get_wsgi_application()

# [MODIFIED] Wrap the application with WhiteNoise and add the MEDIA_ROOT
# This tells WhiteNoise to serve files from your MEDIA_ROOT at the MEDIA_URL prefix
application = WhiteNoise(application, root=settings.MEDIA_ROOT)
application.add_files(settings.STATIC_ROOT, prefix=settings.STATIC_URL.lstrip('/'))