# back/core/management/commands/seed_data.py

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

# Import all necessary models
from companies.models import Company, CompanyConfiguration
from contracts.models import Contract
from menu.models import FoodCategory, FoodItem, SideDish
from orders.models import Order
from schedules.models import Schedule, DailyMenu
from users.models import User
from wallets.models import Wallet, Transaction
from discounts.models import DiscountCode, DynamicMenuDiscount, DiscountCodeUsage
from surveys.models import Survey

class Command(BaseCommand):
    """
    یک دستور مدیریتی جامع برای پر کردن دیتابیس با داده‌های تستی واقعی و متنوع.
    این نسخه تمام قابلیت‌های اصلی سیستم از جمله کاربران، شرکت‌ها، منوها، سفارشات،
    کیف پول، قراردادها، تخفیف‌ها و نظرسنجی‌ها را پوشش می‌دهد.
    """
    help = 'Populates the database with comprehensive and realistic test data.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("====================================================="))
        self.stdout.write(self.style.SUCCESS("=== شروع فرآیند جامع پر کردن دیتابیس با داده‌های تستی... ==="))
        self.stdout.write(self.style.SUCCESS("====================================================="))
        
        self.fake = Faker('fa_IR')
        self.today = timezone.now().date()

        try:
            with transaction.atomic():
                self.clear_data()
                self.create_super_admin()
                self.create_menu_items()
                self.create_discounts()
                self.create_default_schedule()

                # پروفایل‌های متنوع برای تست سناریوهای مختلف
                company_profiles = [
                    {
                        "name": "شرکت فناوران نوین", 
                        "is_custom_schedule": True,
                        "payment_model": Company.PaymentModel.ONLINE,
                        "discount_type": Company.DiscountType.PERCENTAGE,
                        "discount_value": Decimal('15.00')
                    },
                    {
                        "name": "گروه صنعتی پولاد", 
                        "is_custom_schedule": False,
                        "payment_model": Company.PaymentModel.INVOICE,
                        "discount_type": Company.DiscountType.FIXED,
                        "discount_value": Decimal('20000.00')
                    },
                    {
                        "name": "آژانس خلاقیت زیبا",
                        "is_custom_schedule": False,
                        "payment_model": Company.PaymentModel.ONLINE,
                        "calculation_type": Company.CalculationType.AVERAGE,
                        "average_price": Decimal('150000.00'),
                        "status": Company.CompanyStatus.DRAFT
                    },
                ]

                for index, profile in enumerate(company_profiles):
                    self.create_company_and_related_data(index + 1, profile)

                self.stdout.write(self.style.SUCCESS("\n=============================================="))
                self.stdout.write(self.style.SUCCESS("=== عملیات با موفقیت به پایان رسید! ==="))
                self.stdout.write(self.style.SUCCESS("=============================================="))
                self.stdout.write("\nLogin with: superadmin / superpassword123")
                self.stdout.write("Company Admins: admin_co1, admin_co2, etc. / password123")
                self.stdout.write("Employees: user1_co1, user2_co1, etc. / password123")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nخطا در حین اجرای عملیات: {e}"))
            import traceback
            traceback.print_exc()
            self.stdout.write(self.style.ERROR("تمام تغییرات به حالت اولیه بازگردانده شد."))

    def clear_data(self):
        self.stdout.write("\n۱. پاکسازی داده‌های قبلی...")
        # حذف به ترتیب وابستگی معکوس
        Survey.objects.all().delete()
        DiscountCodeUsage.objects.all().delete()
        DiscountCode.objects.all().delete()
        DynamicMenuDiscount.objects.all().delete()
        Order.objects.all().delete()
        DailyMenu.objects.all().delete()
        Schedule.objects.all().delete()
        Transaction.objects.all().delete()
        Contract.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Company.objects.all().delete()
        SideDish.objects.all().delete()
        FoodItem.objects.all().delete()
        FoodCategory.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("   -> داده‌های قبلی با موفقیت پاک شدند."))

    def create_super_admin(self):
        self.stdout.write("\n۲. ایجاد کاربر ادمین کل...")
        self.super_admin, _ = User.objects.update_or_create(
            username="superadmin",
            defaults={
                'email': "superadmin@example.com", 'role': User.Role.SUPER_ADMIN,
                'first_name': 'ادمین', 'last_name': 'کل',
                'is_staff': True, 'is_superuser': True
            }
        )
        if not self.super_admin.has_usable_password():
            self.super_admin.set_password("superpassword123")
            self.super_admin.save()
        self.stdout.write(self.style.SUCCESS("   -> کاربر 'superadmin' با رمز 'superpassword123' ایجاد/به‌روزرسانی شد."))

    def create_menu_items(self):
        self.stdout.write("\n۳. ایجاد آیتم‌های منو...")
        main_cat = FoodCategory.objects.create(name="غذای اصلی")
        salad_cat = FoodCategory.objects.create(name="سالاد و پیش‌غذا")
        
        self.food_items = {
            "kebab": FoodItem.objects.create(name="چلوکباب کوبیده", price=Decimal('220000'), category=main_cat),
            "qorme": FoodItem.objects.create(name="قورمه سبزی", price=Decimal('185000'), category=main_cat),
            "jooje": FoodItem.objects.create(name="جوجه کباب", price=Decimal('210000'), category=main_cat),
            "zereshk": FoodItem.objects.create(name="زرشک پلو با مرغ", price=Decimal('195000'), category=main_cat),
            "caesar": FoodItem.objects.create(name="سالاد سزار", price=Decimal('150000'), category=salad_cat),
        }
        self.side_dishes = [
            SideDish.objects.create(name="سالاد شیرازی", price=Decimal('35000')),
            SideDish.objects.create(name="ماست و خیار", price=Decimal('30000')),
            SideDish.objects.create(name="نوشابه", price=Decimal('20000')),
        ]
        self.stdout.write(self.style.SUCCESS(f"   -> {len(self.food_items)} غذا و {len(self.side_dishes)} کنارغذا ایجاد شد."))

    def create_discounts(self):
        self.stdout.write("\n۴. ایجاد تخفیف‌ها...")
        now = timezone.now()
        
        self.active_codes = [
            DiscountCode.objects.create(
                code="BEHESHTI", discount_type='PERCENTAGE', value=Decimal('30'),
                max_usage_count=50, start_date=now - timedelta(days=10), end_date=now + timedelta(days=20),
                is_active=True, scope='PUBLIC', description="تخفیف عمومی ۳۰ درصدی بهشتی"
            ),
            DiscountCode.objects.create(
                code="EHSANFOOD", discount_type='FIXED_AMOUNT', value=Decimal('25000'),
                start_date=now - timedelta(days=5), end_date=now + timedelta(days=25),
                is_active=True, scope='PUBLIC', description="تخفیف ۲۵ هزار تومانی",
                min_order_amount=Decimal('100000.00')
            )
        ]
        DiscountCode.objects.create(
            code="EXPIRED", discount_type='PERCENTAGE', value=Decimal('10'),
            start_date=now - timedelta(days=30), end_date=now - timedelta(days=1),
            is_active=False, scope='PUBLIC', description="کد منقضی شده"
        )
        self.stdout.write(self.style.SUCCESS("   -> ۳ کد تخفیف (۲ فعال، ۱ بایگانی) ایجاد شد."))

        dynamic_active = DynamicMenuDiscount.objects.create(
            name="تخفیف جوجه کباب", discount_percentage=Decimal('15.00'),
            start_date=now, end_date=now + timedelta(days=30),
            is_active=True, show_on_menu=True
        )
        dynamic_active.applicable_items.add(self.food_items["jooje"])
        self.stdout.write(self.style.SUCCESS("   -> ۱ تخفیف داینامیک منو فعال برای جوجه کباب ایجاد شد."))


    def create_default_schedule(self):
        self.stdout.write("\n۵. ایجاد برنامه غذایی پیش‌فرض...")
        self.default_schedule = Schedule.objects.create(
            name="برنامه غذایی پیش‌فرض عمومی", company=None,
            start_date=self.today - timedelta(days=30),
            end_date=self.today + timedelta(days=60), is_active=True
        )
        foods = list(self.food_items.values())
        current_date = self.default_schedule.start_date
        while current_date <= self.default_schedule.end_date:
            if current_date.weekday() not in [4, 5]: # پنج‌شنبه و جمعه تعطیل
                daily_menu = DailyMenu.objects.create(schedule=self.default_schedule, date=current_date)
                daily_menu.available_foods.set(random.sample(foods, k=random.randint(2, 4)))
                daily_menu.available_sides.set(random.sample(self.side_dishes, k=random.randint(1, 3)))
            current_date += timedelta(days=1)
        self.stdout.write(self.style.SUCCESS("   -> برنامه پیش‌فرض برای ۹۰ روز ایجاد شد."))

    def create_company_and_related_data(self, index, profile):
        self.stdout.write(f"\n۶.{index}. ایجاد داده‌ها برای «{profile['name']}»...")
        company = Company.objects.create(
            name=profile["name"],
            contact_person=self.fake.name(),
            contact_phone=self.fake.phone_number(),
            address=self.fake.address(),
            status=profile.get("status", Company.CompanyStatus.PUBLISHED),
            payment_model=profile.get("payment_model", Company.PaymentModel.ONLINE),
            discount_type=profile.get("discount_type", Company.DiscountType.NONE),
            discount_value=profile.get("discount_value", Decimal('0.00')),
            calculation_type=profile.get("calculation_type", Company.CalculationType.FLUID),
            average_price=profile.get("average_price", Decimal('0.00')),
        )
        Contract.objects.create(company=company, start_date=self.today - timedelta(days=30), end_date=self.today + timedelta(days=365), status=Contract.ContractStatus.ACTIVE)
        
        wallet = company.wallet
        deposit_amount = Decimal('50000000.00')
        wallet.balance = deposit_amount
        wallet.save()
        Transaction.objects.create(wallet=wallet, user=self.super_admin, transaction_type=Transaction.TransactionType.DEPOSIT, amount=deposit_amount, description="واریز اولیه توسط ادمین کل")
        self.stdout.write(self.style.SUCCESS(f"   -> کیف پول شرکت با {deposit_amount:,.0f} تومان شارژ شد."))

        admin = User.objects.create_user(username=f"admin_co{index}", password="password123", first_name=self.fake.first_name(), last_name=self.fake.last_name(), role=User.Role.COMPANY_ADMIN, company=company)
        employees = [User.objects.create_user(username=f"user{i+1}_co{index}", password="password123", first_name=self.fake.first_name(), last_name=self.fake.last_name(), role=User.Role.EMPLOYEE, company=company) for i in range(5)]
        
        for emp in employees[:3]: # تخصیص اعتبار به ۳ کارمند
            budget_amount = Decimal(random.choice(['500000', '1000000', '1500000']))
            emp.budget = budget_amount
            emp.save()
            wallet.balance -= budget_amount
            wallet.save()
            Transaction.objects.create(wallet=wallet, user=admin, transaction_type=Transaction.TransactionType.BUDGET_ALLOCATION, amount=-budget_amount, description=f"تخصیص اعتبار به {emp.username}")
        
        self.stdout.write(self.style.SUCCESS(f"   -> {len(employees)} کارمند و ۱ ادمین شرکت ایجاد و به برخی اعتبار تخصیص داده شد."))
        
        if profile.get("is_custom_schedule"):
            self.stdout.write("   -> ایجاد و تخصیص برنامه غذایی اختصاصی...")
            schedule = Schedule.objects.create(name=f"برنامه اختصاصی {company.name}", company=company, start_date=self.today - timedelta(days=30), end_date=self.today + timedelta(days=30), is_active=True)
            foods = list(self.food_items.values())
            current_date = schedule.start_date
            while current_date <= schedule.end_date:
                if current_date.weekday() not in [4, 5]:
                    daily_menu = DailyMenu.objects.create(schedule=schedule, date=current_date)
                    # [اصلاح کلیدی] این خط برای ایجاد تنوع بیشتر تغییر کرد
                    daily_menu.available_foods.set(random.sample(foods, k=random.randint(2, 4)))
                    daily_menu.available_sides.set(random.sample(self.side_dishes, k=2))
                current_date += timedelta(days=1)
            company.active_schedule = schedule
        else:
             self.stdout.write("   -> تخصیص برنامه غذایی پیش‌فرض...")
             company.active_schedule = self.default_schedule
        company.save()
        
        self.create_orders_for_company(company, employees)

    def create_orders_for_company(self, company, employees):
        self.stdout.write("   -> ایجاد سفارشات گذشته و آینده...")
        
        # 1. سفارشات گذشته (تحویل شده و قابل نظرسنجی)
        past_menus = DailyMenu.objects.filter(schedule=company.active_schedule, date__lt=self.today, date__gte=self.today - timedelta(days=15)).prefetch_related('available_foods')
        order_count = 0
        for employee in employees:
            for _ in range(random.randint(3, 7)):
                if not past_menus.exists(): continue
                daily_menu = random.choice(past_menus)
                if daily_menu.available_foods.exists() and not Order.objects.filter(user=employee, daily_menu=daily_menu).exists():
                    order = Order.objects.create(user=employee, daily_menu=daily_menu, food_item=random.choice(list(daily_menu.available_foods.all())), status=Order.OrderStatus.DELIVERED)
                    order.side_dishes.set(random.sample(self.side_dishes, k=random.randint(0, 2)))
                    
                    # اعمال کد تخفیف به صورت تصادفی
                    if random.random() < 0.4:
                        code_to_use = random.choice(self.active_codes)
                        if DiscountCodeUsage.objects.filter(discount_code=code_to_use, user=employee).count() < code_to_use.max_usage_per_user:
                            DiscountCodeUsage.objects.create(discount_code=code_to_use, user=employee, order=order)
                            code_to_use.usage_count += 1; code_to_use.save()
                    
                    # محاسبه قیمت نهایی (مهم)
                    order.calculate_and_save_prices()
                    order_count += 1
                    
                    # ثبت نظرسنجی به صورت تصادفی
                    if random.random() < 0.5:
                        Survey.objects.create(order=order, user=employee, rating=random.randint(3, 5), comment=self.fake.sentence())
        
        # 2. سفارشات آینده (ثبت شده)
        future_menus = DailyMenu.objects.filter(schedule=company.active_schedule, date__gt=self.today, date__lte=self.today + timedelta(days=7)).prefetch_related('available_foods')
        for employee in employees:
            if not future_menus.exists(): continue
            daily_menu = random.choice(future_menus)
            if daily_menu.available_foods.exists() and not Order.objects.filter(user=employee, daily_menu=daily_menu).exists():
                order = Order.objects.create(user=employee, daily_menu=daily_menu, food_item=random.choice(list(daily_menu.available_foods.all())), status=Order.OrderStatus.PLACED)
                order.calculate_and_save_prices() # محاسبه قیمت نهایی
                order_count += 1
        
        if order_count > 0:
            self.stdout.write(self.style.SUCCESS(f"      -> {order_count} سفارش نمونه در وضعیت‌های مختلف ایجاد شد."))