# back/schedules/models.py
from django.db import models
from django.core.exceptions import ValidationError

class Schedule(models.Model):
    name = models.CharField(max_length=255)
    # [تغییر] فیلد شرکت را اختیاری می‌کنیم
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='schedules',
        null=True,  # اجازه می‌دهد این فیلد خالی باشد
        blank=True, # در فرم‌های ادمین هم اختیاری می‌شود
        verbose_name="شرکت (در صورت اختصاصی بودن)"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def clean(self):
        # Ensures that the start date is not after the end date.
        if self.start_date > self.end_date:
            raise ValidationError("End date cannot be before the start date.")

    def __str__(self):
        # [تغییر] نمایش نام برنامه به شکل خواناتر
        if self.company:
            return f"{self.name} ({self.company.name})"
        return f"{self.name} (منوی پیش‌فرض)"

# ... مدل DailyMenu بدون تغییر باقی می‌ماند ...
class DailyMenu(models.Model):
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name='daily_menus'
    )
    date = models.DateField()
    available_foods = models.ManyToManyField(
        'menu.FoodItem',
        related_name='daily_menus',
        blank=True
    )
    available_sides = models.ManyToManyField(
        'menu.SideDish',
        related_name='daily_menus',
        blank=True
    )

    class Meta:
        # Ensures that there is only one menu per day for a given schedule
        unique_together = ('schedule', 'date')
        ordering = ['date']

    def clean(self):
        # Ensures that the menu's date is within its parent schedule's date range.
        if not (self.schedule.start_date <= self.date <= self.schedule.end_date):
            raise ValidationError(
                f"Date must be within the schedule's range "
                f"({self.schedule.start_date} to {self.schedule.end_date})."
            )

    def __str__(self):
        return f"Menu for {self.date} ({self.schedule.name})"