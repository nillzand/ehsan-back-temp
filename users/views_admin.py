# users/views_admin.py
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal

from .models import User
from wallets.models import Wallet, Transaction
from .serializers import AllocateBudgetSerializer
from core.permissions import IsCompanyAdminOfTargetUser

class AllocateBudgetView(APIView):
    """
    An endpoint for a Company Admin to allocate funds from the company wallet
    to an employee's personal budget.
    """
    permission_classes = [IsCompanyAdminOfTargetUser]
    serializer_class = AllocateBudgetSerializer

    @transaction.atomic
    def post(self, request, user_id, *args, **kwargs):
        target_user = get_object_or_404(User, pk=user_id)
        company_wallet = get_object_or_404(Wallet, company=request.user.company)
        
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount_to_allocate = serializer.validated_data['amount']

        if company_wallet.balance < amount_to_allocate:
            return Response({"error": "موجودی کیف پول شرکت برای انجام این تراکنش کافی نیست."}, status=status.HTTP_400_BAD_REQUEST)
        
        company_wallet.balance -= amount_to_allocate
        company_wallet.save()

        target_user.budget += amount_to_allocate
        target_user.save()

        Transaction.objects.create(
            wallet=company_wallet,
            user=request.user,
            transaction_type=Transaction.TransactionType.BUDGET_ALLOCATION,
            amount=-amount_to_allocate,
            description=f"تخصیص اعتبار به کارمند {target_user.username}."
        )
        
        return Response({"message": "اعتبار با موفقیت تخصیص داده شد."}, status=status.HTTP_200_OK)


class ReclaimBudgetView(APIView):
    """
    An endpoint for a Company Admin to reclaim funds from an employee's
    personal budget back to the company wallet.
    """
    permission_classes = [IsCompanyAdminOfTargetUser]
    serializer_class = AllocateBudgetSerializer

    @transaction.atomic
    def post(self, request, user_id, *args, **kwargs):
        target_user = get_object_or_404(User, pk=user_id)
        company_wallet = get_object_or_404(Wallet, company=request.user.company)
        
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount_to_reclaim = serializer.validated_data['amount']

        if target_user.budget < amount_to_reclaim:
            return Response({"error": "مبلغ درخواستی برای بازپس‌گیری از اعتبار کارمند بیشتر است."}, status=status.HTTP_400_BAD_REQUEST)
        
        target_user.budget -= amount_to_reclaim
        target_user.save()

        company_wallet.balance += amount_to_reclaim
        company_wallet.save()

        Transaction.objects.create(
            wallet=company_wallet,
            user=request.user,
            transaction_type=Transaction.TransactionType.REFUND,
            amount=amount_to_reclaim,
            description=f"بازپس‌گیری اعتبار از کارمند {target_user.username}."
        )
        
        return Response({"message": "اعتبار با موفقیت به کیف پول شرکت بازگردانده شد."}, status=status.HTTP_200_OK)