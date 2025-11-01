# core/management/commands/seed_data.py

import random
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

# Import all necessary models
from companies.models import Company
from contracts.models import Contract
from menu.models import FoodCategory, FoodItem, SideDish
from orders.models import Order
from schedules.models import Schedule, DailyMenu
from users.models import User
from wallets.models import Wallet, Transaction


class Command(BaseCommand):
    """
    A Django management command to seed the database with realistic Persian test data.
    """
    help = 'پایگاه داده را با داده‌های اولیه برای شرکت‌ها، کاربران، منوها و غیره پر می‌کند.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("==============================================="))
        self.stdout.write(self.style.SUCCESS("=== شروع فرآیند پر کردن پایگاه داده (Seeding) ==="))
        self.stdout.write(self.style.SUCCESS("==============================================="))
        fake = Faker('fa_IR')

        try:
            with transaction.atomic():
                self.clear_data()
                self.create_menu_items()
                self.create_super_admin()
                self.create_default_schedule()

                for i in range(3):
                    self.create_company_and_related_data(i + 1, fake)

                self.stdout.write(self.style.SUCCESS("\n=============================================="))
                self.stdout.write(self.style.SUCCESS("=== پر کردن پایگاه داده با موفقیت کامل شد! ==="))
                self.stdout.write(self.style.SUCCESS("=============================================="))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nخطایی در حین پر کردن پایگاه داده رخ داد: {e}"))
            self.stdout.write(self.style.ERROR("عملیات به طور کامل بازگردانده (Rollback) شد."))

    def clear_data(self):
        """ Clears all data from the relevant models except for superusers. """
        self.stdout.write("\n1. پاک‌سازی داده‌های موجود...")
        Order.objects.all().delete()
        DailyMenu.objects.all().delete()
        Schedule.objects.all().delete()
        Transaction.objects.all().delete()
        Contract.objects.all().delete()
        Wallet.objects.all().delete()
        Company.objects.all().delete()
        SideDish.objects.all().delete()
        FoodItem.objects.all().delete()
        FoodCategory.objects.all().delete()
        # [IMPROVED] Only deletes non-superuser users
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS("   -> داده‌های قبلی با موفقیت پاک شدند."))

    def create_menu_items(self):
        """ Creates food categories, food items, and side dishes in Persian. """
        self.stdout.write("\n2. ایجاد آیتم‌های منو (غذاها، دسرها و کنارغذاها)...")
        main_course_cat = FoodCategory.objects.create(name="غذای اصلی", description="غذاهای اصلی خوشمزه و متنوع.")
        dessert_cat = FoodCategory.objects.create(name="دسر", description="دسرهای شیرین برای پایان وعده غذایی.")
        
        self.food_items = [
            FoodItem.objects.create(name="چلوکباب کوبیده", description="دو سیخ کباب کوبیده گوشت گوسفندی به همراه برنج ایرانی", price=Decimal('150000'), category=main_course_cat),
            FoodItem.objects.create(name="قورمه سبزی", description="خورشت سبزیجات معطر با گوشت گوسفندی و لوبیا قرمز به همراه برنج", price=Decimal('135000'), category=main_course_cat),
            FoodItem.objects.create(name="جوجه کباب", description="یک سیخ جوجه کباب زعفرانی به همراه برنج ایرانی", price=Decimal('140000'), category=main_course_cat),
            FoodItem.objects.create(name="زرشک پلو با مرغ", description="ران مرغ سرخ شده به همراه برنج زعفرانی و زرشک", price=Decimal('120000'), category=main_course_cat),
            FoodItem.objects.create(name="قیمه بادمجان", description="خورشت قیمه با لپه و بادمجان سرخ شده", price=Decimal('130000'), category=main_course_cat),
            FoodItem.objects.create(name="کشک بادمجان", description="غذای سنتی با بادمجان، کشک، نعنا داغ و گردو", price=Decimal('95000'), category=main_course_cat),
            FoodItem.objects.create(name="شله زرد", description="دسر سنتی ایرانی با برنج، زعفران و شکر", price=Decimal('35000'), category=dessert_cat),
        ]
        self.side_dishes = [
            SideDish.objects.create(name="سالاد شیرازی", description="خیار، گوجه و پیاز خرد شده با آبغوره", price=Decimal('25000')),
            SideDish.objects.create(name="ماست و خیار", description="ماست چکیده به همراه خیار و نعنا خشک", price=Decimal('20000')),
            SideDish.objects.create(name="دوغ", description="نوشیدنی سنتی بر پایه ماست", price=Decimal('15000')),
        ]
        self.stdout.write(self.style.SUCCESS("   -> آیتم‌های منو با موفقیت ایجاد شدند."))

    def create_super_admin(self):
        """ [IMPROVED] Ensures a super admin user exists and has the correct state. """
        self.stdout.write("\n3. بررسی و ایجاد کاربر ادمین کل (superadmin)...")
        self.super_admin, created = User.objects.update_or_create(
            username="superadmin",
            defaults={
                'email': "superadmin@example.com",
                'role': User.Role.SUPER_ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'budget': Decimal('9999999.00')
            }
        )
        if created:
            self.super_admin.set_password("superpassword123")
            self.super_admin.save()
            self.stdout.write(self.style.SUCCESS("   -> کاربر 'superadmin' با رمز 'superpassword123' ایجاد شد."))
        else:
            self.stdout.write(self.style.WARNING("   -> کاربر 'superadmin' از قبل وجود داشت. اطلاعات آن به‌روزرسانی شد."))


    def create_default_schedule(self):
        """ Creates a single, global default schedule. """
        self.stdout.write("\n4. ایجاد برنامه غذایی پیش‌فرض سراسری...")
        today = timezone.now().date()
        self.default_schedule = Schedule.objects.create(
            name="برنامه غذایی پیش‌فرض سراسری",
            company=None, 
            start_date=today.replace(day=1),
            end_date=today + timedelta(days=60),
            is_active=True
        )
        main_foods = [food for food in self.food_items if food.category.name == "غذای اصلی"]
        current_date = self.default_schedule.start_date
        while current_date <= self.default_schedule.end_date:
            if current_date.weekday() != 4: # Skip Thursdays (or Fridays if your week starts differently)
                daily_menu = DailyMenu.objects.create(schedule=self.default_schedule, date=current_date)
                daily_menu.available_foods.set(random.sample(main_foods, k=random.randint(2, 4)))
                daily_menu.available_sides.set(random.sample(self.side_dishes, k=random.randint(1, 3)))
            current_date += timedelta(days=1)
        self.stdout.write(self.style.SUCCESS("   -> برنامه غذایی پیش‌فرض برای ۶۰ روز آینده ایجاد شد."))

    def create_company_and_related_data(self, index, fake):
        """ Creates a company and all its related data. """
        self.stdout.write(f"\n5.{index}. ایجاد داده برای شرکت «{fake.company()}»...")
        today = timezone.now().date()

        company = Company.objects.create(
            name=f"{fake.company()} شعبه {index}",
            contact_person=fake.name(),
            contact_phone=fake.phone_number(),
            address=fake.address()
        )
        Contract.objects.create(company=company, start_date=today - timedelta(days=30), end_date=today + timedelta(days=365), status=Contract.ContractStatus.ACTIVE)
        
        # [IMPROVED] Deposit to company wallet and create transaction
        wallet = company.wallet
        deposit_amount = Decimal('50000000.00')
        wallet.balance = deposit_amount
        wallet.save()
        Transaction.objects.create(wallet=wallet, user=self.super_admin, transaction_type=Transaction.TransactionType.DEPOSIT, amount=deposit_amount, description=f"واریز اولیه توسط {self.super_admin.username}.")
        self.stdout.write(f"   -> کیف پول شرکت با مبلغ {deposit_amount:,.0f} تومان شارژ شد.")

        # Create users for the company
        company_admin = User.objects.create_user(username=f"admin_co_{index}", password="password123", first_name=fake.first_name(), last_name=fake.last_name(), role=User.Role.COMPANY_ADMIN, company=company)
        employees = [User.objects.create_user(username=f"user{i}_co{index}", password="password123", first_name=fake.first_name(), last_name=fake.last_name(), role=User.Role.EMPLOYEE, company=company) for i in range(5)]
        
        # Allocate budget to employees
        allocation_amount = Decimal('1000000.00')
        for employee in employees:
            wallet.balance -= allocation_amount
            employee.budget += allocation_amount
            employee.save()
            Transaction.objects.create(wallet=wallet, user=company_admin, transaction_type=Transaction.TransactionType.BUDGET_ALLOCATION, amount=-allocation_amount, description=f"تخصیص اعتبار به {employee.username}.")
        wallet.save()
        self.stdout.write(f"   -> ادمین شرکت و {len(employees)} کارمند ایجاد شدند و اعتبار گرفتند.")

        # Assign a schedule
        if index == 1: # Assign a dedicated schedule to the first company
            self.stdout.write(f"   -> ایجاد و تخصیص برنامه غذایی اختصاصی...")
            schedule = Schedule.objects.create(name=f"برنامه اختصاصی {company.name}", company=company, start_date=today.replace(day=1), end_date=today + timedelta(days=30), is_active=True)
            main_foods = [food for food in self.food_items if food.category.name == "غذای اصلی"]
            current_date = schedule.start_date
            while current_date <= schedule.end_date:
                if current_date.weekday() != 4:
                    daily_menu = DailyMenu.objects.create(schedule=schedule, date=current_date)
                    daily_menu.available_foods.set(random.sample(main_foods, k=2))
                current_date += timedelta(days=1)
            company.active_schedule = schedule
        else: # Assign default schedule to others
             self.stdout.write(f"   -> تخصیص برنامه غذایی پیش‌فرض سراسری...")
             company.active_schedule = self.default_schedule
        company.save()