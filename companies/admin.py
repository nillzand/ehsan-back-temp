
# start of companies/admin.py
from django.contrib import admin
# [MODIFIED] Import the Wallet model
from .models import Company
from wallets.models import Wallet 

# [NEW] Define an inline admin for the Wallet
class WalletInline(admin.StackedInline):
    """
    Makes the Wallet model editable directly within the Company admin page.
    """
    model = Wallet
    can_delete = False  # A company should always have a wallet
    verbose_name_plural = 'Company Wallet'
    # Make the balance read-only to prevent accidental manual changes
    readonly_fields = ('balance',)
    # We only care about the balance here
    fields = ('balance',)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_wallet_balance', 'active_schedule')
    search_fields = ('name',)
    # [NEW] Add the WalletInline to the company admin page
    inlines = (WalletInline,)

    # [MODIFIED] Make the wallet balance display more resilient.
    @admin.display(description='Wallet Balance')
    def get_wallet_balance(self, obj):
        """
        Safely returns the balance from the related wallet object.
        Returns 'N/A' if the company does not have a wallet associated with it.
        """
        # Use hasattr to prevent an error if a company somehow exists without a wallet.
        if hasattr(obj, 'wallet') and obj.wallet is not None:
            return obj.wallet.balance
        return "N/A"

# end of companies/admin.py
