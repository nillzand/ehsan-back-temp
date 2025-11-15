# back/orders/views_admin.py

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django.db.models import Count, Sum, F, Q, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from collections import defaultdict

from .models import Order
from users.models import User
from companies.models import Company
from .serializers import OrderReadSerializer, AdminOrderUpdateSerializer
from core.permissions import IsSuperAdmin, IsAdmin


class OrderFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="daily_menu__date", lookup_expr='gte')
    end_date = filters.DateFilter(field_name="daily_menu__date", lookup_expr='lte')
    company_id = filters.NumberFilter(field_name='user__company_id')
    class Meta:
        model = Order
        fields = ['status', 'company_id', 'start_date', 'end_date']

class AdminOrderViewSet(viewsets.ModelViewSet):
    # [اصلاح] اضافه کردن فیلتر برای جلوگیری از خطا هنگام دسترسی به روابطی که ممکن است null باشند
    queryset = Order.objects.filter(daily_menu__isnull=False, user__isnull=False).select_related(
        'user', 'food_item', 'daily_menu__schedule__company'
    ).prefetch_related('side_dishes').all().order_by('-daily_menu__date', '-created_at')
    permission_classes = [IsSuperAdmin]
    filterset_class = OrderFilter
    http_method_names = ['get', 'patch', 'head', 'options']
    
    def get_serializer_class(self):
        if self.action == 'partial_update':
            return AdminOrderUpdateSerializer
        return OrderReadSerializer

class DashboardStatsView(APIView):
    permission_classes = [IsAdmin]
    
    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=6)
        user = request.user
        
        # [اصلاح] فیلتر کردن سفارش‌هایی که آیتم غذایی ندارند (ممکن است حذف شده باشند)
        base_order_queryset = Order.objects.filter(food_item__isnull=False)
        base_company_queryset = Company.objects.all()
        base_user_queryset = User.objects.all()

        if user.role == User.Role.COMPANY_ADMIN and user.company:
            base_order_queryset = base_order_queryset.filter(user__company=user.company)
            base_company_queryset = base_company_queryset.filter(pk=user.company.id)
            base_user_queryset = base_user_queryset.filter(company=user.company)

        orders_today_qs = base_order_queryset.filter(created_at__date=today)
        
        # [اصلاح] محاسبه فروش بر اساس فیلد 'final_price' که تمام تخفیف‌ها در آن لحاظ شده است
        total_sales = orders_today_qs.aggregate(
            total=Coalesce(Sum('final_price'), Decimal('0.0'))
        )['total']

        sales_data = base_order_queryset.filter(created_at__date__gte=seven_days_ago).values(
            date=F('created_at__date')
        ).annotate(
            order_count=Count('id')
        ).order_by('date')

        todays_orders_list = Order.objects.filter(created_at__date=today).order_by('-created_at')[:4]
        todays_orders_data = OrderReadSerializer(todays_orders_list, many=True, context={'request': request}).data

        company_reports = []
        if user.role == User.Role.SUPER_ADMIN:
            company_reports = Company.objects.annotate(
                user_count=Count('employees', filter=Q(employees__is_active=True))
            ).values('name', 'user_count').order_by('-user_count')[:4]

        # داده‌های placeholder برای گزارش دیروز حذف شد تا با داده‌های واقعی جایگزین شود
        yesterday_reports_placeholder = []

        stats = {
            'orders_today': orders_today_qs.count(),
            'total_sales_today': total_sales,
            'company_count': base_company_queryset.count(),
            'user_count': base_user_queryset.count(),
            'sales_last_7_days': list(sales_data),
            'todays_orders': todays_orders_data,
            'company_reports': list(company_reports),
            'yesterday_reports': yesterday_reports_placeholder,
        }
        return Response(stats)

class AdminReportsView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=29)

        try:
            start_date_str = request.query_params.get('from', thirty_days_ago.isoformat())
            end_date_str = request.query_params.get('to', today.isoformat())
            start_date = timezone.datetime.fromisoformat(start_date_str).date()
            end_date = timezone.datetime.fromisoformat(end_date_str).date()
        except (ValueError, TypeError):
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        company_id = request.query_params.get('companyId')

        base_orders_queryset = Order.objects.filter(
            daily_menu__date__range=(start_date, end_date),
            daily_menu__isnull=False,
            food_item__isnull=False
        )
        if company_id:
            base_orders_queryset = base_orders_queryset.filter(user__company_id=company_id)

        # خلاصه آمار
        today_sales_agg = base_orders_queryset.filter(daily_menu__date=today).aggregate(
            total=Coalesce(Sum('final_price'), Decimal('0.0'))
        )
        
        summary_data = {
            "orders_today": base_orders_queryset.filter(daily_menu__date=today).count(),
            "pending_orders_total": base_orders_queryset.filter(status__in=['PLACED', 'CONFIRMED']).count(),
            "total_sales_today": today_sales_agg['total']
        }
        
        # آیتم‌های پرفروش
        top_items_data = base_orders_queryset.values(
            'food_item__name'
        ).annotate(
            name=F('food_item__name'),
            ordered=Count('id')
        ).order_by('-ordered').values('name', 'ordered')[:5]

        # فروش بر اساس تاریخ
        sales_by_date_data = base_orders_queryset.values(
            date_str=F('daily_menu__date')
        ).annotate(
            orders=Count('id'),
            revenue=Coalesce(Sum('final_price'), Decimal('0.0'))
        ).order_by('date_str').values('date_str', 'orders', 'revenue')

        # آمار شرکت‌ها
        company_stats_qs = Company.objects.all()
        if company_id:
            company_stats_qs = company_stats_qs.filter(id=company_id)
            
        company_stats_data = company_stats_qs.annotate(
            active_users=Count('employees', filter=Q(employees__is_active=True), distinct=True),
            orders=Count('employees__orders', filter=Q(employees__orders__daily_menu__date__range=(start_date, end_date)), distinct=True)
        ).values('id', 'name', 'active_users', 'orders')

        # آمار کاربران
        user_stats_data = {
            "total_users": User.objects.count(),
            "active_last_30_days": User.objects.filter(last_login__gte=(today - timedelta(days=30))).count()
        }

        response_data = {
            "summary": summary_data,
            "top_items": list(top_items_data),
            "sales_by_date": list(sales_by_date_data),
            "company_stats": list(company_stats_data),
            "user_stats": user_stats_data,
        }
        return Response(response_data)

class DailyOrderSummaryView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, *args, **kwargs):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({"error": "A 'date' query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_date = timezone.datetime.fromisoformat(date_str).date()
        except (ValueError, TypeError):
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # [اصلاح] فیلتر کردن سفارش‌های ناقص برای جلوگیری از کرش کردن
        orders = Order.objects.filter(
            daily_menu__date=target_date, 
            food_item__isnull=False,
            user__company__isnull=False
        ).select_related(
            'user__company', 'food_item'
        ).prefetch_related('side_dishes')

        daily_totals = orders.values('food_item__name').annotate(
            count=Count('id')
        ).order_by('-count')

        grouped_by_company = defaultdict(lambda: {"items": defaultdict(int), "statuses": set()})
        
        for order in orders:
            company_name = order.user.company.name
            
            if order.food_item:
                grouped_by_company[company_name]["items"][order.food_item.name] += 1
            
            for side in order.side_dishes.all():
                grouped_by_company[company_name]["items"][side.name] += 1
                
            grouped_by_company[company_name]["statuses"].add(order.status)

        company_summary = []
        for name, data in grouped_by_company.items():
            is_pending = any(s not in [Order.OrderStatus.DELIVERED, Order.OrderStatus.CONFIRMED] for s in data['statuses'])
            
            company_summary.append({
                "company_name": name,
                "status": "PENDING" if is_pending else "CONFIRMED",
                "ordered_items": [{"name": item, "count": count} for item, count in data['items'].items()]
            })

        return Response({
            "target_date": target_date,
            "daily_totals": list(daily_totals),
            "grouped_by_company": sorted(company_summary, key=lambda x: x['company_name'])
        })


class WeeklyOrderSummaryView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, *args, **kwargs):
        start_date_str = request.query_params.get('start_date')
        if not start_date_str:
            today = timezone.now().date()
            days_since_saturday = (today.weekday() + 2) % 7
            start_date = today - timedelta(days=days_since_saturday)
        else:
            try:
                start_date = timezone.datetime.fromisoformat(start_date_str).date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        end_date = start_date + timedelta(days=6)

        # [اصلاح] فیلتر کردن سفارش‌های ناقص
        orders = Order.objects.filter(
            daily_menu__date__range=[start_date, end_date],
            food_item__isnull=False
        ).prefetch_related('food_item', 'side_dishes', 'daily_menu')

        daily_counts = defaultdict(lambda: defaultdict(int))

        for order in orders:
            date_key = order.daily_menu.date.isoformat()
            if order.food_item:
                daily_counts[date_key][('food', order.food_item.name)] += 1
            
            for side in order.side_dishes.all():
                daily_counts[date_key][('side', side.name)] += 1
        
        result = defaultdict(list)
        for date_key, items in daily_counts.items():
            for (item_type, item_name), count in items.items():
                result[date_key].append({
                    "name": item_name,
                    "count": count,
                    "type": item_type
                })
        
        for date_key in result:
            result[date_key].sort(key=lambda x: (x['type'], -x['count']))

        return Response({
            "start_date": start_date,
            "end_date": end_date,
            "summary": result
        })