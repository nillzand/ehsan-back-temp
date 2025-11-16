# back/schedules/views_user.py (نسخه نهایی و بهینه شده)

from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404
from .models import Schedule
from .serializers import ScheduleSerializer
from users.models import User 
from companies.models import Company

class MyCompanyMenuView(generics.ListAPIView):
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        """
        Passes the correct company context to the serializer for accurate pricing.
        A Super Admin can specify a company, otherwise the user's own company is used.
        """
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
        """
        Returns the active schedule for the user's company.
        This version is optimized to prevent the N+1 query problem.
        """
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
            # --- [اصلاح کلیدی] ---
            # ما به جنگو می‌گوییم که تمام تخفیف‌های مربوط به تمام غذاهای این منو را
            # به صورت یکجا و بهینه واکشی کند.
            return Schedule.objects.filter(pk=active_schedule.pk).select_related('company').prefetch_related(
                'daily_menus__available_foods__dynamic_discounts', # این خط مشکل را حل می‌کند
                'daily_menus__available_sides'
            )
        
        return Schedule.objects.none()