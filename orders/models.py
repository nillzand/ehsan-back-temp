# back/orders/models.py
from django.db import models
from django.conf import settings
from decimal import Decimal
from companies.models import Company
from discounts.models import DiscountCode

class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PLACED = "PLACED", "ثبت شده"
        CONFIRMED = "CONFIRMED", "تایید شده"
        PREPARING = "PREPARING", "در حال آماده‌سازی"
        DELIVERED = "DELIVERED", "تحویل داده شده"
        CANCELED = "CANCELED", "لغو شده"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    daily_menu = models.ForeignKey('schedules.DailyMenu', on_delete=models.SET_NULL, null=True, related_name='orders')
    food_item = models.ForeignKey('menu.FoodItem', on_delete=models.SET_NULL, null=True, related_name='orders')
    side_dishes = models.ManyToManyField('menu.SideDish', related_name='orders', blank=True)
    
    quantity = models.PositiveIntegerField(default=1, verbose_name="تعداد")

    status = models.CharField(max_length=50, choices=OrderStatus.choices, default=OrderStatus.PLACED)
    
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="قیمت پایه")
    company_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="تخفیف شرکت")
    coupon_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="تخفیف کد")
    final_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="قیمت نهایی")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_and_save_prices(self):
        if not self.food_item:
            return

        from schedules.serializers import _apply_company_pricing

        food_price = self.food_item.price
        sides_price = sum(side.price for side in self.side_dishes.all())
        
        self.base_price = (food_price + sides_price) * self.quantity

        company = self.user.company
        price_after_company_discount = self.base_price
        if company:
            final_food_price = _apply_company_pricing(food_price, company)
            final_sides_price = sum(_apply_company_pricing(side.price, company) for side in self.side_dishes.all())
            price_after_company_discount = (final_food_price + final_sides_price) * self.quantity
        
        self.company_discount_amount = self.base_price - price_after_company_discount
        
        self.coupon_discount_amount = Decimal('0.00')
        if hasattr(self, 'discount_usage') and self.discount_usage:
            discount_code = self.discount_usage.discount_code
            self.coupon_discount_amount = discount_code.calculate_discount_amount(price_after_company_discount)

        self.final_price = price_after_company_discount - self.coupon_discount_amount
        self.save()

    def __str__(self):
        return f"سفارش #{self.id} ({self.quantity} عدد) برای {self.user.username}"