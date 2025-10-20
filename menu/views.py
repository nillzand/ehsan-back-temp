# menu/views.py
from rest_framework import viewsets
from .models import FoodCategory, FoodItem, SideDish
from .serializers import FoodCategorySerializer, FoodItemSerializer, SideDishSerializer
# [MODIFIED] Use the new, clearly named permission class.
from core.permissions import IsSuperAdminOrReadOnly

class FoodCategoryViewSet(viewsets.ModelViewSet):
    queryset = FoodCategory.objects.all()
    serializer_class = FoodCategorySerializer
    # [FIXED] Permissions are now consistent and clear.
    permission_classes = [IsSuperAdminOrReadOnly]

class FoodItemViewSet(viewsets.ModelViewSet):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer
    # [FIXED] Permissions are now consistent and clear.
    permission_classes = [IsSuperAdminOrReadOnly]

class SideDishViewSet(viewsets.ModelViewSet):
    queryset = SideDish.objects.all()
    serializer_class = SideDishSerializer
    # [FIXED] Permissions are now consistent and clear.
    permission_classes = [IsSuperAdminOrReadOnly]