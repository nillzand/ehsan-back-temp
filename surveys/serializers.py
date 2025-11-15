from rest_framework import serializers
from .models import Survey
from orders.models import Order

class SurveySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Survey
        fields = [
            'id', 'order', 'user', 'user_name', 
            'rating', 'comment', 'created_at'
        ]
        read_only_fields = ['user', 'user_name', 'created_at']

    def validate_order(self, order):
        """
        بررسی می‌کند که آیا کاربر مجاز به ثبت نظر برای این سفارش است یا خیر.
        """
        request = self.context.get('request')
        # کاربر فقط می‌تواند برای سفارش‌های خودش نظر ثبت کند
        if not request or order.user != request.user:
            raise serializers.ValidationError("شما فقط می‌توانید برای سفارش‌های خودتان نظر ثبت کنید.")
        
        # کاربر فقط برای سفارش‌های تحویل داده شده می‌تواند نظر ثبت کند
        if order.status != Order.OrderStatus.DELIVERED:
            raise serializers.ValidationError("شما فقط می‌توانید برای سفارش‌هایی که تحویل داده شده‌اند نظر ثبت کنید.")
        
        # بررسی می‌کند که آیا قبلاً برای این سفارش نظری ثبت شده یا نه
        if hasattr(order, 'survey'):
            raise serializers.ValidationError("برای این سفارش قبلاً نظرسنجی ثبت شده است.")

        return order