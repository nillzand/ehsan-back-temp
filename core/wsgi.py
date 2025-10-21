# back/core/wsgi.py (MODIFIED)

import os
from django.core.wsgi import get_wsgi_application
# [NEW] Import WhiteNoise
from whitenoise import WhiteNoise
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Get the standard Django application
application = get_wsgi_application()

# [NEW] Wrap the application with WhiteNoise
# This will serve files from STATIC_ROOT at the STATIC_URL
application = WhiteNoise(application, root=settings.STATIC_ROOT)

# [NEW] Add your MEDIA_ROOT to be served at the MEDIA_URL
# This is the key change to make your images work
application.add_files(settings.MEDIA_ROOT, prefix=settings.MEDIA_URL)