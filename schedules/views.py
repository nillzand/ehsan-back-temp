# backend/schedules/views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Schedule, DailyMenu
from .serializers import (
    ScheduleSerializer,
    DailyMenuReadSerializer,
    DailyMenuWriteSerializer,
)
from core.permissions import IsSuperAdminOrReadOnly
# [NEW] Import DjangoFilterBackend
from django_filters.rest_framework import DjangoFilterBackend


class ScheduleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing schedules.
    Only admins can create or modify schedules.
    """
    queryset = Schedule.objects.prefetch_related(
        'daily_menus__available_foods',
        'daily_menus__available_sides'
    ).select_related('company').all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsSuperAdminOrReadOnly]


class DailyMenuViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing daily menus within a specific schedule.
    Accessed via a nested route: /api/schedules/<schedule_pk>/daily_menus/
    """
    permission_classes = [IsSuperAdminOrReadOnly]
    # [NEW] Add filtering capabilities
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date'] # Allows filtering by ?date=YYYY-MM-DD

    def get_queryset(self):
        """
        Return only daily menus belonging to the schedule in the URL.
        """
        schedule_pk = self.kwargs['schedule_pk']
        return DailyMenu.objects.filter(schedule_id=schedule_pk)

    def get_serializer_class(self):
        """
        Use write serializer for POST/PUT/PATCH, read serializer for GET.
        """
        if self.action in ['create', 'update', 'partial_update']:
            return DailyMenuWriteSerializer
        return DailyMenuReadSerializer

    def get_serializer_context(self):
        """
        Pass the schedule object to the serializer for validation.
        """
        context = super().get_serializer_context()
        context['schedule'] = get_object_or_404(Schedule, pk=self.kwargs['schedule_pk'])
        return context

    def perform_create(self, serializer):
        """
        Automatically associate the daily menu with the schedule from the URL.
        """
        schedule = get_object_or_404(Schedule, pk=self.kwargs['schedule_pk'])
        serializer.save(schedule=schedule)

    def create(self, request, *args, **kwargs):
        """
        Override the default create method to:
        - Add the 'X-Warning' header if the created menu date is less than 7 days away.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Prepare the response
        headers = self.get_success_headers(serializer.data)
        response = Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        # Add a custom warning header if the menu date is less than a week away
        menu_date = serializer.instance.date
        today = timezone.now().date()
        if (menu_date - today).days < 7:
            response['X-Warning'] = "Menu created for a date that is less than one week away."

        return response