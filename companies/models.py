# back/companies/models.py
from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    contact_person = models.CharField(max_length=255, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # [جدید] فیلد برای اتصال شرکت به یک برنامه غذایی فعال
    active_schedule = models.ForeignKey(
        'schedules.Schedule',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_for_companies',
        help_text="برنامه غذایی که برای کارمندان این شرکت نمایش داده می‌شود."
    )

    class Meta:
        verbose_name_plural = "شرکت‌ها"

    def __str__(self):
        return self.name
    