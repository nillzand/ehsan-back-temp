# ehsan-back-temp/menu/serializers.py

from rest_framework import serializers
from .models import FoodCategory, FoodItem, SideDish

class FoodCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCategory
        fields = ['id', 'name', 'description']

class FoodItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the FoodItem model.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    image = serializers.ImageField(write_only=True, required=False, allow_null=True)
    image_url = serializers.SerializerMethodField() # این خط باقی می‌ماند

    class Meta:
        model = FoodItem
        fields = [
            'id', 'name', 'description', 'price', 'is_available',
            'image',
            'image_url', # این فیلد مهم است
            'category',
            'category_name',
            'created_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
            'is_available': {'required': False}
        }

    # [اصلاح کلیدی] این متد آدرس کامل تصویر را با پروتکل صحیح تولید می‌کند
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            # build_absolute_uri به صورت هوشمند از http یا https استفاده می‌کند
            return request.build_absolute_uri(obj.image.url)
        return None

class SideDishSerializer(serializers.ModelSerializer):
    class Meta:
        model = SideDish
        fields = ['id', 'name', 'description', 'price', 'is_available']