from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from tasks.models import Employee


class EmployeeAPITest(TestCase):
    """Тесты для API сотрудников"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.employee = Employee.objects.create(
            last_name='Иванов',
            first_name='Иван',
            email='ivanov@test.com',
            created_by=self.user
        )
    
    def test_employee_search_api(self):
        """Тест поиска сотрудников через API"""
        response = self.client.get(reverse('employee_search_api'), {'q': 'Иван'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertIn('Иванов', data['results'][0]['text'])
    
    def test_employee_search_api_empty(self):
        """Тест поиска с пустым запросом"""
        response = self.client.get(reverse('employee_search_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)  # Возвращает всех