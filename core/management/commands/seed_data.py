# back/core/management/commands/seed_data.py

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
        # Initialize Faker for Persian locale
        fake = Faker('fa_IR')

        try:
            with transaction.atomic():
                # Keep superusers before clearing other data
                # This ensures your main admin account is not deleted
                self.stdout.write("حذف کاربران غیر ادمین...")
                User.objects.exclude(is_superuser=True).delete()

                self.clear_data()
                self.create_menu_items()
                self.create_super_admin()

                # Create 3 companies with all related data
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
        # User objects are already cleared in the handle method
        Wallet.objects.all().delete()
        Company.objects.all().delete()
        SideDish.objects.all().delete()
        FoodItem.objects.all().delete()
        FoodCategory.objects.all().delete()

    def create_menu_items(self):
        """ Creates food categories, food items, and side dishes in Persian. """
        self.stdout.write("ایجاد آیتم‌های منو...")

        # Food Categories
        main_course_cat = FoodCategory.objects.create(name="غذای اصلی", description="غذاهای اصلی خوشمزه و متنوع.")
        dessert_cat = FoodCategory.objects.create(name="دسر", description="دسرهای شیرین برای پایان وعده غذایی.")

        # Food Items
        self.food_items = [
            FoodItem.objects.create(name="چلوکباب کوبیده", description="دو سیخ کباب کوبیده گوشت گوسفندی به همراه برنج ایرانی", price=Decimal('150000'), category=main_course_cat),
            FoodItem.objects.create(name="قورمه سبزی", description="خورشت سبزیجات معطر با گوشت گوسفندی و لوبیا قرمز به همراه برنج", price=Decimal('135000'), category=main_course_cat),
            FoodItem.objects.create(name="جوجه کباب", description="یک سیخ جوجه کباب زعفرانی به همراه برنج ایرانی", price=Decimal('140000'), category=main_course_cat),
            FoodItem.objects.create(name="زرشک پلو با مرغ", description="ران مرغ سرخ شده به همراه برنج زعفرانی و زرشک", price=Decimal('120000'), category=main_course_cat),
            FoodItem.objects.create(name="شله زرد", description="دسر سنتی ایرانی با برنج، زعفران و شکر", price=Decimal('35000'), category=dessert_cat),
        ]

        # Side Dishes
        self.side_dishes = [
            SideDish.objects.create(name="سالاد شیرازی", description="خیار، گوجه و پیاز خرد شده با آبغوره", price=Decimal('25000')),
            SideDish.objects.create(name="ماست و خیار", description="ماست چکیده به همراه خیار و نعنا خشک", price=Decimal('20000')),
            SideDish.objects.create(name="دوغ", description="نوشیدنی سنتی بر پایه ماست", price=Decimal('15000')),
            SideDish.objects.create(name="نوشابه", description="نوشابه کوکاکولا", price=Decimal('12000')),
        ]

    def create_super_admin(self):
        """ Ensures a super admin user exists. """
        if not User.objects.filter(username="superadmin").exists():
            self.stdout.write("ایجاد کاربر ادمین کل...")
            User.objects.create_superuser(
                username="superadmin",
                email="superadmin@example.com",
                password="superpassword123",
                role=User.Role.SUPER_ADMIN
            )

    def create_company_and_related_data(self, index, fake):
        """ Creates a company with all associated data. """
        self.stdout.write(f"ایجاد داده برای شرکت {index}...")

        # 1. Create Company
        company = Company.objects.create(
            name=fake.company(),
            contact_person=fake.name(),
            contact_phone=fake.phone_number(),
            address=fake.address()
        )

        # 2. Create Contract
        today = timezone.now().date()
        Contract.objects.create(
            company=company,
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=365),
            status=Contract.ContractStatus.ACTIVE
        )

        # 3. Fund Company Wallet
        wallet = company.wallet
        deposit_amount = Decimal('10000000.00')
        wallet.balance = deposit_amount
        wallet.save()

        super_admin = User.objects.get(username="superadmin")
        Transaction.objects.create(
            wallet=wallet,
            user=super_admin,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            amount=deposit_amount,
            description=f"واریز اولیه توسط {super_admin.username}."
        )

        # 4. Create Users for the Company
        company_admin = User.objects.create_user(
            username=f"admin_company_{index}",
            password="password123",
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=f"admin{index}@company.com",
            role=User.Role.COMPANY_ADMIN,
            company=company
        )

        employees = []
        for i in range(5):
            employee = User.objects.create_user(
                username=f"employee_{i}_company_{index}",
                password="password123",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=f"emp{i}_company{index}@company.com",
                role=User.Role.EMPLOYEE,
                company=company
            )
            employees.append(employee)

        # 5. Allocate Budget to Employees
        allocation_amount = Decimal('500000.00')
        for employee in employees:
            if wallet.balance >= allocation_amount:
                wallet.balance -= allocation_amount
                employee.budget += allocation_amount

                Transaction.objects.create(
                    wallet=wallet,
                    user=company_admin,
                    transaction_type=Transaction.TransactionType.BUDGET_ALLOCATION,
                    amount=-allocation_amount,
                    description=f"تخصیص اعتبار به {employee.username} توسط {company_admin.username}."
                )

                Transaction.objects.create(
                    wallet=wallet,
                    user=employee,
                    transaction_type=Transaction.TransactionType.BUDGET_ALLOCATION,
                    amount=allocation_amount,
                    description=f"اعتبار تخصیص داده شده توسط {company_admin.username}."
                )

        wallet.save()
        for emp in employees:
            emp.save()

        # 6. Create Schedule and Daily Menus
        schedule = Schedule.objects.create(
            name=f"برنامه ماهانه {company.name}",
            company=company,
            start_date=today.replace(day=1),
            end_date=(today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
            is_active=True
        )
        
        # [FIX] This was the missing critical step:
        # Assign the newly created schedule as the active one for the company.
        company.active_schedule = schedule
        company.save()

        current_date = schedule.start_date
        while current_date <= schedule.end_date:
            # Skip Fridays (weekend in Iran)
            if current_date.weekday() != 4: # Friday is 4 in Python's weekday()
                daily_menu = DailyMenu.objects.create(schedule=schedule, date=current_date)
                daily_menu.available_foods.set(random.sample(self.food_items, k=2))
                daily_menu.available_sides.set(random.sample(self.side_dishes, k=2))
            current_date += timedelta(days=1)

        # 7. Create Past Orders for some employees
        past_menus = DailyMenu.objects.filter(schedule=schedule, date__lt=today).order_by('?')
        for employee in random.sample(employees, k=3):
            for menu in past_menus[:5]:
                food_item = menu.available_foods.first()
                side_dish = menu.available_sides.first()
                total_cost = food_item.price + (side_dish.price if side_dish else Decimal('0.00'))

                if employee.budget >= total_cost:
                    order = Order.objects.create(
                        user=employee,
                        daily_menu=menu,
                        food_item=food_item,
                        status=random.choice([Order.OrderStatus.DELIVERED, Order.OrderStatus.CONFIRMED])
                    )
                    if side_dish:
                        order.side_dishes.add(side_dish)

                    # Update employee budget and create transaction
                    employee.budget -= total_cost
                    employee.save()

                    Transaction.objects.create(
                        wallet=wallet,
                        user=employee,
                        transaction_type=Transaction.TransactionType.ORDER_DEDUCTION,
                        amount=-total_cost,
                        description=f"کسر هزینه برای سفارش #{order.id}"
                    )