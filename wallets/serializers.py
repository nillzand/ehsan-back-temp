# wallets/serializers.py
from rest_framework import serializers
from decimal import Decimal
from .models import Wallet, Transaction

class DepositSerializer(serializers.Serializer):
    """
    Serializer for the deposit action. Validates the amount.
    """
    amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=Decimal('0.01')
    )

# --- NEW CODE STARTS HERE ---

class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for listing transaction details.
    """
    # To show who was involved without exposing the full user object
    user_username = serializers.CharField(source='user.username', read_only=True, default='System')

    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_type', 'amount', 'timestamp', 
            'description', 'user_username'
        ]


class WalletSerializer(serializers.ModelSerializer):
    """
    Serializer for providing a detailed view of a company's wallet.
    Includes a nested list of all associated transactions.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    # Use the new TransactionSerializer for the nested relationship
    transactions = TransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Wallet
        fields = [
            'id', 'company_name', 'balance', 'updated_at', 'transactions'
        ]