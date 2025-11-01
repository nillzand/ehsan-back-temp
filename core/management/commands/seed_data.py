# core/management/commands/seed_data.py

import random
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

# وارد کردن تمام مدل‌های مورد نیاز
from companies.models import Company
from contracts.models import Contract
from menu.models import FoodCategory, FoodItem, SideDish
from orders.models import Order
from schedules.models import Schedule, DailyMenu
from users.models import User
from wallets.models import Wallet, Transaction


class Command(BaseCommand):
    """
    یک دستور مدیریت جنگو برای پر کردن پایگاه داده با داده‌های آزمایشی واقعی فارسی.
    """
    help = 'پایگاه داده را با داده‌های اولیه برای شرکت‌ها، کاربران، منوها، سفارشات و غیره پر می‌کند.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("==============================================="))
        self.stdout.write(self.style.SUCCESS("=== شروع فرآیند پر کردن پایگاه داده (Seeding) ==="))
        self.stdout.write(self.style.SUCCESS("==============================================="))
        
        # استفاده از Faker برای تولید داده‌های فارسی
        self.fake = Faker('fa_IR')
        self.today = timezone.now().date()

        try:
            # استفاده از تراکنش اتمی برای اطمینان از یکپارچگی داده‌ها
            with transaction.atomic():
                self.clear_data()
                self.create_menu_items()
                self.create_super_admin()
                self.create_default_schedule()

                # ایجاد 3 شرکت به همراه تمام داده‌های وابسته
                for i in range(3):
                    self.create_company_and_related_data(i + 1)

                self.stdout.write(self.style.SUCCESS("\n=============================================="))
                self.stdout.write(self.style.SUCCESS("=== پر کردن پایگاه داده با موفقیت کامل شد! ==="))
                self.stdout.write(self.style.SUCCESS("=============================================="))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nخطایی در حین پر کردن پایگاه داده رخ داد: {e}"))
            self.stdout.write(self.style.ERROR("عملیات به طور کامل بازگردانده (Rollback) شد."))

    def clear_data(self):
        """ تمام داده‌های مرتبط را پاک می‌کند به جز کاربران ادمین کل. """
        self.stdout.write("\n1. پاک‌سازی داده‌های موجود...")
        Order.objects.all().delete()
        DailyMenu.objects.all().delete()
        Schedule.objects.all().delete()
        Transaction.objects.all().delete()
        Contract.objects.all().delete()
        # کاربران غیر سوپرادمین حذف می‌شوند
        User.objects.filter(is_superuser=False).delete()
        Wallet.objects.all().delete()
        Company.objects.all().delete()
        SideDish.objects.all().delete()
        FoodItem.objects.all().delete()
        FoodCategory.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("   -> داده‌های قبلی با موفقیت پاک شدند."))

    def create_menu_items(self):
        """ دسته‌بندی‌ها، غذاها و کنارغذاهای اولیه را ایجاد می‌کند. """
        self.stdout.write("\n2. ایجاد آیتم‌های منو (غذاها، دسرها و کنارغذاها)...")
        main_course_cat = FoodCategory.objects.create(name="غذای اصلی", description="غذاهای اصلی خوشمزه و متنوع.")
        dessert_cat = FoodCategory.objects.create(name="دسر", description="دسرهای شیرین برای پایان وعده غذایی.")
        
        self.food_items = [
            FoodItem.objects.create(name="چلوکباب کوبیده", description="دو سیخ کباب کوبیده گوشت گوسفندی به همراه برنج ایرانی", price=Decimal('180000'), category=main_course_cat),
            FoodItem.objects.create(name="قورمه سبزی", description="خورشت سبزیجات معطر با گوشت گوسفندی و لوبیا قرمز به همراه برنج", price=Decimal('165000'), category=main_course_cat),
            FoodItem.objects.create(name="جوجه کباب", description="یک سیخ جوجه کباب زعفرانی به همراه برنج ایرانی", price=Decimal('170000'), category=main_course_cat),
            FoodItem.objects.create(name="زرشک پلو با مرغ", description="ران مرغ سرخ شده به همراه برنج زعفرانی و زرشک", price=Decimal('150000'), category=main_course_cat),
            FoodItem.objects.create(name="قیمه بادمجان", description="خورشت قیمه با لپه و بادمجان سرخ شده", price=Decimal('160000'), category=main_course_cat),
            FoodItem.objects.create(name="کشک بادمجان", description="غذای سنتی با بادمجان، کشک، نعنا داغ و گردو", price=Decimal('110000'), category=main_course_cat),
            FoodItem.objects.create(name="شله زرد", description="دسر سنتی ایرانی با برنج، زعفران و شکر", price=Decimal('45000'), category=dessert_cat),
        ]
        self.side_dishes = [
            SideDish.objects.create(name="سالاد شیرازی", description="خیار، گوجه و پیاز خرد شده با آبغوره", price=Decimal('30000')),
            SideDish.objects.create(name="ماست و خیار", description="ماست چکیده به همراه خیار و نعنا خشک", price=Decimal('25000')),
            SideDish.objects.create(name="زیتون پرورده", description="زیتون با رب انار، گردو و سبزیجات معطر", price=Decimal('40000')),
            SideDish.objects.create(name="دوغ", description="نوشیدنی سنتی بر پایه ماست", price=Decimal('20000')),
        ]
        self.stdout.write(self.style.SUCCESS("   -> آیتم‌های منو با موفقیت ایجاد شدند."))

    def create_super_admin(self):
        """ کاربر ادمین کل را ایجاد یا به‌روزرسانی می‌کند. """
        self.stdout.write("\n3. بررسی و ایجاد کاربر ادمین کل (superadmin)...")
        self.super_admin, created = User.objects.update_or_create(
            username="superadmin",
            defaults={
                'email': "superadmin@example.com",
                'role': User.Role.SUPER_ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'budget': Decimal('0.00') # ادمین کل بودجه شخصی ندارد
            }
        )
        if created:
            self.super_admin.set_password("superpassword123")
            self.super_admin.save()
            self.stdout.write(self.style.SUCCESS("   -> کاربر 'superadmin' با رمز 'superpassword123' ایجاد شد."))
        else:
            self.stdout.write(self.style.WARNING("   -> کاربر 'superadmin' از قبل وجود داشت. اطلاعات آن به‌روزرسانی شد."))

    def create_default_schedule(self):
        """ یک برنامه غذایی پیش‌فرض و سراسری برای 60 روز آینده ایجاد می‌کند. """
        self.stdout.write("\n4. ایجاد برنامه غذایی پیش‌فرض سراسری...")
        self.default_schedule = Schedule.objects.create(
            name="برنامه غذایی پیش‌فرض سراسری",
            company=None, 
            start_date=self.today - timedelta(days=30), # شامل روزهای گذشته برای سفارشات نمونه
            end_date=self.today + timedelta(days=60),
            is_active=True
        )
        main_foods = [food for food in self.food_items if food.category.name == "غذای اصلی"]
        current_date = self.default_schedule.start_date
        while current_date <= self.default_schedule.end_date:
            if current_date.weekday() not in [4, 5]: # پنجشنبه و جمعه را رد کن
                daily_menu = DailyMenu.objects.create(schedule=self.default_schedule, date=current_date)
                daily_menu.available_foods.set(random.sample(main_foods, k=random.randint(2, 4)))
                daily_menu.available_sides.set(random.sample(self.side_dishes, k=random.randint(1, 3)))
            current_date += timedelta(days=1)
        self.stdout.write(self.style.SUCCESS("   -> برنامه غذایی پیش‌فرض برای ۹۰ روز (شامل گذشته) ایجاد شد."))

    def create_company_and_related_data(self, index):
        """ یک شرکت و تمام داده‌های مربوط به آن (قرارداد، کیف پول، کاربران، سفارشات) را ایجاد می‌کند. """
        company_name = f"{self.fake.company()} شعبه {index}"
        self.stdout.write(f"\n5.{index}. ایجاد داده برای شرکت «{company_name}»...")

        company = Company.objects.create(
            name=company_name,
            contact_person=self.fake.name(),
            contact_phone=self.fake.phone_number(),
            address=self.fake.address()
        )
        Contract.objects.create(company=company, start_date=self.today - timedelta(days=30), end_date=self.today + timedelta(days=365), status=Contract.ContractStatus.ACTIVE)
        
        # واریز اولیه به کیف پول شرکت و ثبت تراکنش
        wallet = company.wallet
        deposit_amount = Decimal('50000000.00')
        wallet.balance = deposit_amount
        wallet.save()
        Transaction.objects.create(wallet=wallet, user=self.super_admin, transaction_type=Transaction.TransactionType.DEPOSIT, amount=deposit_amount, description=f"واریز اولیه توسط {self.super_admin.username}.")
        self.stdout.write(f"   -> کیف پول شرکت با مبلغ {deposit_amount:,.0f} تومان شارژ شد.")

        # ایجاد کاربران برای شرکت
        company_admin = User.objects.create_user(username=f"admin_co_{index}", password="password123", first_name=self.fake.first_name(), last_name=self.fake.last_name(), role=User.Role.COMPANY_ADMIN, company=company)
        employees = [User.objects.create_user(username=f"user{i}_co{index}", password="password123", first_name=self.fake.first_name(), last_name=self.fake.last_name(), role=User.Role.EMPLOYEE, company=company) for i in range(5)]
        
        # تخصیص بودجه به کارمندان و ثبت تراکنش
        allocation_amount = Decimal('1500000.00')
        for employee in employees:
            wallet.balance -= allocation_amount
            employee.budget += allocation_amount
            employee.save()
            Transaction.objects.create(wallet=wallet, user=company_admin, transaction_type=Transaction.TransactionType.BUDGET_ALLOCATION, amount=-allocation_amount, description=f"تخصیص اعتبار به {employee.username}.")
        wallet.save()
        self.stdout.write(f"   -> ادمین شرکت و {len(employees)} کارمند ایجاد شدند و به هرکدام {allocation_amount:,.0f} تومان اعتبار تخصیص داده شد.")

        # اختصاص دادن برنامه غذایی
        if index == 1: # اختصاص برنامه غذایی اختصاصی به شرکت اول
            self.stdout.write(f"   -> ایجاد و تخصیص برنامه غذایی اختصاصی...")
            schedule = Schedule.objects.create(name=f"برنامه اختصاصی {company.name}", company=company, start_date=self.today - timedelta(days=30), end_date=self.today + timedelta(days=30), is_active=True)
            main_foods = [food for food in self.food_items if food.category.name == "غذای اصلی"]
            current_date = schedule.start_date
            while current_date <= schedule.end_date:
                if current_date.weekday() not in [4, 5]:
                    daily_menu = DailyMenu.objects.create(schedule=schedule, date=current_date)
                    daily_menu.available_foods.set(random.sample(main_foods, k=2))
                current_date += timedelta(days=1)
            company.active_schedule = schedule
        else: # اختصاص برنامه پیش‌فرض به بقیه
             self.stdout.write(f"   -> تخصیص برنامه غذایی پیش‌فرض سراسری...")
             company.active_schedule = self.default_schedule
        company.save()
        
        # [جدید] ایجاد سفارشات گذشته برای کارمندان این شرکت
        self.create_past_orders_for_company(company, employees)

    def create_past_orders_for_company(self, company, employees):
        """ برای هر کارمند، تعدادی سفارش در 15 روز گذشته ثبت می‌کند. """
        self.stdout.write(f"   -> ایجاد سفارشات گذشته برای گزارش‌گیری...")
        # منوهای روزانه گذشته که برای این شرکت فعال بوده‌اند را پیدا کن
        past_menus = DailyMenu.objects.filter(
            schedule=company.active_schedule, 
            date__lt=self.today,
            date__gte=self.today - timedelta(days=15)
        ).prefetch_related('available_foods', 'available_sides')

        if not past_menus.exists():
            self.stdout.write(self.style.WARNING("      -> منوی گذشته‌ای برای ایجاد سفارش نمونه یافت نشد."))
            return

        order_count = 0
        for employee in employees:
            # برای هر کارمند بین 3 تا 7 سفارش نمونه ایجاد کن
            for _ in range(random.randint(3, 7)):
                # یک منوی رندوم از گذشته انتخاب کن
                daily_menu = random.choice(past_menus)
                available_foods = list(daily_menu.available_foods.all())
                available_sides = list(daily_menu.available_sides.all())
                
                if available_foods:
                    # یک غذای اصلی و چند کنارغذا به صورت رندوم انتخاب کن
                    food_item = random.choice(available_foods)
                    side_dishes_sample = random.sample(available_sides, k=random.randint(0, len(available_sides)))
                    
                    # اگر این کارمند قبلاً در این روز سفارش نداشته، سفارش را ایجاد کن
                    if not Order.objects.filter(user=employee, daily_menu=daily_menu).exists():
                        order = Order.objects.create(
                            user=employee,
                            daily_menu=daily_menu,
                            food_item=food_item,
                            status=random.choice([Order.OrderStatus.DELIVERED, Order.OrderStatus.CONFIRMED]) # وضعیت‌های متنوع
                        )
                        order.side_dishes.set(side_dishes_sample)
                        order_count += 1
        
        if order_count > 0:
            self.stdout.write(self.style.SUCCESS(f"      -> {order_count} سفارش نمونه در گذشته ایجاد شد."))