# companies/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Company
from .serializers import CompanySerializer
from core.permissions import IsSuperAdmin
from schedules.models import Schedule, DailyMenu # ایمپورت‌های جدید
from menu.services import batch_save_daily_menus # ایمپورت سرویس جدید

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all().order_by('name')
    serializer_class = CompanySerializer
    permission_classes = [IsSuperAdmin]

    # [کد جدید] یک action سفارشی برای ایجاد/به‌روزرسانی جامع اضافه می‌کنیم
    def _handle_custom_schedule(self, company_instance, request_data):
        custom_schedule_data = request_data.get('new_schedule')
        menu_state = request_data.get('menu_state')

        if not custom_schedule_data or not menu_state:
            return

        # 1. ایجاد یا به‌روزرسانی برنامه غذایی
        schedule, created = Schedule.objects.update_or_create(
            company=company_instance,
            defaults={
                'name': custom_schedule_data.get('name', f'منوی اختصاصی {company_instance.name}'),
                'start_date': custom_schedule_data.get('start_date'),
                'end_date': custom_schedule_data.get('end_date'),
                'is_active': True,
            }
        )
        
        # 2. فعال کردن این برنامه برای شرکت
        company_instance.active_schedule = schedule
        company_instance.save()

        # 3. تبدیل menu_state به فرمت قابل استفاده برای سرویس batch_save
        payload_items = []
        existing_menus = {menu.date.isoformat(): menu for menu in schedule.daily_menus.all()}

        for date_str, selections in menu_state.items():
            food_ids = [fid for fid in selections.get('foods', []) if fid is not None]
            side_ids = selections.get('sides', [])
            
            payload = {
                'date': date_str,
                'available_foods': food_ids,
                'available_sides': side_ids,
            }
            
            existing_menu = existing_menus.get(date_str)
            payload_items.append({
                'dailyMenuId': existing_menu.id if existing_menu else None,
                'payload': payload
            })
        
        # 4. ذخیره دسته‌ای منوهای روزانه
        if payload_items:
            batch_save_daily_menus(schedule.id, payload_items)


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_instance = serializer.save()
        
        # [کد جدید] پردازش منوی اختصاصی پس از ایجاد شرکت
        self._handle_custom_schedule(company_instance, request.data)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        company_instance = serializer.save()

        # [کد جدید] پردازش منوی اختصاصی پس از به‌روزرسانی شرکت
        self._handle_custom_schedule(company_instance, request.data)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)