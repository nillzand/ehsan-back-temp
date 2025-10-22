# wallets/views.py
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics, status 
from rest_framework.response import Response

from companies.models import Company
from .models import Wallet, Transaction
from .serializers import DepositSerializer, WalletSerializer 
from core.permissions import IsSuperAdmin, IsCompanyAdmin

class MyCompanyWalletView(generics.RetrieveAPIView):
    """
    [تغییر] این ویو حالا به سادگی اطلاعات کیف پول شرکت کاربر را 
    به همراه تمام تراکنش‌های آن برمی‌گرداند.
    """
    serializer_class = WalletSerializer
    permission_classes = [IsCompanyAdmin]

    def get_object(self):
        user = self.request.user
        wallet = get_object_or_404(
            Wallet.objects.prefetch_related('transactions__user'),
            company=user.company
        )
        return wallet

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
            transaction_type=Transaction.TransactionType.DEPOSIT,
            amount=amount_to_deposit,
            description=f"Deposit made by Super Admin {request.user.username}."
        )

        return Response(
            {"message": "Deposit successful.", "new_balance": wallet.balance},
            status=status.HTTP_200_OK
        )