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
    [MODIFIED] The image field is now explicitly optional to allow for PATCH updates without a new file.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    # [MODIFIED] Make the image field optional for updates.
    # This allows PATCH requests to modify other fields without needing to re-upload the image.
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = FoodItem
        fields = [
            'id', 'name', 'description', 'price', 'image', 'is_available',
            'category', 'category_name', 'created_at'
        ]
        # 'category' is write-only, 'category_name' is read-only
        extra_kwargs = {
            'category': {'write_only': True},
            # Make these fields read-only as they are set automatically
            'created_at': {'read_only': True},
        }

class SideDishSerializer(serializers.ModelSerializer):
    class Meta:
        model = SideDish
        fields = ['id', 'name', 'description', 'price', 'is_available']