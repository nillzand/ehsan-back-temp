# back/schedules/serializers.py (نسخه نهایی و بازبینی شده)

from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP

from .models import Schedule, DailyMenu
from menu.serializers import FoodItemSerializer, SideDishSerializer
from companies.models import Company
from users.models import User

# ... تابع _apply_company_pricing بدون تغییر باقی می‌ماند ...
def _apply_company_pricing(original_price: Decimal, company: Company | None) -> Decimal:
    if not company:
        return original_price.quantize(Decimal('1'))

    if company.calculation_type == Company.CalculationType.AVERAGE and company.average_price > 0:
        base_price = company.average_price
    else:
        base_price = original_price
        
    final_price = base_price
    
    if company.discount_type != Company.DiscountType.NONE and company.discount_value > 0:
        discount_value = company.discount_value
        if company.discount_type == Company.DiscountType.FIXED:
            final_price = max(Decimal('0.00'), base_price - discount_value)
        elif company.discount_type == Company.DiscountType.PERCENTAGE:
            discount_multiplier = Decimal('1') - (discount_value / Decimal('100'))
            final_price = base_price * discount_multiplier

    if company.discount_type == Company.DiscountType.PERCENTAGE and company.rounding_amount != Company.RoundingAmount.NONE:
        rounding_base = Decimal('1000')
        final_price = (final_price / rounding_base).to_integral_value(rounding=ROUND_HALF_UP) * rounding_base

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
    # --- [اصلاح ۱] --- available_foods را به یک سریالایزر مستقیم تغییر می‌دهیم
    # این کار انتقال context را خودکار می‌کند و از خطای انسانی جلوگیری می‌کند.
    available_foods = FoodItemSerializer(many=True, read_only=True)
    available_sides = SideDishSerializer(many=True, read_only=True)

    class Meta:
        model = DailyMenu
        fields = ['id', 'date', 'available_foods', 'available_sides']
        
    # --- [اصلاح ۲] --- منطق قیمت‌گذاری را به to_representation منتقل می‌کنیم
    # این متد در انتهای فرآیند سریالایز اجرا می‌شود و به ما اجازه می‌دهد قیمت‌ها را دستکاری کنیم.
    def to_representation(self, instance):
        # ابتدا داده‌های استاندارد را با context صحیح دریافت می‌کنیم
        data = super().to_representation(instance)
        
        company_for_pricing = self.context.get('company_for_pricing')
        user = self.context.get('request').user
        if user and user.role == User.Role.SUPER_ADMIN:
            company_for_pricing = instance.schedule.company

        # حالا قیمت‌ها را در داده‌های سریالایز شده تغییر می‌دهیم
        for food_data in data.get('available_foods', []):
            original_price = Decimal(food_data['price'])
            # قیمت با تخفیف داینامیک از قبل در discounted_price محاسبه شده
            price_after_dynamic_discount = Decimal(food_data['discounted_price'])
            
            # قیمت نهایی را با توجه به تنظیمات شرکت محاسبه می‌کنیم
            final_price = _apply_company_pricing(price_after_dynamic_discount, company_for_pricing)
            
            # قیمت‌ها را در خروجی نهایی بازنویسی می‌کنیم
            food_data['price'] = f"{original_price:.2f}" # قیمت اصلی برای نمایش (مثلاً خط خورده)
            food_data['discounted_price'] = f"{final_price:.2f}" # قیمت نهایی برای نمایش به کاربر
            
        return data


class ScheduleSerializer(serializers.ModelSerializer):
    company_name = serializers.SerializerMethodField()
    # --- [اصلاح ۳] --- از سریالایزر مستقیم استفاده می‌کنیم تا context به صورت خودکار منتقل شود.
    daily_menus = DailyMenuReadSerializer(many=True, read_only=True)

    class Meta:
        model = Schedule
        fields = ['id', 'name', 'company', 'company_name', 'start_date', 'end_date', 'is_active', 'daily_menus']
        extra_kwargs = {'company': {'required': False, 'allow_null': True}}

    def get_company_name(self, obj: Schedule):
        return obj.company.name if obj.company else None