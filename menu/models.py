from django.db import models

class FoodCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "دسته‌بندی‌های غذا"

    def __str__(self):
        return self.name

class FoodItem(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # The 'upload_to' path will be relative to the MEDIA_ROOT
    image = models.ImageField(upload_to='food_images/', blank=True, null=True)
    category = models.ForeignKey(
        FoodCategory,
        related_name='food_items',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class SideDish(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name