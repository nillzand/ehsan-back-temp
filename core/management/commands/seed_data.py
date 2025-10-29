# ehsan-back-temp/core/management/commands/seed_data.py

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
        self.stdout.write("شروع فرآیند پر کردن پایگاه داده...")
        fake = Faker('fa_IR')

        try:
            with transaction.atomic():
                self.stdout.write("حذف کاربران غیر ادمین...")
                User.objects.exclude(is_superuser=True).delete()

                self.clear_data()
                self.create_menu_items()
                self.create_super_admin()

                self.create_default_schedule()

                for i in range(3):
                    self.create_company_and_related_data(i + 1, fake)

                self.stdout.write(self.style.SUCCESS("پر کردن پایگاه داده با موفقیت به پایان رسید!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"خطایی در حین پر کردن پایگاه داده رخ داد: {e}"))

    def clear_data(self):
        """ Clears all data from the relevant models except for superusers. """
        self.stdout.write("پاک‌سازی داده‌های موجود...")
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

    def create_menu_items(self):
        """ Creates food categories, food items, and side dishes in Persian. """
        self.stdout.write("ایجاد آیتم‌های منو...")
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
            SideDish.objects.create(name="نوشابه", description="نوشابه کوکاکولا", price=Decimal('12000')),
            SideDish.objects.create(name="زیتون پرورده", description="زیتون با رب انار، گردو و سبزیجات معطر", price=Decimal('30000')),
        ]

    def create_super_admin(self):
        """ [FIX] Ensures a super admin user exists AND has a budget for testing. """
        if not User.objects.filter(username="superadmin").exists():
            self.stdout.write("ایجاد کاربر ادمین کل با بودجه تستی...")
            User.objects.create_superuser(
                username="superadmin",
                email="superadmin@example.com",
                password="superpassword123",
                role=User.Role.SUPER_ADMIN,
                budget=Decimal('9999999.00') # Assign a large budget for testing
            )

    def create_default_schedule(self):
        """ Creates a global default schedule not tied to any company. """
        self.stdout.write("ایجاد منوی پیش‌فرض...")
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
            if current_date.weekday() != 4: 
                daily_menu = DailyMenu.objects.create(schedule=self.default_schedule, date=current_date)
                if len(main_foods) >= 4:
                    daily_menu.available_foods.set(random.sample(main_foods, k=4))
                if len(self.side_dishes) >= 3:
                    daily_menu.available_sides.set(random.sample(self.side_dishes, k=3))
            current_date += timedelta(days=1)


    def create_company_and_related_data(self, index, fake):
        """ Creates a company and all its related data. """
        self.stdout.write(f"ایجاد داده برای شرکت {index}...")
        today = timezone.now().date()

        company = Company.objects.create(
            name=f"{fake.company()} شعبه {index}",
            contact_person=fake.name(),
            contact_phone=fake.phone_number(),
            address=fake.address()
        )

        Contract.objects.create(company=company, start_date=today - timedelta(days=30), end_date=today + timedelta(days=365), status=Contract.ContractStatus.ACTIVE)
        wallet = company.wallet
        deposit_amount = Decimal('50000000.00')
        wallet.balance = deposit_amount
        wallet.save()
        super_admin = User.objects.get(username="superadmin")
        Transaction.objects.create(wallet=wallet, user=super_admin, transaction_type=Transaction.TransactionType.DEPOSIT, amount=deposit_amount, description=f"واریز اولیه توسط {super_admin.username}.")
        company_admin = User.objects.create_user(username=f"admin_company_{index}", password="password123", first_name=fake.first_name(), last_name=fake.last_name(), email=f"admin{index}@company.com", role=User.Role.COMPANY_ADMIN, company=company)
        employees = [User.objects.create_user(username=f"employee_{i}_company_{index}", password="password123", first_name=fake.first_name(), last_name=fake.last_name(), email=f"emp{i}_company{index}@company.com", role=User.Role.EMPLOYEE, company=company) for i in range(5)]
        allocation_amount = Decimal('1000000.00')
        for employee in employees:
            if wallet.balance >= allocation_amount:
                wallet.balance -= allocation_amount
                employee.budget += allocation_amount
                employee.save(update_fields=['budget'])
                Transaction.objects.create(wallet=wallet, user=company_admin, transaction_type=Transaction.TransactionType.BUDGET_ALLOCATION, amount=-allocation_amount, description=f"تخصیص اعتبار به {employee.username} توسط {company_admin.username}.")
                Transaction.objects.create(wallet=wallet, user=employee, transaction_type=Transaction.TransactionType.BUDGET_ALLOCATION, amount=allocation_amount, description=f"اعتبار تخصیص داده شده توسط {company_admin.username}.")
        wallet.save()


        if random.choice([True, False]):
            self.stdout.write(f"  -> ایجاد برنامه غذایی اختصاصی برای شرکت {company.name}...")
            schedule = Schedule.objects.create(
                name=f"برنامه اختصاصی {company.name}",
                company=company,
                start_date=today.replace(day=1),
                end_date=today + timedelta(days=60),
                is_active=True
            )
            main_foods = [food for food in self.food_items if food.category.name == "غذای اصلی"]
            current_date = schedule.start_date
            while current_date <= schedule.end_date:
                if current_date.weekday() != 4:
                    daily_menu = DailyMenu.objects.create(schedule=schedule, date=current_date)
                    if len(main_foods) >= 4:
                        daily_menu.available_foods.set(random.sample(main_foods, k=4))
                    if len(self.side_dishes) >= 3:
                        daily_menu.available_sides.set(random.sample(self.side_dishes, k=3))
                current_date += timedelta(days=1)
            company.active_schedule = schedule
            company.save()
        else:
            self.stdout.write(f"  -> اختصاص منوی پیش‌فرض به شرکت {company.name}...")
            company.active_schedule = self.default_schedule
            company.save()

        schedule_to_use = company.active_schedule
        past_menus = DailyMenu.objects.filter(schedule=schedule_to_use, date__lt=today).order_by('?')
        for employee in random.sample(employees, k=3):
            employee.refresh_from_db() 
            for menu in past_menus[:5]:
                food_item = menu.available_foods.first()
                if not food_item: continue
                side_dish = menu.available_sides.first()
                total_cost = food_item.price + (side_dish.price if side_dish else Decimal('0.00'))
                if employee.budget >= total_cost:
                    order = Order.objects.create(user=employee, daily_menu=menu, food_item=food_item, status=random.choice([Order.OrderStatus.DELIVERED, Order.OrderStatus.CONFIRMED]))
                    if side_dish:
                        order.side_dishes.add(side_dish)
                    employee.budget -= total_cost
                    employee.save()
                    Transaction.objects.create(wallet=wallet, user=employee, transaction_type=Transaction.TransactionType.ORDER_DEDUCTION, amount=-total_cost, description=f"کسر هزینه برای سفارش #{order.id}")