from django.test import TestCase
from django.contrib.auth.models import User
from tasks.models import Employee, Department

# Create your tests here.
class EmployeeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
    
    def test_create_employee(self):
        employee = Employee.objects.create(
            last_name='Иванов',
            first_name='Иван',
            email='ivanov@test.com',
            created_by=self.user
        )
        self.assertEqual(employee.full_name, 'Иванов Иван')