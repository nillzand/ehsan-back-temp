# ehsan-back-temp/core/urls.py

from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from rest_framework_simplejwt.views import TokenRefreshView
# --- [اصلاح ۱] --- ایمپورت کردن View سفارشی
from users.auth_views import MyTokenObtainPairView 

from . import urls_admin
from .views import welcome

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/admin/', include(urls_admin)),
    path('api/auth/', include('rest_framework.urls')),
    
    # --- [اصلاح ۲] --- استفاده از MyTokenObtainPairView به جای نسخه پیش‌فرض
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/users/', include('users.urls')),
    path('api/companies/', include('companies.urls')),
    path('api/menu/', include('menu.urls')),
    path('api/schedules/', include('schedules.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/surveys/', include('surveys.urls')),
    path('api/discounts/', include('discounts.urls')), 
    path('', welcome, name='api-welcome'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)