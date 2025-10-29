# contracts/admin.py
from django.contrib import admin
from .models import Contract

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('company', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'company')
    search_fields = ('company__name', 'notes')
    list_editable = ('status',)