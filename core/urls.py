# core/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

# JWT imports
from rest_framework_simplejwt.views import TokenRefreshView
from users.auth_views import MyTokenObtainPairView  # Custom JWT login

# Local imports
from . import urls_admin
from .views import welcome

urlpatterns = [
    # Root welcome
    path('', welcome, name='api-welcome'),

    # Django Admin
    path('admin/', admin.site.urls),

    # Admin API endpoints
    path('api/admin/', include(urls_admin)),

    # API Authentication
    path('api/auth/', include('rest_framework.urls')),  # browsable API login
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # App-specific endpoints
    path('api/users/', include('users.urls')),
    path('api/companies/', include('companies.urls')),
    path('api/menu/', include('menu.urls')),
    path('api/schedules/', include('schedules.urls')),
    path('api/orders/', include('orders.urls')),
]

# [FIXED] Serve static and media files in both development and production.
# In production (DEBUG=False), Django doesn't serve these files itself.
# However, these URL patterns are needed so that Whitenoise can recognize
# requests for these files and serve them from STATIC_ROOT and MEDIA_ROOT.
# The `if settings.DEBUG:` check has been removed.
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)