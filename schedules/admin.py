from django.contrib import admin
from .models import Schedule, DailyMenu

class DailyMenuInline(admin.TabularInline):
    """
    Allows editing DailyMenu models directly within the Schedule admin page.
    """
    model = DailyMenu
    extra = 1  # Number of empty forms to display
    fields = ('date', 'available_foods', 'available_sides')
    filter_horizontal = ('available_foods', 'available_sides') # Better UI for ManyToMany

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'company')
    search_fields = ('name', 'company__name')
    inlines = [DailyMenuInline] # Nest the daily menu editor