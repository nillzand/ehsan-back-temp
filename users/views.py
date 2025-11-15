# back/users/views.py

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import User
from .serializers import UserSerializer
from core.permissions import CanManageUsers

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [CanManageUsers]
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=['get'], url_path='me', permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def get_queryset(self):
        """
        [FIX] This queryset is now completely safe.
        It avoids ordering by related fields that can be null.
        """
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            # Order by a simple, non-relational field on the User model itself.
            return User.objects.all().order_by('username')
        if user.role == User.Role.COMPANY_ADMIN:
            # This is safe because a COMPANY_ADMIN always has a company.
            return User.objects.filter(company=user.company).order_by('username')
        # For other roles like EMPLOYEE, return an empty queryset as they shouldn't list users.
        return User.objects.none()

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == User.Role.COMPANY_ADMIN:
            # Automatically assign the new user to the admin's company.
            serializer.save(company=user.company)
        else:
            serializer.save()