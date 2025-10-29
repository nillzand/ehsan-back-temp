from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from users.models import User


def is_authenticated_user(user):
    """تابع کمکی برای بررسی اینکه آیا کاربر احراز هویت شده است یا خیر."""
    return user and user.is_authenticated


class IsSuperAdmin(BasePermission):
    """
    سطح دسترسی را فقط به کاربرانی با نقش 'SUPER_ADMIN' محدود می‌کند.
    """
    def has_permission(self, request, view):
        return is_authenticated_user(request.user) and request.user.role == User.Role.SUPER_ADMIN

class IsAdmin(BasePermission):
    """
    سطح دسترسی را به کاربرانی با نقش 'SUPER_ADMIN' یا 'COMPANY_ADMIN' محدود می‌کند.
    """
    def has_permission(self, request, view):
        return is_authenticated_user(request.user) and request.user.role in [User.Role.SUPER_ADMIN, User.Role.COMPANY_ADMIN]


class IsCompanyAdmin(BasePermission):
    """
    سطح دسترسی را فقط به کاربرانی با نقش 'COMPANY_ADMIN' محدود می‌کند.
    """
    def has_permission(self, request, view):
        return is_authenticated_user(request.user) and request.user.role == User.Role.COMPANY_ADMIN


class IsSuperAdminOrReadOnly(BasePermission):
    """
    به کاربران احراز هویت شده اجازه دسترسی فقط خواندنی (GET) می‌دهد،
    اما دسترسی برای نوشتن (POST, PUT, DELETE) را فقط به ادمین کل محدود می‌کند.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return is_authenticated_user(request.user)
        return is_authenticated_user(request.user) and request.user.role == User.Role.SUPER_ADMIN


class CanManageUsers(BasePermission):
    """
    سطح دسترسی سفارشی برای مدیریت کاربران:
    - ادمین کل می‌تواند هر عملیاتی روی هر کاربری انجام دهد.
    - ادمین شرکت فقط می‌تواند کاربران شرکت خودش را مدیریت کند.
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
    دسترسی را فقط در صورتی مجاز می‌داند که کاربر درخواست‌دهنده یک COMPANY_ADMIN باشد
    و به همان شرکتی تعلق داشته باشد که کاربر هدف (مشخص شده در URL) به آن تعلق دارد.
    """
    def has_permission(self, request, view):
        # اطمینان از اینکه کاربر لاگین کرده و ادمین شرکت است
        if not (is_authenticated_user(request.user) and request.user.role == User.Role.COMPANY_ADMIN):
            return False

        # گرفتن آی‌دی کاربری که قرار است عملیاتی روی آن انجام شود از URL
        target_user_id = view.kwargs.get('user_id')
        if not target_user_id:
            return False

        try:
            # پیدا کردن کاربر هدف در دیتابیس
            target_user = get_object_or_404(User, pk=int(target_user_id))
        except (ValueError, User.DoesNotExist):
            return False

        # بررسی اینکه آیا شرکت ادمین با شرکت کارمند هدف یکی است یا خیر
        return request.user.company == target_user.company


class CanModifyOrder(BasePermission):
    """
    اجازه تغییر یا حذف یک سفارش را فقط در صورتی می‌دهد که تاریخ سفارش
    به اندازه کافی در آینده باشد (بر اساس تنظیمات RESERVATION_LEAD_DAYS).
    """
    message = f"سفارش‌ها را نمی‌توان در فاصله کمتر از {settings.RESERVATION_LEAD_DAYS} روز تا تاریخ تحویل، تغییر داد یا لغو کرد."

    def has_object_permission(self, request, view, obj):
        # عملیات فقط خواندنی (GET, HEAD, OPTIONS) همیشه مجاز است.
        if request.method in SAFE_METHODS:
            return True

        # برای عملیات نوشتن، تاریخ را بررسی کن.
        today = timezone.now().date()
        days_until_reservation = (obj.daily_menu.date - today).days
        return days_until_reservation >= settings.RESERVATION_LEAD_DAYS