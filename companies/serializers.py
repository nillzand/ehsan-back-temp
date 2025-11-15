# back/companies/serializers.py

from rest_framework import serializers
from decimal import Decimal
from .models import Company, CompanyConfiguration

class CompanyConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyConfiguration
        exclude = ['id', 'company']

class CompanySerializer(serializers.ModelSerializer):
    config = CompanyConfigurationSerializer(required=False)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    wallet_balance = serializers.SerializerMethodField()
    # [اصلاح کلیدی] فیلد جدید را اینجا اضافه می‌کنیم
    active_schedule_is_default = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'contact_person', 'contact_phone', 'address',
            'national_id', 'notes',
            'status', 'status_display',
            'active_schedule', 'config', 'wallet_balance',
            'active_schedule_is_default', # اضافه کردن فیلد به لیست
            
            'calculation_type', 
            'average_price',
            'payment_model', 
            'invoice_schedule',
            'discount_type', 
            'discount_value', 
            'rounding_amount',
            'coordinator_name', 
            'coordinator_phone', 
            'registration_deadline_hours'
        ]

    def get_wallet_balance(self, obj):
        if hasattr(obj, 'wallet') and obj.wallet is not None:
            return obj.wallet.balance
        return Decimal('0.00')
        
    # [اصلاح کلیدی] منطق محاسبه فیلد جدید
    def get_active_schedule_is_default(self, obj):
        if obj.active_schedule:
            # اگر برنامه فعال شرکت، شرکتی نداشته باشد (company is None)، پس پیش‌فرض است.
            return obj.active_schedule.company is None
        # اگر اصلاً برنامه فعالی نداشته باشد، می‌توانیم آن را پیش‌فرض در نظر نگیریم.
        return False

    def update(self, instance, validated_data):
        config_data = validated_data.pop('config', None)
        instance = super().update(instance, validated_data)
        if config_data:
            CompanyConfiguration.objects.update_or_create(
                company=instance,
                defaults=config_data
            )
        return instance

    def create(self, validated_data):
        config_data = validated_data.pop('config', None)
        company = Company.objects.create(**validated_data)
        if config_data:
            CompanyConfiguration.objects.update_or_create(company=company, defaults=config_data)
        return company