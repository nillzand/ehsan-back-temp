# ehsan-back-temp/core/urls.py
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path  # <--- re_path را اضافه کنید و path را نگه دارید
from django.conf.urls.static import static

from rest_framework_simplejwt.views import TokenRefreshView
from users.auth_views import MyTokenObtainPairView

from . import urls_admin
from .views import welcome

urlpatterns = [
    path('admin/', admin.site.urls),

    # مسیرهای اصلی API
    path('api/admin/', include(urls_admin)),
    path('api/auth/', include('rest_framework.urls')),
    
    # [اصلاح کلیدی] استفاده از re_path برای پذیرش URL با و بدون اسلش پایانی
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

# سرو کردن فایل‌های مدیا در حالت DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)