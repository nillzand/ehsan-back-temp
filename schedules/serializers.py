from rest_framework import serializers
from .models import Schedule, DailyMenu
from menu.serializers import FoodItemSerializer, SideDishSerializer

# --- Serializers for DailyMenu ---

class DailyMenuWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating DailyMenu instances."""
    class Meta:
        model = DailyMenu
        fields = ['id', 'date', 'available_foods', 'available_sides']

    def validate_date(self, value):
        # Context is passed from the view to access the schedule
        schedule = self.context.get('schedule')
        if not (schedule.start_date <= value <= schedule.end_date):
            raise serializers.ValidationError(
                "Date must be within the parent schedule's date range."
            )
        return value

class DailyMenuReadSerializer(serializers.ModelSerializer):
    """Serializer for reading DailyMenu instances with nested food details."""
    available_foods = FoodItemSerializer(many=True, read_only=True)
    available_sides = SideDishSerializer(many=True, read_only=True)

    class Meta:
        model = DailyMenu
        fields = ['id', 'date', 'available_foods', 'available_sides']


# --- Serializer for Schedule ---

class ScheduleSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True, allow_null=True)
    daily_menus = DailyMenuReadSerializer(many=True, read_only=True)

    class Meta:
        model = Schedule
        fields = [
            'id', 'name', 'company', 'company_name', 'start_date', 'end_date', 'is_active', 'daily_menus'
        ]
         extra_kwargs = {
            'company': {'required': False, 'allow_null': True, 'write_only': True}
        }