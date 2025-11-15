# back/discounts/views.py

from rest_framework import viewsets, permissions, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import DiscountCode, DynamicMenuDiscount, DiscountCodeUsage
from .serializers import DiscountCodeSerializer, DynamicMenuDiscountSerializer, DiscountCodeUsageSerializer

# [اصلاح] IsAuthenticated از rest_framework.permissions وارد شده است
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdmin


class ValidateDiscountCodeView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        code_str = request.data.get('code')
        if not code_str:
            return Response({'is_valid': False, 'message': 'کد تخفیف ارائه نشده است.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            code = DiscountCode.objects.get(code__iexact=code_str)
            now = timezone.now()

            if not code.is_active:
                return Response({'is_valid': False, 'message': 'این کد تخفیف فعال نیست.'})
            if code.start_date > now:
                return Response({'is_valid': False, 'message': 'زمان استفاده از این کد هنوز شروع نشده است.'})
            if code.end_date and code.end_date < now:
                return Response({'is_valid': False, 'message': 'این کد تخفیف منقضی شده است.'})
            if code.max_usage_count is not None and code.usage_count >= code.max_usage_count:
                return Response({'is_valid': False, 'message': 'ظرفیت استفاده از این کد به پایان رسیده است.'})
            
            user_usage_count = DiscountCodeUsage.objects.filter(discount_code=code, user=request.user).count()
            if user_usage_count >= code.max_usage_per_user:
                return Response({'is_valid': False, 'message': 'شما قبلاً از حداکثر تعداد مجاز این کد استفاده کرده‌اید.'})
            
            serializer = DiscountCodeSerializer(code)
            return Response({
                'is_valid': True,
                'message': 'کد تخفیف معتبر است.',
                'discount_details': serializer.data
            })

        except DiscountCode.DoesNotExist:
            return Response({'is_valid': False, 'message': 'کد تخفیف وارد شده معتبر نیست.'})


class DiscountCodeViewSet(viewsets.ModelViewSet):
    queryset = DiscountCode.objects.all().order_by('-created_at')
    serializer_class = DiscountCodeSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        is_archived = self.request.query_params.get('archived') == 'true'
        
        now = timezone.now()
        active_codes = qs.filter(is_active=True, end_date__gte=now)
        archived_codes = qs.exclude(id__in=active_codes.values('id'))

        if is_archived:
            return archived_codes
        return active_codes

    @action(detail=True, methods=['get'])
    def usages(self, request, pk=None):
        discount_code = self.get_object()
        usages = discount_code.usages.select_related('user', 'order__food_item').prefetch_related('order__side_dishes').all()
        serializer = DiscountCodeUsageSerializer(usages, many=True, context={'request': request})
        return Response(serializer.data)


class DynamicMenuDiscountViewSet(viewsets.ModelViewSet):
    queryset = DynamicMenuDiscount.objects.all().order_by('-created_at')
    serializer_class = DynamicMenuDiscountSerializer
    permission_classes = [IsAdmin]