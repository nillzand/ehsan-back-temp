# core/settings.py
from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv
import dj_database_url

# Load environment variables from a .env file
load_dotenv()

# ==================== Base Path ====================
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==================== Security ====================
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-secret-key-for-dev')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# [اصلاح ۱] دامنه بک‌اند خود را به این لیست اضافه می‌کنیم
ALLOWED_HOSTS_str = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,ehsan-back-temp.darkube.app')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_str.split(',') if host.strip()]


# ==================== Installed Apps ====================
INSTALLED_APPS = [
    # Django default apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',

    # Local apps
    'core',
    'users',
    'companies',
    'menu',
    'schedules',
    'orders',
    'wallets',
    'contracts',
    'surveys',
    'discounts', 
]

# ==================== Middleware ====================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==================== URL / WSGI ====================
ROOT_URLCONF = 'core.urls'
WSGI_APPLICATION = 'core.wsgi.application'

# ==================== Templates ====================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# ==================== Authentication ====================
AUTH_USER_MODEL = 'users.User'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/'


# ==================== Database ====================
# Option 1: Try to build the database URL from individual environment variables (Ideal for Darkube)
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_PORT = os.environ.get('DB_PORT')

# Option 2: Check for a single DATABASE_URL variable
DATABASE_URL = os.environ.get('DATABASE_URL')

# Logic to choose the database configuration
if DB_HOST and DB_NAME and DB_USER and DB_PASS and DB_PORT:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASS,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
        }
    }
elif DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600, ssl_require=False)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# --- PRODUCTION SECURITY SETTINGS ---
if not DEBUG:
    SECURE_PROXY_SSL_HEADER  = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = False # Set to True if your proxy handles SSL termination
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ==================== REST Framework ====================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
}

# ==================== Simple JWT ====================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# ==================== CORS ====================
# [اصلاح ۲] دامنه فرانت‌اند با https به لیست مبداهای مجاز اضافه شده است
CORS_ALLOWED_ORIGINS_str = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173,https://ehsan-restaurant.nilva.ai,https://ehsan-front-temp.darkube.app')
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOWED_ORIGINS_str.split(',') if origin.strip()]

# [اصلاح ۳] دامنه فرانت‌اند با https به لیست مبداهای مورد اعتماد برای CSRF اضافه شده است
CSRF_TRUSTED_ORIGINS_str = os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173,https://ehsan-restaurant.nilva.ai,https://ehsan-front-temp.darkube.app')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in CSRF_TRUSTED_ORIGINS_str.split(',') if origin.strip()]

CORS_ALLOW_CREDENTIALS=True

# ==================== Static & Media ====================
STATIC_URL = '/staticfiles/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==================== Internationalization ====================
LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'UTC'
USE_I18N = True 
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / 'locale']

# ==================== Default Primary Key Field ====================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== Custom Settings ====================
RESERVATION_LEAD_DAYS = 1

# ==================== Logging ====================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',  
    },
}