# start of orders/admin.py
from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_company', 'get_date', 'food_item', 'status')
    list_filter = ('status', 'daily_menu__date', 'daily_menu__schedule__company')
    search_fields = ('user__username', 'food_item__name')
    list_select_related = ('user', 'daily_menu', 'food_item', 'daily_menu__schedule__company')

    @admin.display(description='Company')
    def get_company(self, obj):
        return obj.daily_menu.schedule.company.name
    
    @admin.display(description='Date')
    def get_date(self, obj):
        return obj.daily_menu.date
# end of orders/admin.py
