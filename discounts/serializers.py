# discounts/serializers.py
from rest_framework import serializers
from .models import DiscountCode, DynamicMenuDiscount, DiscountCodeUsage
from orders.serializers import OrderReadSerializer
from users.serializers import UserSerializer # برای نمایش اطلاعات کاربر

class DiscountCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountCode
        fields = '__all__'

class DynamicMenuDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicMenuDiscount
        fields = '__all__'

class DiscountCodeUsageSerializer(serializers.ModelSerializer):
    # از سریالایزر خواندنی سفارش استفاده می‌کنیم تا جزئیات کامل نمایش داده شود
    order = OrderReadSerializer(read_only=True) 
    # آبجکت کامل کاربر را برای نمایش بهتر اضافه می‌کنیم
    user = UserSerializer(read_only=True) 

    class Meta:
        model = DiscountCodeUsage
        # فیلد user را به جای user_name قرار می‌دهیم تا آبجکت کامل کاربر ارسال شود
        fields = ['id', 'user', 'order', 'used_at']