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
from collections import defaultdict # [NEW] Import defaultdict for easier processing

from .models import Order
from users.models import User
from companies.models import Company
from menu.models import FoodItem
from core.permissions import IsSuperAdmin 
from .serializers import OrderReadSerializer


# --- FilterSet for the Order View ---

class OrderFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="daily_menu__date", lookup_expr='gte')
    end_date = filters.DateFilter(field_name="daily_menu__date", lookup_expr='lte')
    company_id = filters.NumberFilter(field_name='daily_menu__schedule__company_id')

    class Meta:
        model = Order
        fields = ['status', 'company_id', 'start_date', 'end_date']


# --- Admin ViewSet for All Orders ---

class AdminOrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Order.objects.select_related(
        'user',
        'food_item',
        'daily_menu__schedule__company'
    ).prefetch_related('side_dishes').all()
    serializer_class = OrderReadSerializer
    permission_classes = [IsSuperAdmin]
    filterset_class = OrderFilter


# --- APIViews for Reports and Dashboard ---

class DailyOrderSummaryView(APIView):
    permission_classes = [IsSuperAdmin]
    def get(self, request, *args, **kwargs):
        # This view is unchanged but included for completeness
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
    permission_classes = [IsSuperAdmin]
    def get(self, request, *args, **kwargs):
        # This view is unchanged but included for completeness
        today = timezone.now().date()
        orders_today = Order.objects.filter(daily_menu__date=today).count()
        pending_orders = Order.objects.filter(status__in=['PLACED', 'CONFIRMED']).count()
        top_foods = FoodItem.objects.annotate(order_count=Count('orders')).order_by('-order_count')[:5]
        top_foods_data = [{'name': f.name, 'count': f.order_count} for f in top_foods]
        stats = {'orders_today': orders_today, 'pending_orders_total': pending_orders, 'top_5_foods': top_foods_data}
        return Response(stats)


# --- Comprehensive Admin Reports View ---

class AdminReportsView(APIView):
    """
    Provides aggregated data for the admin reports page.
    [MODIFIED] This view is now rewritten to be more robust.
    """
    permission_classes = [IsSuperAdmin]

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)

        # 1. Parse filters
        try:
            start_date_str = request.query_params.get('from', thirty_days_ago.isoformat())
            end_date_str = request.query_params.get('to', today.isoformat())
            start_date = timezone.datetime.fromisoformat(start_date_str).date()
            end_date = timezone.datetime.fromisoformat(end_date_str).date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        company_id = request.query_params.get('companyId')

        # 2. Base QuerySets
        base_orders_queryset = Order.objects.filter(daily_menu__date__range=(start_date, end_date), daily_menu__isnull=False)
        company_queryset = Company.objects.all()
        if company_id:
            base_orders_queryset = base_orders_queryset.filter(user__company_id=company_id)
            company_queryset = company_queryset.filter(id=company_id)

        # 3. Aggregations (Now done in a safer way)

        # --- Summary Stats ---
        orders_today_qs = Order.objects.filter(daily_menu__date=today)
        if company_id:
            orders_today_qs = orders_today_qs.filter(user__company_id=company_id)
        
        total_sales_today = Decimal('0.0')
        # Eager load related items to prevent many small queries
        for order in orders_today_qs.select_related('food_item').prefetch_related('side_dishes'):
            if order.food_item:
                total_sales_today += order.food_item.price
            total_sales_today += sum(side.price for side in order.side_dishes.all())

        summary_data = {
            "orders_today": orders_today_qs.count(),
            "pending_orders_total": base_orders_queryset.filter(status__in=['PLACED', 'CONFIRMED']).count(),
            "total_sales_today": total_sales_today
        }

        # --- Top Items (This query is generally safe) ---
        top_items_data = base_orders_queryset.values('food_item__id', 'food_item__name').annotate(
            foodId=F('food_item__id'),
            name=F('food_item__name'),
            ordered=Count('food_item')
        ).order_by('-ordered')[:5]

        # --- Sales by Date (Calculated in Python for reliability) ---
        sales_by_date = defaultdict(lambda: {'orders': 0, 'revenue': Decimal('0.0')})
        
        orders_for_revenue = base_orders_queryset.select_related('food_item', 'daily_menu').prefetch_related('side_dishes')
        
        for order in orders_for_revenue:
            date_str = order.daily_menu.date.isoformat()
            sales_by_date[date_str]['orders'] += 1
            
            order_total = order.food_item.price if order.food_item else Decimal('0.0')
            order_total += sum(side.price for side in order.side_dishes.all())
            sales_by_date[date_str]['revenue'] += order_total

        sales_by_date_data = [{'date': date, **data} for date, data in sorted(sales_by_date.items())]

        # --- Company & User Stats (These queries are safe) ---
        company_stats_data = company_queryset.annotate(
            active_users=Count('employees', filter=Q(employees__is_active=True), distinct=True),
            orders=Count('employees__orders', filter=Q(employees__orders__daily_menu__date__range=(start_date, end_date)), distinct=True)
        ).values('id', 'name', 'active_users', 'orders')

        user_stats_data = {
            "total_users": User.objects.count(),
            "active_last_30_days": User.objects.filter(last_login__gte=(today - timedelta(days=30))).count()
        }

        # --- 4. Response ---
        response_data = {
            "summary": summary_data,
            "top_items": list(top_items_data),
            "sales_by_date": sales_by_date_data,
            "company_stats": list(company_stats_data),
            "user_stats": user_stats_data,
        }

        return Response(response_data)