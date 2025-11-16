# back/menu/serializers.py (نسخه نهایی و پاک‌سازی شده)

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
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url') and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def _get_active_discount(self, obj):
        now = timezone.now()
        # به دلیل prefetch، این بخش دیگر به دیتابیس درخواست نمی‌زند
        for discount in obj.dynamic_discounts.all():
            if (discount.is_active and 
                discount.start_date <= now and 
                (discount.end_date is None or discount.end_date >= now)):
                return discount
        return None

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