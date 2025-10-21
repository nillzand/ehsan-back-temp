# menu/views.py
from rest_framework import viewsets
# [NEW] Import the necessary parsers for file uploads
from rest_framework.parsers import MultiPartParser, FormParser
from .models import FoodCategory, FoodItem, SideDish
from .serializers import FoodCategorySerializer, FoodItemSerializer, SideDishSerializer
from core.permissions import IsSuperAdminOrReadOnly

class FoodCategoryViewSet(viewsets.ModelViewSet):
    queryset = FoodCategory.objects.all()
    serializer_class = FoodCategorySerializer
    permission_classes = [IsSuperAdminOrReadOnly]

class FoodItemViewSet(viewsets.ModelViewSet):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    # [MODIFIED] Add parser classes to support image uploads
    parser_classes = [MultiPartParser, FormParser]

class SideDishViewSet(viewsets.ModelViewSet):
    queryset = SideDish.objects.all()
    serializer_class = SideDishSerializer
    permission_classes = [IsSuperAdminOrReadOnly]