# core/urls_admin.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from orders.views_admin import (
    AdminOrderViewSet,
    DailyOrderSummaryView, # این ایمپورت ممکن است دیگر استفاده نشود، اما برای اطمینان نگه دارید
    DashboardStatsView,
    AdminReportsView,
    WeeklyOrderSummaryView, # <-- این را اضافه کنید
)

router = DefaultRouter()
router.register(r'orders', AdminOrderViewSet, basename='admin-order')

urlpatterns = [
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('reports/daily-summary/', DailyOrderSummaryView.as_view(), name='daily-summary'),
    path('reports/weekly-summary/', WeeklyOrderSummaryView.as_view(), name='weekly-summary'), # <-- این خط را اضافه کنید
    path('reports/', AdminReportsView.as_view(), name='admin-reports'),
    path('wallets/', include('wallets.urls')),
    path('contracts/', include('contracts.urls')),
    path('', include('users.urls_admin')),
    path('', include(router.urls)),
]