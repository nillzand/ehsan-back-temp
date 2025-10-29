# orders/views.py

from rest_framework import viewsets, permissions, serializers
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

from .models import Order
from .serializers import OrderReadSerializer, OrderWriteSerializer
from wallets.models import Transaction
from users.models import User
from core.permissions import CanModifyOrder


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing orders.
    Users can only see and modify their own orders.
    Includes budget deduction, refunds, and transaction logging.
    """
    permission_classes = [permissions.IsAuthenticated, CanModifyOrder]

    def get_queryset(self):
        """
        Return only orders for the currently authenticated user.
        """
        return Order.objects.filter(user=self.request.user).select_related(
            'food_item',
            'daily_menu__schedule__company'
        ).prefetch_related(
            'side_dishes'
        )

    def get_serializer_class(self):
        """
        Use write serializer for creating/updating, read serializer otherwise.
        """
        if self.action in ['create', 'update', 'partial_update']:
            return OrderWriteSerializer
        return OrderReadSerializer

    def perform_create(self, serializer):
        """
        Wrap order creation and budget deduction in a transaction.
        """
        user = self.request.user
        total_cost = serializer.context.get('total_cost', Decimal('0.00'))

        with transaction.atomic():
            user_for_update = User.objects.select_for_update().get(pk=user.pk)
            
            if user_for_update.budget < total_cost:
                raise serializers.ValidationError("Insufficient funds.")

            order = serializer.save(user=user_for_update)
            user_for_update.budget -= total_cost
            user_for_update.save(update_fields=['budget'])

            # [FIX] Only create a transaction if the user belongs to a company with a wallet.
            if user_for_update.company and hasattr(user_for_update.company, 'wallet'):
                Transaction.objects.create(
                    wallet=user_for_update.company.wallet,
                    user=user_for_update,
                    transaction_type=Transaction.TransactionType.ORDER_DEDUCTION,
                    amount=-total_cost,
                    description=f"Deduction for Order #{order.id}"
                )
    
    def perform_update(self, serializer):
        """
        Handle order updates, calculate cost differences, and adjust the user's budget.
        """
        order_instance = serializer.instance
        
        old_food_price = order_instance.food_item.price if order_instance.food_item else Decimal('0.00')
        old_sides_price = sum(side.price for side in order_instance.side_dishes.all())
        old_total_cost = old_food_price + old_sides_price

        new_food_item = serializer.validated_data.get('food_item', order_instance.food_item)
        new_side_dishes = serializer.validated_data.get('side_dishes', order_instance.side_dishes.all())
        new_food_price = new_food_item.price if new_food_item else Decimal('0.00')
        new_sides_price = sum(side.price for side in new_side_dishes)
        new_total_cost = new_food_price + new_sides_price
        
        cost_difference = old_total_cost - new_total_cost

        if cost_difference == Decimal('0.00'):
            serializer.save()
            return
        
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=self.request.user.pk)
            
            if cost_difference < 0 and user.budget < abs(cost_difference):
                raise serializers.ValidationError(
                    f"Insufficient funds to cover the price increase of {abs(cost_difference)}."
                )

            user.budget += cost_difference
            user.save(update_fields=['budget'])
            
            serializer.save()
            
            # [FIX] Also check for company wallet here for safety
            if user.company and hasattr(user.company, 'wallet'):
                transaction_type = Transaction.TransactionType.REFUND if cost_difference > 0 else Transaction.TransactionType.ORDER_DEDUCTION
                Transaction.objects.create(
                    wallet=user.company.wallet,
                    user=user,
                    transaction_type=transaction_type,
                    amount=cost_difference,
                    description=f"Price adjustment for updated Order #{order_instance.id}"
                )

    def perform_destroy(self, instance):
        """
        Handle order cancellation by refunding the full amount to the user's budget.
        """
        food_price = instance.food_item.price if instance.food_item else Decimal('0.00')
        sides_price = sum(side.price for side in instance.side_dishes.all())
        refund_amount = food_price + sides_price
        
        if refund_amount > Decimal('0.00'):
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=instance.user.pk)
                user.budget += refund_amount
                user.save(update_fields=['budget'])
                
                # [FIX] And check here as well for the refund transaction
                if user.company and hasattr(user.company, 'wallet'):
                    Transaction.objects.create(
                        wallet=user.company.wallet,
                        user=user,
                        transaction_type=Transaction.TransactionType.REFUND,
                        amount=refund_amount,
                        description=f"Refund for canceled Order #{instance.id}"
                    )

        instance.delete()