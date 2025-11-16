# back/schedules/views_user.py (نسخه نهایی با هر دو بهینه‌سازی)

from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Prefetch  # ایمپورت کردن Prefetch
from .models import Schedule, DailyMenu
from .serializers import ScheduleSerializer
from users.models import User 
from companies.models import Company

class MyCompanyMenuView(generics.ListAPIView):
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        user = self.request.user
        
        target_company = None
        
        if user.role == User.Role.SUPER_ADMIN:
            company_id = self.request.query_params.get('company_id')
            if company_id:
                try:
                    target_company = Company.objects.get(pk=company_id)
                except Company.DoesNotExist:
                    pass
        elif user.company:
            target_company = user.company

        context['company_for_pricing'] = target_company
        return context

    def get_queryset(self):
        user = self.request.user
        target_company = None

        if user.role == User.Role.SUPER_ADMIN:
            company_id = self.request.query_params.get('company_id')
            if company_id:
                target_company = get_object_or_404(Company, pk=company_id)
        elif user.company:
            target_company = user.company

        if not target_company:
            return Schedule.objects.none()

        active_schedule = target_company.active_schedule
        if not active_schedule:
            active_schedule = Schedule.objects.filter(company__isnull=True, is_active=True).first()
            
        if active_schedule:
            # --- [اصلاح کلیدی و نهایی] ---
            # ۱. تعریف بازه زمانی محدود برای جلوگیری از Timeout
            today = timezone.now().date()
            start_range = today - timedelta(days=7)
            end_range = today + timedelta(days=30)

            # ۲. ساخت یک prefetch سفارشی برای فیلتر کردن daily_menus در سطح دیتابیس
            filtered_daily_menus = Prefetch(
                'daily_menus',
                queryset=DailyMenu.objects.filter(date__range=(start_range, end_range)).prefetch_related(
                    'available_foods__dynamic_discounts',
                    'available_sides'
                )
            )

            # ۳. اجرای کوئری نهایی با تمام بهینه‌سازی‌ها
            return Schedule.objects.filter(pk=active_schedule.pk).select_related('company').prefetch_related(filtered_daily_menus)
        
        return Schedule.objects.none()