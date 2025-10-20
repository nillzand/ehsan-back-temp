# backend/orders/models.py
# start of orders/models.py
from django.db import models
from django.conf import settings

class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PLACED = "PLACED", "ثبت شده"
        CONFIRMED = "CONFIRMED", "تایید شده"
        PREPARING = "PREPARING", "در حال آماده‌سازی"
        DELIVERED = "DELIVERED", "تحویل داده شده"
        CANCELED = "CANCELED", "لغو شده"

    # --- Relationships ---
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    daily_menu = models.ForeignKey(
        'schedules.DailyMenu',
        on_delete=models.SET_NULL, # Keep order history even if menu is deleted
        null=True,
        related_name='orders'
    )
    food_item = models.ForeignKey(
        'menu.FoodItem',
        on_delete=models.SET_NULL, # Keep order history even if food item is deleted
        null=True,
        related_name='orders'
    )
    side_dishes = models.ManyToManyField(
        'menu.SideDish',
        related_name='orders',
        blank=True
    )

    # --- Order Details ---
    status = models.CharField(
        max_length=50,
        choices=OrderStatus.choices,
        default=OrderStatus.PLACED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"سفارش #{self.id} برای {self.user.username} در {self.daily_menu.date}"

# end of orders/models.py