# wallets/models.py

from django.db import models
from django.conf import settings
from companies.models import Company


class Wallet(models.Model):
    """
    Represents the financial wallet for a client company.
    Each company has exactly one wallet.
    """
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="The total available balance for the company."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet for {self.company.name} - Balance: {self.balance}"


class Transaction(models.Model):
    """
    Logs every financial transaction in the system for auditing.
    Each transaction is linked to a Wallet and optionally to a User.
    """
    class TransactionType(models.TextChoices):
        DEPOSIT = "DEPOSIT", "Deposit"
        BUDGET_ALLOCATION = "BUDGET_ALLOCATION", "Budget Allocation"
        ORDER_DEDUCTION = "ORDER_DEDUCTION", "Order Deduction"
        REFUND = "REFUND", "Refund"  # New type for refunds

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,  # Prevent deleting a wallet that has transactions
        related_name='transactions'
    )
    # User who initiated the transaction; can be null for system-level actions
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    transaction_type = models.CharField(
        max_length=50,
        choices=TransactionType.choices
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="The amount of the transaction. Positive or negative values allowed."
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="A brief description of the transaction (e.g., 'Order #123')."
    )

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} for {self.wallet.company.name} at {self.timestamp}"
