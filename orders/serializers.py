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
    discount_code = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Order
        fields = ['id', 'daily_menu', 'food_item', 'side_dishes', 'quantity', 'discount_code']
        read_only_fields = ['id']
    
    def validate(self, data):
        """
        [اصلاح کلیدی] منطق اعتبارسنجی که حذف شده بود، در اینجا کامل می‌شود.
        """
        daily_menu = data['daily_menu']
        food_item = data['food_item']
        side_dishes = data.get('side_dishes', [])
        user = self.context['request'].user

        # بررسی اینکه آیا کاربر به منوی این شرکت دسترسی دارد یا خیر
        schedule_company = daily_menu.schedule.company
        if schedule_company is not None and user.company != schedule_company:
            raise serializers.ValidationError("You can only order from your own company's menu.")

        # بررسی اینکه آیا غذای انتخاب شده در منوی آن روز موجود است یا خیر
        if food_item not in daily_menu.available_foods.all():
            raise serializers.ValidationError(f"Food item '{food_item.name}' is not available on this date.")

        # بررسی اینکه آیا کنارغذاهای انتخاب شده در منوی آن روز موجود هستند یا خیر
        for side in side_dishes:
            if side not in daily_menu.available_sides.all():
                raise serializers.ValidationError(f"Side dish '{side.name}' is not available on this date.")
        
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