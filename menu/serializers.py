# back/menu/serializers.py
from rest_framework import serializers
from .models import FoodCategory, FoodItem, SideDish
from django.utils import timezone
from decimal import Decimal
from django.db import models

class FoodCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCategory
        fields = ['id', 'name', 'description']

class FoodItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    image = serializers.ImageField(write_only=True, required=False, allow_null=True)
    image_url = serializers.SerializerMethodField()
    
    discount_percentage = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = FoodItem
        fields = [
            'id', 'name', 'description', 'price', 'is_available',
            'image', 'image_url', 'category', 'category_name', 'created_at',
            'discount_percentage', 'discounted_price'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
            'is_available': {'required': False}
        }

    def get_image_url(self, obj):
        # [دیباگ] شروع فرآیند ساخت URL برای تصویر
        print(f"\n--- [DEBUG] Processing image for FoodItem ID: {obj.id} ({obj.name}) ---")
        
        request = self.context.get('request')
        
        # [دیباگ] بررسی وجود آبجکت تصویر و درخواست
        if not obj.image:
            print("[DEBUG] -> obj.image is None. No image file is associated with this item in the database.")
            return None
        
        print(f"[DEBUG] -> obj.image exists. Value: {obj.image}")
        print(f"[DEBUG] -> obj.image.url: {obj.image.url}")

        if not request:
            print("[DEBUG] -> 'request' is NOT in serializer context. Cannot build absolute URL.")
            return obj.image.url # بازگرداندن URL نسبی

        # ساخت URL کامل
        absolute_url = request.build_absolute_uri(obj.image.url)
        print(f"[DEBUG] -> Final absolute URL generated: {absolute_url}")
        print("--- [END DEBUG] ---")
        
        return absolute_url

    def _get_active_discount(self, obj):
        now = timezone.now()
        discount = obj.dynamic_discounts.filter(
            is_active=True,
            start_date__lte=now,
        ).filter(
            models.Q(end_date__gte=now) | models.Q(end_date__isnull=True)
        ).first()
        return discount

    def get_discount_percentage(self, obj):
        discount = self._get_active_discount(obj)
        return discount.discount_percentage if discount else None

    def get_discounted_price(self, obj):
        discount = self._get_active_discount(obj)
        if not discount:
            return obj.price

        discount_amount = (obj.price * discount.discount_percentage) / Decimal('100')
        if discount.max_discount_per_item and discount_amount > discount.max_discount_per_item:
            discount_amount = discount.max_discount_per_item
        
        return obj.price - discount_amount

class SideDishSerializer(serializers.ModelSerializer):
    class Meta:
        model = SideDish
        fields = ['id', 'name', 'description', 'price', 'is_available']