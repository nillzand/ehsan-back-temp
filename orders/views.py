# back/orders/views.py
from rest_framework import viewsets, permissions, serializers
from django.db import transaction
from decimal import Decimal

from .models import Order
from .serializers import OrderReadSerializer, OrderWriteSerializer
from wallets.models import Transaction
from users.models import User
from core.permissions import CanModifyOrder
from companies.models import Company
from discounts.models import DiscountCode, DiscountCodeUsage

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, CanModifyOrder]

    def get_queryset(self):
        """
        این کوئری اطمینان می‌دهد که هر کاربر فقط سفارش‌های خودش را می‌بیند.
        """
        return Order.objects.filter(user=self.request.user).select_related(
            'food_item',
            'daily_menu__schedule__company'
        ).prefetch_related(
            'side_dishes'
        )

    def get_serializer_class(self):
        """
        بسته به نوع عملیات (خواندن یا نوشتن)، سریالایزر مناسب را برمی‌گرداند.
        """
        if self.action in ['create', 'update', 'partial_update']:
            return OrderWriteSerializer
        return OrderReadSerializer

    def perform_create(self, serializer):
        """
        منطق اصلی ایجاد یک سفارش جدید، شامل پردازش کد تخفیف و کسر از بودجه.
        """
        user = self.request.user
        company = user.company if hasattr(user, 'company') and user.company else None
        
        # [اصلاح کلیدی ۱] کد تخفیف را از داده‌های معتبر شده سریالایزر استخراج می‌کنیم
        discount_code_str = serializer.validated_data.pop('discount_code', None)

        # تمام عملیات زیر در یک تراکنش دیتابیس انجام می‌شود تا از بروز خطا جلوگیری شود
        with transaction.atomic():
            # سفارش را با کاربر فعلی ذخیره می‌کنیم
            order = serializer.save(user=user)

            # [اصلاح کلیدی ۲] اگر کد تخفیفی ارسال شده بود، آن را پردازش می‌کنیم
            if discount_code_str:
                try:
                    # کد تخفیف فعال را در دیتابیس پیدا می‌کنیم
                    code_instance = DiscountCode.objects.get(code__iexact=discount_code_str, is_active=True)
                    # TODO: می‌توان بررسی‌های بیشتری (تاریخ انقضا، تعداد استفاده) را اینجا نیز اضافه کرد
                    
                    # یک رکورد استفاده از کد تخفیف برای این سفارش و کاربر ثبت می‌کنیم
                    DiscountCodeUsage.objects.create(discount_code=code_instance, user=user, order=order)
                    
                    # تعداد کل استفاده از کد را یک واحد افزایش می‌دهیم
                    code_instance.usage_count += 1
                    code_instance.save()
                except DiscountCode.DoesNotExist:
                    # اگر کد وجود نداشت یا فعال نبود، به سادگی از آن عبور می‌کنیم
                    pass

            # [اصلاح کلیدی ۳] حالا متد محاسبه قیمت را فراخوانی می‌کنیم
            # این متد به دلیل وجود `discount_usage` که در بالا ایجاد شد، تخفیف را محاسبه خواهد کرد
            order.calculate_and_save_prices()
            
            # منطق کسر از بودجه برای شرکت‌هایی با مدل پرداخت آنلاین
            if company and company.payment_model == Company.PaymentModel.ONLINE:
                # برای جلوگیری از race condition، رکورد کاربر را قفل می‌کنیم
                user_for_update = User.objects.select_for_update().get(pk=user.pk)
                
                if user_for_update.budget < order.final_price:
                    # اگر بودجه کافی نباشد، تراکنش را لغو کرده و خطا برمی‌گردانیم
                    raise serializers.ValidationError("اعتبار شما برای ثبت این سفارش کافی نیست.")

                # کسر هزینه از بودجه کاربر
                user_for_update.budget -= order.final_price
                user_for_update.save(update_fields=['budget'])

                # ثبت تراکنش در کیف پول شرکت (برای حسابرسی)
                if user_for_update.company and hasattr(user_for_update.company, 'wallet'):
                    Transaction.objects.create(
                        wallet=user_for_update.company.wallet,
                        user=user_for_update,
                        transaction_type=Transaction.TransactionType.ORDER_DEDUCTION,
                        amount=-order.final_price,
                        description=f"کسر هزینه برای سفارش #{order.id}"
                    )
    
    def perform_update(self, serializer):
        # این بخش برای ویرایش سفارش است که در حال حاضر پیاده‌سازی نشده است
        # و نیاز به منطق مشابه برای بازگرداندن بودجه و ... دارد.
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        # این بخش برای لغو سفارش است. باید منطق بازگرداندن بودجه
        # و حذف رکورد استفاده از کد تخفیف در اینجا اضافه شود.
        super().perform_destroy(instance)