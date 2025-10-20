from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from users.models import User
from companies.models import Company
from menu.models import FoodItem, SideDish
from schedules.models import Schedule, DailyMenu
from .models import Order

class OrderAPITests(APITestCase):
    def setUp(self):
        """Set up initial data for all tests."""
        # Create Companies
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")

        # Create Users
        self.admin_user = User.objects.create_user(username='admin', password='password123', role=User.Role.ADMIN, company=self.company_a)
        self.employee_a = User.objects.create_user(username='employee_a', password='password123', role=User.Role.EMPLOYEE, company=self.company_a)
        self.employee_b = User.objects.create_user(username='employee_b', password='password123', role=User.Role.EMPLOYEE, company=self.company_b)

        # Create Menu Items
        self.food_item_1 = FoodItem.objects.create(name="Kebab", price=15.00)
        self.food_item_2 = FoodItem.objects.create(name="Pasta", price=12.00)
        self.side_dish_1 = SideDish.objects.create(name="Salad", price=3.00)

        # Create Schedule and Daily Menu for Company A
        today = timezone.now().date()
        self.schedule_a = Schedule.objects.create(
            name="Test Schedule A",
            company=self.company_a,
            start_date=today,
            end_date=today + timezone.timedelta(days=7)
        )
        self.daily_menu_a = DailyMenu.objects.create(schedule=self.schedule_a, date=today)
        self.daily_menu_a.available_foods.set([self.food_item_1, self.food_item_2])
        self.daily_menu_a.available_sides.set([self.side_dish_1])

    def test_employee_can_create_order(self):
        """Ensure an employee can successfully place an order for their company."""
        self.client.force_authenticate(user=self.employee_a)
        url = reverse('order-list')
        data = {
            'daily_menu': self.daily_menu_a.id,
            'food_item': self.food_item_1.id,
            'side_dishes': [self.side_dish_1.id]
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.first().user, self.employee_a)

    def test_employee_cannot_order_unavailable_food(self):
        """Ensure an order fails if the food item is not in the daily menu."""
        unavailable_food = FoodItem.objects.create(name="Sushi", price=20.00)
        self.client.force_authenticate(user=self.employee_a)
        url = reverse('order-list')
        data = {
            'daily_menu': self.daily_menu_a.id,
            'food_item': unavailable_food.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not available', str(response.data))

    def test_employee_cannot_order_from_another_company_menu(self):
        """Ensure an employee from Company B cannot order from Company A's menu."""
        self.client.force_authenticate(user=self.employee_b) # Employee from Company B
        url = reverse('order-list')
        data = {
            'daily_menu': self.daily_menu_a.id, # Menu from Company A
            'food_item': self.food_item_1.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("own company's menu", str(response.data))

    def test_employee_can_only_view_own_orders(self):
        """Ensure an employee can list their own orders but not others'."""
        # Create an order for employee_a
        Order.objects.create(user=self.employee_a, daily_menu=self.daily_menu_a, food_item=self.food_item_1)
        
        # Authenticate as employee_a and check
        self.client.force_authenticate(user=self.employee_a)
        url = reverse('order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Authenticate as employee_b and check
        self.client.force_authenticate(user=self.employee_b)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0) # Should see no orders