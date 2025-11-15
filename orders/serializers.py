# back/orders/serializers.py
from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import Order
from schedules.models import DailyMenu
from menu.serializers import FoodItemSerializer, SideDishSerializer
from users.models import User 
from companies.models import Company

class OrderWriteSerializer(serializers.ModelSerializer):
    daily_menu = serializers.PrimaryKeyRelatedField(queryset=DailyMenu.objects.all())
    quantity = serializers.IntegerField(min_value=1, default=1, required=False)
    # [اصلاح کلیدی] فیلد کد تخفیف را اینجا اضافه می‌کنیم
    discount_code = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Order
        # [اصلاح کلیدی] فیلد جدید را به لیست اضافه می‌کنیم
        fields = ['id', 'daily_menu', 'food_item', 'side_dishes', 'quantity', 'discount_code']
        read_only_fields = ['id']
    
    def validate(self, data):
        # ... (منطق validate مثل قبل) ...
        return data

class OrderReadSerializer(serializers.ModelSerializer):
    food_item = FoodItemSerializer(read_only=True)
    side_dishes = SideDishSerializer(many=True, read_only=True)
    date = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'date', 'user', 'food_item', 'side_dishes',
            'status', 'company', 'created_at', 'quantity', 'final_price'
        ]

    def get_date(self, obj):
        return obj.daily_menu.date if obj.daily_menu else None

    def get_company(self, obj):
        if obj.user and obj.user.company:
            return obj.user.company.name
        return None

    def get_user(self, obj):
        if obj.user:
            return { 'id': obj.user.id, 'name': obj.user.get_full_name() or obj.user.username }
        return None

class AdminOrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']