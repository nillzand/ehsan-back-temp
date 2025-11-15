# back/discounts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DiscountCodeViewSet, DynamicMenuDiscountViewSet, ValidateDiscountCodeView

router = DefaultRouter()
router.register(r'codes', DiscountCodeViewSet, basename='discount-code')
router.register(r'dynamic-menu', DynamicMenuDiscountViewSet, basename='dynamic-menu-discount')

# URL جدید برای اعتبارسنجی کد
urlpatterns = [
    path('validate-code/', ValidateDiscountCodeView.as_view(), name='validate-discount-code'),
    path('', include(router.urls)),
]