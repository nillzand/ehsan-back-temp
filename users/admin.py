from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Add custom fields to the admin display
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role', 'company')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Info', {'fields': ('role', 'company')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Info', {'fields': ('role', 'company')}),
    )