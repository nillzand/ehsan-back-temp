# orders/views_admin.py

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django.db.models import Count, Sum, F, Q
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from collections import defaultdict

from .models import Order
from users.models import User
from companies.models import Company
from menu.models import FoodItem
from core.permissions import IsSuperAdmin, IsAdmin 
from .serializers import OrderReadSerializer, AdminOrderUpdateSerializer

# ... (OrderFilter, AdminOrderViewSet, DailyOrderSummaryView, DashboardStatsView remain unchanged) ...

class OrderFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="daily_menu__date", lookup_expr='gte')
    end_date = filters.DateFilter(field_name="daily_menu__date", lookup_expr='lte')
    company_id = filters.NumberFilter(field_name='user__company_id') # Corrected field name

    class Meta:
        model = Order
        fields = ['status', 'company_id', 'start_date', 'end_date']


class AdminOrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related(
        'user',
        'food_item',
        'daily_menu__schedule__company'
    ).prefetch_related('side_dishes').all().order_by('-daily_menu__date', '-created_at')
    
    permission_classes = [IsSuperAdmin]
    filterset_class = OrderFilter
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return AdminOrderUpdateSerializer
        return OrderReadSerializer

class DailyOrderSummaryView(APIView):
    permission_classes = [IsSuperAdmin]
    def get(self, request, *args, **kwargs):
        query_date_str = request.query_params.get('date', timezone.now().strftime('%Y-%m-%d'))
        try:
            query_date = timezone.datetime.strptime(query_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)
        food_summary = Order.objects.filter(daily_menu__date=query_date, status__in=['PLACED', 'CONFIRMED']).values('food_item__name').annotate(count=Count('food_item')).order_by('-count')
        side_dish_summary = Order.objects.filter(daily_menu__date=query_date, status__in=['PLACED', 'CONFIRMED']).values('side_dishes__name').annotate(count=Count('side_dishes')).order_by('-count')
        side_dish_summary = [item for item in side_dish_summary if item['side_dishes__name'] is not None]
        return Response({'date': query_date, 'food_summary': list(food_summary), 'side_dish_summary': list(side_dish_summary)})


class DashboardStatsView(APIView):
    permission_classes = [IsAdmin]
    
    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=6)
        user = request.user
        
        base_queryset = Order.objects.all()
        if user.role == User.Role.COMPANY_ADMIN:
            base_queryset = base_queryset.filter(user__company=user.company)
        orders_today_qs = base_queryset.filter(daily_menu__date=today)
        total_sales_today = sum(
            (order.food_item.price if order.food_item else 0) + 
            sum(side.price for side in order.side_dishes.all())
            for order in orders_today_qs.select_related('food_item').prefetch_related('side_dishes')
        )
        pending_orders_total = base_queryset.filter(status__in=['PLACED', 'CONFIRMED']).count()
        top_foods_qs = FoodItem.objects
        if user.role == User.Role.COMPANY_ADMIN:
            top_foods_qs = top_foods_qs.filter(orders__user__company=user.company)
        top_foods = top_foods_qs.annotate(order_count=Count('orders')).order_by('-order_count')[:5]
        top_foods_data = [{'name': f.name, 'count': f.order_count} for f in top_foods]
        sales_data = base_queryset.filter(daily_menu__date__gte=seven_days_ago).annotate(date=F('daily_menu__date')).values('date').annotate(order_count=Count('id')).order_by('date')
        latest_pending_orders_qs = base_queryset.filter(status='PLACED').order_by('-created_at')[:5]
        latest_pending_orders_data = OrderReadSerializer(latest_pending_orders_qs, many=True).data
        stats = {
            'orders_today': orders_today_qs.count(),
            'pending_orders_total': pending_orders_total,
            'total_sales_today': total_sales_today,
            'top_5_foods': top_foods_data,
            'sales_last_7_days': list(sales_data),
            'latest_pending_orders': latest_pending_orders_data,
        }
        return Response(stats)


# [REWRITTEN] The AdminReportsView is now more robust and consistent with filters
class AdminReportsView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)

        try:
            start_date_str = request.query_params.get('from', thirty_days_ago.isoformat())
            end_date_str = request.query_params.get('to', today.isoformat())
            start_date = timezone.datetime.fromisoformat(start_date_str).date()
            end_date = timezone.datetime.fromisoformat(end_date_str).date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        company_id = request.query_params.get('companyId')

        # --- Base QuerySets ---
        base_orders_queryset = Order.objects.filter(daily_menu__date__range=(start_date, end_date), daily_menu__isnull=False)
        company_queryset = Company.objects.all()
        if company_id:
            base_orders_queryset = base_orders_queryset.filter(user__company_id=company_id)
            company_queryset = company_queryset.filter(id=company_id)

        # --- Summary Stats (Now correctly filtered) ---
        orders_today_qs = base_orders_queryset.filter(daily_menu__date=today)
        
        total_sales_today = Decimal('0.0')
        for order in orders_today_qs.select_related('food_item').prefetch_related('side_dishes'):
            if order.food_item:
                total_sales_today += order.food_item.price
            total_sales_today += sum(side.price for side in order.side_dishes.all())

        summary_data = {
            "orders_today": orders_today_qs.count(),
            "pending_orders_total": base_orders_queryset.filter(status__in=['PLACED', 'CONFIRMED']).count(),
            "total_sales_today": total_sales_today
        }
        
        # --- Other aggregations ---
        top_items_data = base_orders_queryset.values('food_item__name').annotate(
            name=F('food_item__name'),
            ordered=Count('id')
        ).order_by('-ordered').values('name', 'ordered')[:5]

        sales_by_date = defaultdict(lambda: {'orders': 0, 'revenue': Decimal('0.0')})
        orders_for_revenue = base_orders_queryset.select_related('food_item', 'daily_menu').prefetch_related('side_dishes')
        for order in orders_for_revenue:
            date_str = order.daily_menu.date.isoformat()
            sales_by_date[date_str]['orders'] += 1
            order_total = order.food_item.price if order.food_item else Decimal('0.0')
            order_total += sum(side.price for side in order.side_dishes.all())
            sales_by_date[date_str]['revenue'] += order_total
        sales_by_date_data = [{'date': date, **data} for date, data in sorted(sales_by_date.items())]

        company_stats_data = company_queryset.annotate(
            active_users=Count('employees', filter=Q(employees__is_active=True), distinct=True),
            orders=Count('employees__orders', filter=Q(employees__orders__daily_menu__date__range=(start_date, end_date)), distinct=True)
        ).values('id', 'name', 'active_users', 'orders')

        user_stats_data = {
            "total_users": User.objects.count(),
            "active_last_30_days": User.objects.filter(last_login__gte=(today - timedelta(days=30))).count()
        }

        response_data = {
            "summary": summary_data,
            "top_items": list(top_items_data),
            "sales_by_date": sales_by_date_data,
            "company_stats": list(company_stats_data),
            "user_stats": user_stats_data,
        }
        return Response(response_data)