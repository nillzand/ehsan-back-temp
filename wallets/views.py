# wallets/views.py
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from companies.models import Company
from .models import Wallet, Transaction
from .serializers import DepositSerializer, WalletSerializer, TransactionSerializer
from core.permissions import IsSuperAdmin, IsCompanyAdmin


# ------------------------
# Pagination for transactions
# ------------------------
class TransactionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


# ------------------------
# View for Company Admin to see their wallet
# ------------------------
class MyCompanyWalletView(generics.RetrieveAPIView):
    """
    Allows a Company Admin to view their own company's wallet
    details and paginated transaction history.
    """
    serializer_class = WalletSerializer
    permission_classes = [IsCompanyAdmin]
    pagination_class = TransactionPagination

    def get_object(self):
        user = self.request.user
        wallet = get_object_or_404(
            Wallet.objects.prefetch_related('transactions__user'),
            company=user.company
        )
        return wallet

    def retrieve(self, request, *args, **kwargs):
        wallet = self.get_object()
        serializer = self.get_serializer(wallet)

        # Paginate transactions
        transactions_qs = wallet.transactions.all().order_by('-created_at')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(transactions_qs, request)
        transactions_serializer = TransactionSerializer(page, many=True)

        data = serializer.data
        data['transactions'] = transactions_serializer.data

        return paginator.get_paginated_response(data)


# ------------------------
# View for Super Admin to deposit funds
# ------------------------
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

        # Use F() expression for atomic increment
        wallet.balance = F('balance') + amount_to_deposit
        wallet.save(update_fields=['balance'])
        wallet.refresh_from_db()  # Get actual balance after F()

        # Log the transaction
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
