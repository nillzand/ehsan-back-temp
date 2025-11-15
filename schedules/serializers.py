# back/schedules/serializers.py
from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP

from .models import Schedule, DailyMenu
from menu.serializers import FoodItemSerializer, SideDishSerializer
from companies.models import Company
from users.models import User

def _apply_company_pricing(original_price: Decimal, company: Company | None) -> Decimal:
    if not company:
        # اگر شرکتی وجود نداشت، قیمت اصلی را بدون اعشار برمی‌گردانیم
        return original_price.quantize(Decimal('1'))

    if company.calculation_type == Company.CalculationType.AVERAGE and company.average_price > 0:
        base_price = company.average_price
    else:
        base_price = original_price
        
    final_price = base_price
    
    # اعمال تخفیف شرکت
    if company.discount_type != Company.DiscountType.NONE and company.discount_value > 0:
        discount_value = company.discount_value
        if company.discount_type == Company.DiscountType.FIXED:
            final_price = max(Decimal('0.00'), base_price - discount_value)
        elif company.discount_type == Company.DiscountType.PERCENTAGE:
            discount_multiplier = Decimal('1') - (discount_value / Decimal('100'))
            final_price = base_price * discount_multiplier

    # اعمال منطق رند کردن فقط برای تخفیف درصدی
    if company.discount_type == Company.DiscountType.PERCENTAGE and company.rounding_amount != Company.RoundingAmount.NONE:
        rounding_map = {
            'HUNDRED': Decimal('100'),
            'FIVE_HUNDRED': Decimal('500'),
            'THOUSAND': Decimal('1000'),
        }
        # اگر هر نوع رند کردنی انتخاب شده بود، همیشه به نزدیک‌ترین ۱۰۰۰ رند می‌کنیم
        rounding_base = Decimal('1000')
        final_price = (final_price / rounding_base).to_integral_value(rounding=ROUND_HALF_UP) * rounding_base

    # [اصلاح کلیدی] اطمینان از اینکه خروجی همیشه یک عدد صحیح و بدون اعشار است
    return final_price.quantize(Decimal('1'))


class DailyMenuWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyMenu
        fields = ['id', 'date', 'available_foods', 'available_sides']
    def validate_date(self, value):
        schedule = self.context.get('schedule')
        if schedule and not (schedule.start_date <= value <= schedule.end_date):
            raise serializers.ValidationError("Date must be within the parent schedule's date range.")
        return value

class DailyMenuReadSerializer(serializers.ModelSerializer):
    available_foods = serializers.SerializerMethodField()
    available_sides = SideDishSerializer(many=True, read_only=True)

    class Meta:
        model = DailyMenu
        fields = ['id', 'date', 'available_foods', 'available_sides']

    def get_available_foods(self, obj: DailyMenu):
        company_for_pricing = self.context.get('company_for_pricing')
        
        user = self.context.get('request').user
        if user and user.role == User.Role.SUPER_ADMIN:
            company_for_pricing = obj.schedule.company

        foods = obj.available_foods.all()
        processed_food_data = []

        for food in foods:
            serialized_food = FoodItemSerializer(food, context=self.context).data
            
            true_original_price = food.price
            price_after_dynamic_discount = Decimal(serialized_food['discounted_price'])
            
            final_price = _apply_company_pricing(price_after_dynamic_discount, company_for_pricing)
            
            serialized_food['price'] = f"{true_original_price:.2f}"
            serialized_food['discounted_price'] = f"{final_price:.2f}"
            
            processed_food_data.append(serialized_food)

        return processed_food_data


class ScheduleSerializer(serializers.ModelSerializer):
    company_name = serializers.SerializerMethodField()
    daily_menus = DailyMenuReadSerializer(many=True, read_only=True)

    class Meta:
        model = Schedule
        fields = ['id', 'name', 'company', 'company_name', 'start_date', 'end_date', 'is_active', 'daily_menus']
        extra_kwargs = {'company': {'required': False, 'allow_null': True}}

    def get_company_name(self, obj: Schedule):
        return obj.company.name if obj.company else None