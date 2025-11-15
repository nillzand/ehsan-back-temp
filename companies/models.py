# back/companies/models.py

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

class Company(models.Model):
    class CompanyStatus(models.TextChoices):
        PUBLISHED = "PUBLISHED", "منتشر شده"
        DRAFT = "DRAFT", "پیش نویس"

    class PaymentModel(models.TextChoices):
        ONLINE = "ONLINE", "آنلاین"
        INVOICE = "INVOICE", "ارسال فاکتور"

    class InvoiceSchedule(models.TextChoices):
        WEEKLY = "WEEKLY", "هفتگی"
        BIWEEKLY = "BIWEEKLY", "دو هفتگی"
        MONTHLY = "MONTHLY", "ماهانه"
    
    class DiscountType(models.TextChoices):
        NONE = "NONE", "بدون تخفیف"
        PERCENTAGE = "PERCENTAGE", "درصدی"
        FIXED = "FIXED", "مبلغ ثابت"

    class RoundingAmount(models.TextChoices):
        NONE = "NONE", "بدون رند کردن"
        HUNDRED = "HUNDRED", "نزدیک‌ترین ۱۰۰"
        FIVE_HUNDRED = "FIVE_HUNDRED", "نزدیک‌ترین ۵۰۰"
        THOUSAND = "THOUSAND", "نزدیک‌ترین ۱۰۰۰"
        
    class CalculationType(models.TextChoices):
        FLUID = "FLUID", "سیال"
        AVERAGE = "AVERAGE", "میانگین"

    # --- بخش اطلاعات اصلی ---
    name = models.CharField(max_length=255, unique=True, verbose_name="نام شرکت")
    national_id = models.CharField(max_length=50, blank=True, verbose_name="شناسه ملی")
    address = models.TextField(blank=True, verbose_name="آدرس شرکت")

    # --- بخش اطلاعات ادمین و هماهنگ کننده ---
    contact_person = models.CharField(max_length=255, blank=True, verbose_name="نام ادمین")
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name="شماره تماس ادمین")
    coordinator_name = models.CharField(max_length=255, blank=True, verbose_name="نام هماهنگ کننده")
    coordinator_phone = models.CharField(max_length=20, blank=True, verbose_name="شماره تماس هماهنگ کننده")

    # --- بخش تنظیمات مالی و قرارداد ---
    calculation_type = models.CharField(
        max_length=20,
        choices=CalculationType.choices,
        default=CalculationType.FLUID,
        verbose_name="نوع محاسبه قیمت"
    )
    average_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="مبلغ میانگین (در صورت انتخاب)"
    )
    
    payment_model = models.CharField(
        max_length=20,
        choices=PaymentModel.choices,
        default=PaymentModel.ONLINE,
        verbose_name="مدل پرداخت"
    )
    invoice_schedule = models.CharField(
        max_length=20,
        choices=InvoiceSchedule.choices,
        default=InvoiceSchedule.WEEKLY,
        verbose_name="دوره ارسال فاکتور"
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.NONE,
        verbose_name="نوع تخفیف"
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="مقدار تخفیف"
    )
    rounding_amount = models.CharField(
        max_length=20,
        choices=RoundingAmount.choices,
        default=RoundingAmount.NONE,
        verbose_name="رند کردن مبلغ"
    )
    
    # --- بخش تنظیمات سفارش و توضیحات ---
    registration_deadline_hours = models.PositiveIntegerField(default=48, verbose_name="مهلت ثبت نام (ساعت قبل)")
    notes = models.TextField(blank=True, verbose_name="توضیحات")
    
    # --- فیلدهای سیستمی ---
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    status = models.CharField(
        max_length=20,
        choices=CompanyStatus.choices,
        default=CompanyStatus.DRAFT,
        verbose_name="وضعیت"
    )
    active_schedule = models.ForeignKey(
        'schedules.Schedule',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_for_companies',
        verbose_name="برنامه غذایی فعال"
    )

    class Meta:
        verbose_name = "شرکت"
        verbose_name_plural = "شرکت‌ها"

    def __str__(self):
        return self.name


class CompanyConfiguration(models.Model):
    company = models.OneToOneField(
        Company, 
        on_delete=models.CASCADE, 
        related_name='config'
    )
    show_food_images = models.BooleanField(default=True, verbose_name="نمایش عکس غذا")
    show_food_prices = models.BooleanField(default=True, verbose_name="نمایش قیمت غذا")
    allow_holidays = models.BooleanField(default=True, verbose_name="مجاز بودن سفارش در تعطیلات رسمی")
    admin_only_ordering = models.BooleanField(default=False, verbose_name="امکان سفارش فقط توسط ادمین")
    admin_can_see_order_list = models.BooleanField(default=True, verbose_name="نمایش لیست سفارشات (ادمین)")
    admin_can_see_invoices = models.BooleanField(default=True, verbose_name="گزارش فاکتورها (ادمین)")
    admin_has_survey_access = models.BooleanField(default=True, verbose_name="دسترسی به نظرسنجی (ادمین)")
    user_can_see_own_orders = models.BooleanField(default=True, verbose_name="مشاهده سفارشات من (کاربر)")
    user_has_wallet_access = models.BooleanField(default=True, verbose_name="دسترسی به کیف پول (کاربر)")
    user_can_access_surveys = models.BooleanField(default=True, verbose_name="دسترسی به نظرسنجی (کاربر)")
    user_can_submit_tickets = models.BooleanField(default=False, verbose_name="قابلیت ثبت تیکت (کاربر)")
    user_can_leave_comments = models.BooleanField(default=False, verbose_name="قابلیت ثبت کامنت (کاربر)")

    class Meta:
        verbose_name = "تنظیمات شرکت"
        verbose_name_plural = "تنظیمات شرکت‌ها"

    def __str__(self):
        return f"Configuration for {self.company.name}"


@receiver(post_save, sender=Company)
def create_company_config(sender, instance, created, **kwargs):
    if created:
        CompanyConfiguration.objects.create(company=instance)