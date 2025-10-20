from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FoodCategoryViewSet, FoodItemViewSet, SideDishViewSet

router = DefaultRouter()
router.register(r'categories', FoodCategoryViewSet)
router.register(r'items', FoodItemViewSet)
router.register(r'sides', SideDishViewSet)

urlpatterns = [
    path('', include(router.urls)),
]