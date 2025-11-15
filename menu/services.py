# menu/services.py (فایل جدید)

from schedules.models import DailyMenu

def batch_save_daily_menus(schedule_id, items):
    """
    Saves multiple daily menus for a schedule in a batch.
    """
    for item in items:
        daily_menu_id = item.get('dailyMenuId')
        payload = item.get('payload')
        
        if not payload:
            continue
            
        date = payload.get('date')
        food_ids = payload.get('available_foods', [])
        side_ids = payload.get('available_sides', [])
        
        # اگر هیچ غذایی انتخاب نشده بود، منوی آن روز را حذف می‌کنیم (در صورت وجود)
        if not food_ids and daily_menu_id:
            DailyMenu.objects.filter(id=daily_menu_id, schedule_id=schedule_id).delete()
            continue
        
        # اگر غذایی وجود داشت، ایجاد یا به‌روزرسانی می‌کنیم
        if food_ids:
            daily_menu, created = DailyMenu.objects.update_or_create(
                id=daily_menu_id,
                schedule_id=schedule_id,
                date=date,
                defaults={}
            )
            daily_menu.available_foods.set(food_ids)
            daily_menu.available_sides.set(side_ids)