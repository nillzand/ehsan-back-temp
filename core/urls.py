# core/urls.py
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path  # ۱. re_path را اضافه کنید
from django.views.static import serve         # ۲. serve را اضافه کنید

# JWT imports
from rest_framework_simplejwt.views import TokenRefreshView
from users.auth_views import MyTokenObtainPairView

# Local imports
from . import urls_admin
from .views import welcome

urlpatterns = [
    path('admin/', admin.site.urls),

    # مسیرهای اصلی API شما (بدون تغییر)
    path('api/admin/', include(urls_admin)),
    path('api/auth/', include('rest_framework.urls')),
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

# ۳. [اصلاح کلیدی] این بخش را جایگزین بلوک if settings.DEBUG قبلی کنید
# این کد به طور صریح به جنگو می‌گوید که فایل‌های media را در حالت توسعه سرو کند
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]