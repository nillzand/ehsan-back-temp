# wallets/views.py
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics, status 
from rest_framework.response import Response
from decimal import Decimal

from companies.models import Company
from users.models import User
from .models import Wallet, Transaction
from .serializers import DepositSerializer, WalletSerializer 
from core.permissions import IsSuperAdmin, IsCompanyAdmin, IsAdmin

class MyCompanyWalletView(generics.RetrieveAPIView):
    serializer_class = WalletSerializer
    permission_classes = [IsAdmin]

    def get_object(self):
        user = self.request.user
        if user.role == User.Role.COMPANY_ADMIN and user.company:
            wallet = get_object_or_404(
                Wallet.objects.prefetch_related('transactions__user'),
                company=user.company
            )
            return wallet
        elif user.role == User.Role.SUPER_ADMIN:
            # A Super Admin might not have a company, so this logic needs care.
            # This endpoint is primarily for Company Admins. 
            # We return the first wallet for testing, but a dedicated Super Admin endpoint would be better.
            return Wallet.objects.prefetch_related('transactions__user').first()
        return None

class WalletDepositView(APIView):
    """
    Allows a Super Admin to deposit funds into a company's wallet.
    """
    permission_classes = [IsSuperAdmin]
    serializer_class = DepositSerializer

    @transaction.atomic
    def post(self, request, company_id, *args, **kwargs):
        company = get_object_or_404(Company, pk=company_id)
        wallet = get_object_or_404(Wallet, company=company)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount_to_deposit = serializer.validated_data['amount']

        wallet.balance = F('balance') + amount_to_deposit
        wallet.save(update_fields=['balance'])
        wallet.refresh_from_db()

        Transaction.objects.create(
            wallet=wallet,
            user=request.user,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            amount=amount_to_deposit,
            description=f"Deposit made by Super Admin {request.user.username}."
        )
        return Response({"message": "Deposit successful.", "new_balance": wallet.balance}, status=status.HTTP_200_OK)

class WalletWithdrawView(APIView):
    """
    Allows a Super Admin to withdraw funds from a company's wallet.
    """
    permission_classes = [IsSuperAdmin]
    serializer_class = DepositSerializer

    @transaction.atomic
    def post(self, request, company_id, *args, **kwargs):
        company = get_object_or_404(Company, pk=company_id)
        wallet = get_object_or_404(Wallet, company=company)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount_to_withdraw = serializer.validated_data['amount']

        if wallet.balance < amount_to_withdraw:
            return Response({"error": "مبلغ درخواستی برای کسر، از موجودی کیف پول بیشتر است."}, status=status.HTTP_400_BAD_REQUEST)

        wallet.balance = F('balance') - amount_to_withdraw
        wallet.save(update_fields=['balance'])
        wallet.refresh_from_db()

        Transaction.objects.create(
            wallet=wallet,
            user=request.user,
            transaction_type=Transaction.TransactionType.DEPOSIT, # Using DEPOSIT with a negative amount for withdrawal
            amount=-amount_to_withdraw,
            description=f"برداشت وجه توسط ادمین کل {request.user.username}."
        )
        return Response({"message": "مبلغ با موفقیت از کیف پول کسر شد.", "new_balance": wallet.balance}, status=status.HTTP_200_OK)

class CompanyWalletDepositView(APIView):
    """
    Allows a Company Admin to simulate a deposit into their own company's wallet.
    """
    permission_classes = [IsCompanyAdmin]
    serializer_class = DepositSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        wallet = get_object_or_404(Wallet, company=user.company)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount_to_deposit = serializer.validated_data['amount']

        wallet.balance = F('balance') + amount_to_deposit
        wallet.save(update_fields=['balance'])
        wallet.refresh_from_db()

        Transaction.objects.create(
            wallet=wallet,
            user=user,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            amount=amount_to_deposit,
            description=f"واریز توسط ادمین شرکت ({user.username})."
        )
        return Response({"message": "کیف پول با موفقیت شارژ شد.", "new_balance": wallet.balance}, status=status.HTTP_200_OK)