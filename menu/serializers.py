# back/menu/serializers.py
from rest_framework import serializers
from .models import FoodCategory, FoodItem, SideDish

class FoodCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCategory
        fields = ['id', 'name', 'description']

class FoodItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the FoodItem model.
    [FINAL FIX] The 'write_only' constraint on 'category' has been removed to fix PATCH updates.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    image = serializers.ImageField(required=False, allow_null=True, use_url=True)

    class Meta:
        model = FoodItem
        fields = [
            'id', 'name', 'description', 'price', 'image', 'is_available',
            'category', 'category_name', 'created_at'
        ]
        # [MODIFIED] The problematic 'write_only' setting for the category is REMOVED.
        # This allows the serializer to correctly handle both POST and PATCH requests for the category field.
        extra_kwargs = {
            'created_at': {'read_only': True},
        }

class SideDishSerializer(serializers.ModelSerializer):
    class Meta:
        model = SideDish
        fields = ['id', 'name', 'description', 'price', 'is_available']