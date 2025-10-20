# users/serializers.py

from rest_framework import serializers
from decimal import Decimal
from .models import User
from companies.models import Company


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model, designed for admin management.
    Handles password hashing on creation and update.
    Enforces business rules for Company Admins when assigning roles or companies.
    """
    # Read-only combined name field
    name = serializers.SerializerMethodField()
    # Read-only company name for display
    company_name = serializers.CharField(source='company.name', read_only=True)
    # Allows setting the company via its ID when creating/updating
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), required=False
    )
    # Password is write-only
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'name', 'first_name', 'last_name',
            'role', 'company', 'company_name', 'password'
        ]
        extra_kwargs = {
            'first_name': {'write_only': True},
            'last_name': {'write_only': True},
        }

    def get_name(self, obj):
        """Combine first and last name for display purposes."""
        return f"{obj.first_name} {obj.last_name}".strip()

    def validate(self, data):
        """
        Enforce business rules for Company Admins:
        1. Cannot assign a user to a different company.
        2. Cannot create/assign other Admins or Super Admins.
        """
        request_user = self.context['request'].user

        if request_user.role == User.Role.COMPANY_ADMIN:
            # Rule 1: Company Admin cannot manage users for other companies
            if 'company' in data and data['company'] != request_user.company:
                raise serializers.ValidationError(
                    "You do not have permission to manage users for another company."
                )

            # Rule 2: Company Admin can only assign Employee role
            if 'role' in data and data['role'] != User.Role.EMPLOYEE:
                raise serializers.ValidationError(
                    "You only have permission to create or assign the 'Employee' role."
                )

        return data

    def create(self, validated_data):
        """Create a user and hash their password securely."""
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        """Update user instance and handle password hashing if provided."""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class AllocateBudgetSerializer(serializers.Serializer):
    """
    Serializer for validating budget allocation input.
    """
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01')  # Ensures positive amounts with correct precision
    )


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# users/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['role'] = user.role
        return token
