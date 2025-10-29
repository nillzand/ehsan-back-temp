# wallets/admin.py
from django.contrib import admin
from .models import Wallet, Transaction

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('company', 'balance', 'updated_at')
    search_fields = ('company__name',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'wallet', 'transaction_type', 'amount', 'user')
    list_filter = ('transaction_type', 'timestamp', 'wallet__company')
    search_fields = ('wallet__company__name', 'user__username', 'description')
    list_select_related = ('wallet__company', 'user') # Optimization for performance
    