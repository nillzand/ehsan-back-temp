# back/schedules/views_user.py
from rest_framework import generics, permissions
from .models import Schedule
from .serializers import ScheduleSerializer
from users.models import User # <-- Import User model

class MyCompanyMenuView(generics.ListAPIView):
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # ادمین کل همه برنامه‌ها را برای مدیریت می‌بیند
        if user.is_superuser or user.role == User.Role.SUPER_ADMIN:
            return Schedule.objects.prefetch_related(
                'daily_menus__available_foods',
                'daily_menus__available_sides'
            ).select_related('company').order_by('company__name', 'name')
            
        active_schedule = None
        if user.company:
            # 1. اولویت با برنامه‌ی اختصاصی شرکت است
            if user.company.active_schedule:
                active_schedule = user.company.active_schedule
        
        # 2. اگر برنامه اختصاصی نبود، به دنبال برنامه پیش‌فرض فعال بگرد
        if not active_schedule:
            default_schedule = Schedule.objects.filter(company__isnull=True, is_active=True).first()
            active_schedule = default_schedule
            
        # اگر برنامه‌ای (اختصاصی یا پیش‌فرض) پیدا شد، آن را برگردان
        if active_schedule:
            return Schedule.objects.filter(pk=active_schedule.pk).prefetch_related(
                'daily_menus__available_foods',
                'daily_menus__available_sides'
            )
        
        # در غیر این صورت، لیست خالی برگردان
        return Schedule.objects.none()