# back/schedules/views_user.py
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
        
        # If the user is a Super Admin, they can view the menu of any company
        # by providing a 'company_id' in the query parameters.
        if user.role == User.Role.SUPER_ADMIN:
            company_id = self.request.query_params.get('company_id')
            if company_id:
                try:
                    target_company = Company.objects.get(pk=company_id)
                except Company.DoesNotExist:
                    pass  # Let get_queryset handle the 404 or empty response
        
        # For any other user (like Company Admin or Employee), use their own company.
        elif user.company:
            target_company = user.company

        context['company_for_pricing'] = target_company
        return context

    def get_queryset(self):
        """
        Returns the active schedule for the user's company.
        A Super Admin can specify a company_id to see a specific company's menu.
        If a company has no specific active schedule, it falls back to the default schedule.
        """
        user = self.request.user
        target_company = None

        if user.role == User.Role.SUPER_ADMIN:
            company_id = self.request.query_params.get('company_id')
            if company_id:
                # Super Admin is requesting a specific company's menu
                target_company = get_object_or_404(Company, pk=company_id)
        elif user.company:
            # Regular user (Employee or Company Admin)
            target_company = user.company

        if not target_company:
            # If no company can be determined, return no schedules.
            return Schedule.objects.none()

        # Find the active schedule for the target company.
        active_schedule = target_company.active_schedule
        if not active_schedule:
            # If the company has no specific schedule, find the active default schedule.
            active_schedule = Schedule.objects.filter(company__isnull=True, is_active=True).first()
            
        if active_schedule:
            # Return a queryset containing only the determined active schedule.
            return Schedule.objects.filter(pk=active_schedule.pk).select_related('company').prefetch_related(
                'daily_menus__available_foods',
                'daily_menus__available_sides'
            )
        
        # If no active schedule is found at all, return an empty queryset.
        return Schedule.objects.none()