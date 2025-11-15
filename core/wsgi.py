# core/wsgi.py

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()

# ما WhiteNoise را در اینجا برای فایل‌های مدیا پیکربندی نمی‌کنیم.
# این کار باید توسط Nginx در پروداکشن انجام شود.