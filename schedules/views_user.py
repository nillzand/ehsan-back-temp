from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import Schedule
from .serializers import ScheduleSerializer
from django.utils import timezone

class MyCompanyMenuView(generics.ListAPIView):
    """
    A read-only endpoint that returns the active schedule(s)
    for the currently authenticated user's company.
    """
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.company:
            return Schedule.objects.none() # Return empty if user has no company

        today = timezone.now().date()
        
        # Find active schedules for the user's company that are currently ongoing
        queryset = Schedule.objects.filter(
            company=user.company,
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        ).prefetch_related(
            'daily_menus__available_foods',
            'daily_menus__available_sides'
        )
        return queryset