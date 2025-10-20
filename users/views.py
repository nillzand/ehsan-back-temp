# backend/users/views.py

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserSerializer
from core.permissions import CanManageUsers

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for user management.
    - Super Admins can view and edit all users.
    - Company Admins can view and edit users only within their own company.
    """
    serializer_class = UserSerializer
    permission_classes = [CanManageUsers]

    @action(detail=False, methods=['get'], url_path='me', permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Return the information for the currently authenticated user.
        """
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def get_queryset(self):
        """
        Dynamically filter the queryset based on the request user's role.
        """
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return User.objects.all().order_by('company__name', 'last_name')
        
        if user.role == User.Role.COMPANY_ADMIN:
            return User.objects.filter(company=user.company).order_by('last_name')
        
        return User.objects.none()

    def get_serializer_context(self):
        """
        Pass the request object to the serializer context.
        """
        return {'request': self.request}

    def perform_create(self, serializer):
        """
        When a Company Admin creates a user, automatically assign that user
        to the admin's own company.
        """
        user = self.request.user
        if user.role == User.Role.COMPANY_ADMIN:
            serializer.save(company=user.company)
        else:
            serializer.save()

# Note: The MyTokenObtainPairView and its imports have been removed from this file.