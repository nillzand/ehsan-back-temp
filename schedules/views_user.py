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
        context = super().get_serializer_context()
        context['request'] = self.request
        user = self.request.user
        
        target_company = None
        
        print("\n" + "="*50) # LOG Separator
        print("[LOG | VIEW] -> get_serializer_context() called.")
        
        if user.role == User.Role.SUPER_ADMIN:
            company_id = self.request.query_params.get('company_id')
            print(f"[LOG | VIEW] Super Admin detected. Trying to get company_id from query params: {company_id}") # LOG
            if company_id:
                try:
                    target_company = Company.objects.get(pk=company_id)
                    print(f"[LOG | VIEW] Successfully fetched company object: {target_company.name}") # LOG
                except Company.DoesNotExist:
                    print(f"[LOG | VIEW] Company with id={company_id} NOT FOUND.") # LOG
                    pass
        elif user.company:
            target_company = user.company
            print(f"[LOG | VIEW] Employee/CompanyAdmin detected. Using user's own company: {target_company.name}") # LOG

        context['company_for_pricing'] = target_company
        print(f"[LOG | VIEW] Passing company to context: {'Object exists' if target_company else 'None'}") # LOG
        print("="*50 + "\n")
        
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
            return Schedule.objects.filter(pk=active_schedule.pk).select_related('company').prefetch_related(
                'daily_menus__available_foods',
                'daily_menus__available_sides'
            )
        
        return Schedule.objects.none()