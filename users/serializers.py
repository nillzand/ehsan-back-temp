# back/users/serializers.py (نسخه نهایی و کامل)

from rest_framework import serializers
from decimal import Decimal
from .models import User
from companies.models import Company
from companies.serializers import CompanyConfigurationSerializer 
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
    # --- Read-only fields (computed for display) ---
    name = serializers.SerializerMethodField(read_only=True)
    company_name = serializers.SerializerMethodField(read_only=True)
    company_config = serializers.SerializerMethodField(read_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)

    # --- Write-only fields (for creating/updating) ---
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    image = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        # All fields needed for both reading and writing are listed here.
        # The combination of read_only_fields and write_only=True on specific fields
        # tells DRF how to handle them.
        fields = [
            'id', 'username', 'password', 'first_name', 'last_name',
            'role', 'company', 'budget', 'image',
            # Read-only computed fields
            'name', 'company_name', 'company_config', 'image_url'
        ]
        
        # These fields are only used for reading, not for writing.
        read_only_fields = ('id', 'name', 'company_name', 'budget', 'company_config', 'image_url')
        
        # Make company optional for create/update
        extra_kwargs = {
            'company': {'required': False}
        }

    def get_name(self, obj):
        full_name = obj.get_full_name()
        return full_name if full_name else obj.username

    def get_company_name(self, obj):
        return obj.company.name if obj.company else None

    def get_company_config(self, obj):
        if obj.company and hasattr(obj.company, 'config') and obj.company.config is not None:
            return CompanyConfigurationSerializer(obj.company.config).data
        return None

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url') and request:
            return request.build_absolute_uri(obj.image.url)
        return f"https://i.pravatar.cc/150?u={obj.username}"

    # Handle create and update to correctly manage password
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_password("password123") # Default password if not provided
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        # Handle password update: only update if a non-empty password is provided
        if password:
            instance.set_password(password)
            
        # Update other fields
        instance = super().update(instance, validated_data)
        instance.save()
        return instance

# ... (بقیه سریالایزرها بدون تغییر)
class AllocateBudgetSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['role'] = user.role
        return token