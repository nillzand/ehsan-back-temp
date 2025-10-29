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
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = FoodItem
        fields = [
            'id', 'name', 'description', 'price', 'is_available',
            'image',
            'image_url',
            'category',
            'category_name',
            'created_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
            'is_available': {'required': False}
        }

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class SideDishSerializer(serializers.ModelSerializer):
    class Meta:
        model = SideDish
        # [FIX] حرف 's' اضافی از انتهای این خط حذف شد
        fields = ['id', 'name', 'description', 'price', 'is_available']