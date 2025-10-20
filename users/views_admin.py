# users/views_admin.py
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

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

        # 1. Check if company wallet has sufficient funds
        if company_wallet.balance < amount_to_allocate:
            return Response(
                {"error": "Insufficient company funds to perform this allocation."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 2. Perform the transaction atomically
        company_wallet.balance -= amount_to_allocate
        company_wallet.save()

        target_user.budget += amount_to_allocate
        target_user.save()

        # 3. Log both sides of the transaction for auditing
        # Log the withdrawal from the company wallet
        Transaction.objects.create(
            wallet=company_wallet,
            user=request.user, # The admin who performed the action
            transaction_type=Transaction.TransactionType.BUDGET_ALLOCATION,
            amount=-amount_to_allocate, # Negative amount for withdrawal
            description=f"Allocation to employee {target_user.username}."
        )

        # Log the "deposit" into the user's budget (for their transaction history)
        Transaction.objects.create(
            wallet=company_wallet,
            user=target_user,
            transaction_type=Transaction.TransactionType.BUDGET_ALLOCATION,
            amount=amount_to_allocate,
            description=f"Budget allocated by {request.user.username}."
        )
        
        return Response(
            {
                "message": "Budget allocated successfully.",
                "employee": target_user.username,
                "new_employee_budget": target_user.budget,
                "new_company_balance": company_wallet.balance,
            },
            status=status.HTTP_200_OK
        )