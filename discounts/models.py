# back/discounts/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class DiscountCode(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'PERCENTAGE', 'درصدی'
        FIXED_AMOUNT = 'FIXED_AMOUNT', 'مبلغ ثابت'

    class ScopeType(models.TextChoices):
        PUBLIC = 'PUBLIC', 'عمومی'
        PRIVATE = 'PRIVATE', 'خصوصی'

    code = models.CharField(max_length=50, unique=True, verbose_name="کد تخفیف")
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices, verbose_name="نوع تخفیف")
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="مقدار تخفیف")
    
    max_usage_count = models.PositiveIntegerField(null=True, blank=True, verbose_name="حداکثر تعداد استفاده")
    usage_count = models.PositiveIntegerField(default=0, verbose_name="تعداد استفاده شده")
    max_usage_per_user = models.PositiveIntegerField(default=1, verbose_name="حداکثر استفاده برای هر کاربر")

    min_order_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="حداقل مبلغ سفارش")
    max_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="حداکثر مبلغ تخفیف")

    start_date = models.DateTimeField(verbose_name="تاریخ شروع")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ انقضا")
    
    scope = models.CharField(max_length=20, choices=ScopeType.choices, default=ScopeType.PUBLIC, verbose_name="نوع")
    is_active = models.BooleanField(default=True, verbose_name="وضعیت فعال")
    description = models.TextField(blank=True, verbose_name="توضیحات")

    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_discount_amount(self, price: Decimal) -> Decimal:
        """مقدار تخفیف را برای یک قیمت مشخص محاسبه می‌کند."""
        discount_amount = Decimal('0.00')
        if self.discount_type == self.DiscountType.FIXED_AMOUNT:
            discount_amount = self.value
        elif self.discount_type == self.DiscountType.PERCENTAGE:
            discount_amount = (price * self.value) / Decimal('100')

        if self.max_discount_amount and discount_amount > self.max_discount_amount:
            discount_amount = self.max_discount_amount
        
        return min(price, discount_amount)

    def __str__(self):
        return self.code

class DiscountCodeUsage(models.Model):
    discount_code = models.ForeignKey(DiscountCode, related_name='usages', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='discount_usages', on_delete=models.CASCADE)
    order = models.OneToOneField('orders.Order', related_name='discount_usage', on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('discount_code', 'user', 'order')

class DynamicMenuDiscount(models.Model):
    name = models.CharField(max_length=255, verbose_name="نام تخفیف")
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('100.00'))],
        verbose_name="درصد تخفیف"
    )
    max_discount_per_item = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="حداکثر تخفیف برای هر آیتم")
    
    start_date = models.DateTimeField(verbose_name="تاریخ شروع")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ انقضا")

    is_active = models.BooleanField(default=True, verbose_name="وضعیت فعال")
    show_on_menu = models.BooleanField(default=False, verbose_name="نمایش در منو")
    
    applicable_items = models.ManyToManyField('menu.FoodItem', blank=True, related_name='dynamic_discounts', verbose_name="آیتم‌های مشمول")
    applicable_companies = models.ManyToManyField('companies.Company', blank=True, related_name='dynamic_discounts', verbose_name="شرکت‌های مشمول")

    description = models.TextField(blank=True, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name