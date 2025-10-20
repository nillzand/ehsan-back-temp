# start of orders/views.py
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
# [MODIFIED] Import the new permission class
from core.permissions import CanModifyOrder


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing orders.
    Users can only see and modify their own orders.
    Includes budget deduction, refunds, and transaction logging.
    """
    # [MODIFIED] Add the new permission class. It will run after IsAuthenticated.
    permission_classes = [permissions.IsAuthenticated, CanModifyOrder]

    # ... (get_queryset and get_serializer_class methods are unchanged) ...
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
            # Lock the user row to prevent race conditions on their budget.
            user_for_update = User.objects.select_for_update().get(pk=user.pk)
            
            # Re-check budget inside the transaction for safety
            if user_for_update.budget < total_cost:
                raise serializers.ValidationError("Insufficient funds.")

            order = serializer.save(user=user_for_update)
            user_for_update.budget -= total_cost
            user_for_update.save(update_fields=['budget'])

            Transaction.objects.create(
                wallet=user_for_update.company.wallet,
                user=user_for_update,
                transaction_type=Transaction.TransactionType.ORDER_DEDUCTION,
                amount=-total_cost,
                description=f"Deduction for Order #{order.id}"
            )
    
    # --- REFACTORED CODE STARTS HERE ---

    # [REMOVED] The redundant helper function is no longer needed.
    # def _is_modification_allowed(self, order_date): ...

    def perform_update(self, serializer):
        """
        Handle order updates, calculate cost differences, and adjust the user's budget.
        The permission check is now handled automatically by CanModifyOrder.
        """
        order_instance = serializer.instance
        
        # [REMOVED] The manual permission check is gone.
        # if not self._is_modification_allowed(order_instance.daily_menu.date): ...

        # Calculate the cost of the order BEFORE the update
        old_food_price = order_instance.food_item.price if order_instance.food_item else Decimal('0.00')
        old_sides_price = sum(side.price for side in order_instance.side_dishes.all())
        old_total_cost = old_food_price + old_sides_price

        # Calculate the cost of the order AFTER the update
        new_food_item = serializer.validated_data.get('food_item', order_instance.food_item)
        new_side_dishes = serializer.validated_data.get('side_dishes', order_instance.side_dishes.all())
        new_food_price = new_food_item.price if new_food_item else Decimal('0.00')
        new_sides_price = sum(side.price for side in new_side_dishes)
        new_total_cost = new_food_price + new_sides_price
        
        cost_difference = old_total_cost - new_total_cost

        if cost_difference == Decimal('0.00'):
            # If no price change, just save the order.
            serializer.save()
            return
        
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=self.request.user.pk)
            
            # If the new order is more expensive, check if the user has enough budget for the difference.
            if cost_difference < 0 and user.budget < abs(cost_difference):
                raise serializers.ValidationError(
                    f"Insufficient funds to cover the price increase of {abs(cost_difference)}."
                )

            # Adjust budget (positive difference = refund, negative = deduction)
            user.budget += cost_difference
            user.save(update_fields=['budget'])
            
            # Save the updated order
            serializer.save()
            
            # Log the transaction for the budget adjustment
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
        The permission check is now handled automatically by CanModifyOrder.
        """
        # [REMOVED] The manual permission check is gone.
        # if not self._is_modification_allowed(instance.daily_menu.date): ...
        
        food_price = instance.food_item.price if instance.food_item else Decimal('0.00')
        sides_price = sum(side.price for side in instance.side_dishes.all())
        refund_amount = food_price + sides_price
        
        if refund_amount > Decimal('0.00'):
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=instance.user.pk)
                user.budget += refund_amount
                user.save(update_fields=['budget'])
                
                # Log the refund transaction
                Transaction.objects.create(
                    wallet=user.company.wallet,
                    user=user,
                    transaction_type=Transaction.TransactionType.REFUND,
                    amount=refund_amount,
                    description=f"Refund for canceled Order #{instance.id}"
                )

        # Finally, delete the order instance
        instance.delete()
# end of orders/views.py```
