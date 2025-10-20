# orders/tests/test_admin_reports.py

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from datetime import timedelta

# Import all necessary models to create test data
from users.models import User
from companies.models import Company
from menu.models import FoodItem
from schedules.models import Schedule, DailyMenu
from orders.models import Order

class AdminReportsAPITests(APITestCase):
    def setUp(self):
        """Set up a realistic set of data for testing the reports endpoint."""
        self.today = timezone.now().date()
        self.yesterday = self.today - timedelta(days=1)

        # === Create Companies ===
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")

        # === Create Users ===
        self.admin_user = User.objects.create_user(
            username='admin_reports', password='password123', role=User.Role.ADMIN, company=self.company_a
        )
        self.employee_a = User.objects.create_user(
            username='employee_reports_a', password='password123', role=User.Role.EMPLOYEE, company=self.company_a
        )

        # === Create Menu Items ===
        self.food_kebab = FoodItem.objects.create(name="Test Kebab", price=100.00)
        self.food_pizza = FoodItem.objects.create(name="Test Pizza", price=150.00)

        # === Create Schedules and Menus ===
        schedule_a = Schedule.objects.create(
            name="Reports Test Schedule",
            company=self.company_a,
            start_date=self.yesterday,
            end_date=self.today
        )
        self.daily_menu_today = DailyMenu.objects.create(schedule=schedule_a, date=self.today)
        self.daily_menu_today.available_foods.set([self.food_kebab, self.food_pizza])
        
        self.daily_menu_yesterday = DailyMenu.objects.create(schedule=schedule_a, date=self.yesterday)
        self.daily_menu_yesterday.available_foods.set([self.food_kebab])

        # === Create Orders ===
        # 2 orders for today
        Order.objects.create(user=self.employee_a, daily_menu=self.daily_menu_today, food_item=self.food_kebab)
        Order.objects.create(user=self.employee_a, daily_menu=self.daily_menu_today, food_item=self.food_pizza)
        # 1 order for yesterday
        Order.objects.create(user=self.employee_a, daily_menu=self.daily_menu_yesterday, food_item=self.food_kebab)

        # URL for the reports endpoint
        self.reports_url = reverse('admin-reports')

    def test_security_employee_cannot_access_reports(self):
        """
        VERIFY: A user with the 'EMPLOYEE' role receives a 403 Forbidden error.
        """
        self.client.force_authenticate(user=self.employee_a)
        response = self.client.get(self.reports_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_security_admin_can_access_reports(self):
        """
        VERIFY: A user with the 'ADMIN' role can successfully access the endpoint.
        """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.reports_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_shape_is_correct(self):
        """
        VERIFY: The API response contains all the expected top-level keys.
        """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.reports_url)
        
        self.assertIn("summary", response.data)
        self.assertIn("top_items", response.data)
        self.assertIn("sales_by_date", response.data)
        self.assertIn("company_stats", response.data)
        self.assertIn("user_stats", response.data)

    def test_aggregation_orders_today_is_correct(self):
        """
        VERIFY: The 'summary.orders_today' field correctly counts orders placed today.
        """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.reports_url)
        
        # We created 2 orders for today in setUp
        self.assertEqual(response.data['summary']['orders_today'], 2)

    def test_aggregation_total_sales_today_is_correct(self):
        """
        VERIFY: The 'summary.total_sales_today' correctly sums the price of today's orders.
        """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.reports_url)
        
        # Expected total = price of Kebab (100) + price of Pizza (150) = 250
        expected_sales = 250.00
        self.assertEqual(float(response.data['summary']['total_sales_today']), expected_sales)

    def test_filtering_by_date_range(self):
        """
        VERIFY: The 'from' and 'to' query parameters correctly filter the data.
        """
        self.client.force_authenticate(user=self.admin_user)
        
        # Filter for only yesterday's data
        url = f"{self.reports_url}?from={self.yesterday.isoformat()}&to={self.yesterday.isoformat()}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 'orders_today' should be 0 because we are filtering for yesterday
        self.assertEqual(response.data['summary']['orders_today'], 0)
        # The sales by date should only contain one entry for yesterday
        self.assertEqual(len(response.data['sales_by_date']), 1)
        self.assertEqual(response.data['sales_by_date'][0]['date'], self.yesterday.isoformat())