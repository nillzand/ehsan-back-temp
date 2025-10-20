# orders/serializers.py

from rest_framework import serializers
from django.conf import settings
from django.utils import timezone
from .models import Order
from schedules.models import DailyMenu
from menu.serializers import FoodItemSerializer, SideDishSerializer


class OrderWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating orders.
    Includes:
    - Company ownership validation
    - Menu item availability checks
    - Duplicate order prevention
    - Budget validation
    - Reservation deadline enforcement
    """
    daily_menu = serializers.PrimaryKeyRelatedField(queryset=DailyMenu.objects.all())

    class Meta:
        model = Order
        fields = ['id', 'daily_menu', 'food_item', 'side_dishes']
        read_only_fields = ['id']

    def validate(self, data):
        daily_menu = data.get('daily_menu')
        food_item = data.get('food_item')
        side_dishes = data.get('side_dishes', [])
        user = self.context['request'].user

        # 1️⃣ Ensure the user belongs to the same company as the menu
        if user.company != daily_menu.schedule.company:
            raise serializers.ValidationError(
                "You can only order from your own company's menu."
            )

        # 2️⃣ Ensure the food item is available on that day's menu
        if food_item not in daily_menu.available_foods.all():
            raise serializers.ValidationError(
                f"'{food_item.name}' is not an available food item on {daily_menu.date}."
            )

        # 3️⃣ Ensure all selected side dishes are available
        for side in side_dishes:
            if side not in daily_menu.available_sides.all():
                raise serializers.ValidationError(
                    f"'{side.name}' is not an available side dish on {daily_menu.date}."
                )

        # 4️⃣ Prevent duplicate orders for the same day
        if not self.instance and Order.objects.filter(daily_menu=daily_menu, user=user).exists():
            raise serializers.ValidationError(
                "You have already placed an order for this day."
            )

        # 5️⃣ Enforce reservation deadline (new)
        today = timezone.now().date()
        reservation_date = daily_menu.date
        days_in_advance = (reservation_date - today).days

        if days_in_advance < settings.RESERVATION_LEAD_DAYS:
            raise serializers.ValidationError(
                f"Reservation failed. You must place your order at least "
                f"{settings.RESERVATION_LEAD_DAYS} full days in advance."
            )

        # 6️⃣ Check for sufficient budget
        food_price = food_item.price if food_item else 0
        sides_price = sum(side.price for side in side_dishes)
        total_cost = food_price + sides_price

        if user.budget < total_cost:
            raise serializers.ValidationError(
                f"Insufficient funds. Your budget is {user.budget}, but the order costs {total_cost}."
            )

        # Store the calculated total cost for use in the view (atomic budget deduction)
        self.context['total_cost'] = total_cost

        return data


class OrderReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading order details with nested related objects.
    """
    food_item = FoodItemSerializer(read_only=True)
    side_dishes = SideDishSerializer(many=True, read_only=True)
    date = serializers.DateField(source='daily_menu.date', read_only=True)
    company = serializers.CharField(source='daily_menu.schedule.company.name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'date',
            'food_item',
            'side_dishes',
            'status',
            'company',
            'created_at',
        ]
