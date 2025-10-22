# start of core/permissions.py
# core/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from users.models import User


def is_authenticated_user(user):
    """Helper to check if a user is authenticated."""
    return user and user.is_authenticated


class IsSuperAdmin(BasePermission):
    """
    Allows access only to users with the 'SUPER_ADMIN' role.
    """
    def has_permission(self, request, view):
        return is_authenticated_user(request.user) and request.user.role == User.Role.SUPER_ADMIN

class IsAdmin(BasePermission):
    """
    Allows access only to users with 'SUPER_ADMIN' or 'COMPANY_ADMIN' roles.
    """
    def has_permission(self, request, view):
        return is_authenticated_user(request.user) and request.user.role in [User.Role.SUPER_ADMIN, User.Role.COMPANY_ADMIN]


class IsCompanyAdmin(BasePermission):
    """
    Allows access only to users with the 'COMPANY_ADMIN' role.
    """
    def has_permission(self, request, view):
        return is_authenticated_user(request.user) and request.user.role == User.Role.COMPANY_ADMIN


class IsSuperAdminOrReadOnly(BasePermission):
    """
    Allows read-only access to any authenticated user,
    but write access (create, update, delete) only to Super Admins.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return is_authenticated_user(request.user)
        return is_authenticated_user(request.user) and request.user.role == User.Role.SUPER_ADMIN


class CanManageUsers(BasePermission):
    """
    Custom permission for the UserViewSet:
    - Super Admins can perform any action on any user.
    - Company Admins can manage users within their own company.
    """
    def has_permission(self, request, view):
        return is_authenticated_user(request.user) and request.user.role in [User.Role.SUPER_ADMIN, User.Role.COMPANY_ADMIN]

    def has_object_permission(self, request, view, obj):
        if not is_authenticated_user(request.user):
            return False

        if request.user.role == User.Role.SUPER_ADMIN:
            return True

        if request.user.role == User.Role.COMPANY_ADMIN:
            return obj.company == request.user.company

        return False


class IsCompanyAdminOfTargetUser(BasePermission):
    """
    Allows access only if the request user is a COMPANY_ADMIN
    and belongs to the same company as the target user specified in the URL.
    """
    def has_permission(self, request, view):
        if not (is_authenticated_user(request.user) and request.user.role == User.Role.COMPANY_ADMIN):
            return False

        target_user_id = view.kwargs.get('user_id')
        if not target_user_id:
            return False

        try:
            target_user = get_object_or_404(User, pk=int(target_user_id))
        except (ValueError, User.DoesNotExist):
            return False

        return request.user.company == target_user.company


class CanModifyOrder(BasePermission):
    """
    Allows modification or deletion of an order only if the reservation date
    is far enough in the future, based on RESERVATION_LEAD_DAYS.
    """
    message = f"Orders cannot be changed or canceled within {settings.RESERVATION_LEAD_DAYS} days of the delivery date."

    def has_object_permission(self, request, view, obj):
        # Read-only actions (GET, HEAD, OPTIONS) are always allowed.
        if request.method in SAFE_METHODS:
            return True

        # For write actions, check the date.
        today = timezone.now().date()
        days_until_reservation = (obj.daily_menu.date - today).days
        return days_until_reservation >= settings.RESERVATION_LEAD_DAYS
# end of core/permissions.py