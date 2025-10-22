# back/menu/serializers.py
from rest_framework import serializers
from .models import FoodCategory, FoodItem, SideDish

class FoodCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the FoodCategory model.
    """
    class Meta:
        model = FoodCategory
        fields = ['id', 'name', 'description']

class FoodItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the FoodItem model.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    image = serializers.ImageField(required=False, allow_null=True, use_url=True)

    class Meta:
        model = FoodItem
        fields = [
            'id', 'name', 'description', 'price', 'image', 'is_available',
            'category', 'category_name', 'created_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
        }

class SideDishSerializer(serializers.ModelSerializer):
    """
    Serializer for the SideDish model.
    """
    class Meta:
        model = SideDish
        fields = ['id', 'name', 'description', 'price', 'is_available']