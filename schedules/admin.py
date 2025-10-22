# back/schedules/admin.py
from django.contrib import admin
from .models import Schedule, DailyMenu

class DailyMenuInline(admin.TabularInline):
    model = DailyMenu
    extra = 1
    fields = ('date', 'available_foods', 'available_sides')
    filter_horizontal = ('available_foods', 'available_sides')

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    # [MODIFIED] Add a custom display method to show if a schedule is a default one
    list_display = ('name', 'company', 'is_default_schedule', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'company')
    search_fields = ('name', 'company__name')
    inlines = [DailyMenuInline]

    # [NEW] Custom method to add a boolean checkmark column in the admin
    @admin.display(boolean=True, description='Default Menu?')
    def is_default_schedule(self, obj):
        """Returns True if the schedule is not linked to any specific company."""
        return obj.company is None