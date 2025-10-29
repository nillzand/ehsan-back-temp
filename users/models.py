# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal

class User(AbstractUser):
    """
    Custom user model for the catering system.
    """

    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"        # Catering company admin
        COMPANY_ADMIN = "COMPANY_ADMIN", "Company Admin"  # Client company admin
        EMPLOYEE = "EMPLOYEE", "Employee"                 # Client company employee

    # Optional company reference for employees/admins
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )

    # User role
    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.EMPLOYEE
    )
    
    # User-specific meal budget
    budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="The current meal budget allocated to this user."
    )

    def __str__(self):
        return self.username
