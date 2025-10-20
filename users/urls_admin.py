# users/urls_admin.py
from django.urls import path
from .views_admin import AllocateBudgetView

urlpatterns = [
    path('employees/<int:user_id>/allocate_budget/', AllocateBudgetView.as_view(), name='admin-allocate-budget'),
]