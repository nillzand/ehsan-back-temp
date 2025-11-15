from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from orders.models import Order

class Survey(models.Model):
    """
    نظرسنجی ثبت شده توسط کاربر برای یک سفارش مشخص.
    """
    # با OneToOneField تضمین می‌کنیم که برای هر سفارش فقط یک نظرسنجی بتوان ثبت کرد
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='survey'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='surveys'
    )
    # امتیاز عددی بین ۱ تا ۵
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="امتیاز"
    )
    # نظر متنی کاربر (اختیاری)
    comment = models.TextField(
        blank=True,
        verbose_name="نظر متنی"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت"
    )

    class Meta:
        verbose_name = "نظرسنجی"
        verbose_name_plural = "نظرسنجی‌ها"
        ordering = ['-created_at']

    def __str__(self):
        return f"نظرسنجی برای سفارش #{self.order.id} توسط {self.user.username}"