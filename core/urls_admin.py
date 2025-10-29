# core/urls_admin.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from orders.views_admin import (
    AdminOrderViewSet,
    DailyOrderSummaryView,
    DashboardStatsView,
    AdminReportsView,
)

# --- Register ViewSet routes ---
router = DefaultRouter()
router.register(r'orders', AdminOrderViewSet, basename='admin-order')

# --- URL patterns ---
urlpatterns = [
    # --- Dashboard & Reports ---
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('reports/daily-summary/', DailyOrderSummaryView.as_view(), name='daily-summary'),
    path('reports/', AdminReportsView.as_view(), name='admin-reports'),

    # --- Wallet, Contract, and User Management ---
    path('wallets/', include('wallets.urls')),
    path('contracts/', include('contracts.urls')),  # [NEW] Contracts management endpoints
    path('', include('users.urls_admin')),  # Employee/user management routes

    # --- Orders ViewSet routes ---
    path('', include(router.urls)),
]
