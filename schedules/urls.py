# schedules/urls.py (Corrected)

from django.urls import path, include
from rest_framework.routers import DefaultRouter
# vvv ADD THIS LINE vvv
from .views import ScheduleViewSet, DailyMenuViewSet 
from .views_user import MyCompanyMenuView

# Router for the main Schedule endpoint
router = DefaultRouter()
router.register(r'', ScheduleViewSet, basename='schedule') # Now this will work

# Manual URL patterns for the nested DailyMenu endpoint
# And now this will work
daily_menu_list = DailyMenuViewSet.as_view({'get': 'list', 'post': 'create'})
daily_menu_detail = DailyMenuViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})

urlpatterns = [
    # User-facing endpoint
    path('my-menu/', MyCompanyMenuView.as_view(), name='my-company-menu'),

    # Admin-facing endpoints
    path('', include(router.urls)),
    path('<int:schedule_pk>/daily_menus/', daily_menu_list, name='schedule-daily-menus-list'),
    path('<int:schedule_pk>/daily_menus/<int:pk>/', daily_menu_detail, name='schedule-daily-menus-detail'),
]