from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from tasks.models import Employee, Department, Position, StaffPosition, Task, Subtask
from datetime import datetime, timedelta


class EmployeeModelTest(TestCase):
    """Тесты для модели Employee"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@test.com'
        )
        self.employee = Employee.objects.create(
            last_name='Иванов',
            first_name='Иван',
            patronymic='Иванович',
            position='Разработчик',
            email='ivanov@test.com',
            is_active=True,
            created_by=self.user
        )
    
    def test_full_name(self):
        """Тест полного имени"""
        self.assertEqual(self.employee.full_name, 'Иванов Иван Иванович')
    
    def test_short_name(self):
        """Тест краткого имени"""
        self.assertEqual(self.employee.short_name, 'Иванов И.И.')
    
    def test_employee_creation(self):
        """Тест создания сотрудника"""
        self.assertEqual(Employee.objects.count(), 1)
        self.assertEqual(self.employee.email, 'ivanov@test.com')
    
    def test_employee_str(self):
        """Тест строкового представления"""
        self.assertEqual(str(self.employee), 'Иванов Иван Иванович')
    
    def test_is_active_default(self):
        """Тест значения is_active по умолчанию"""
        self.assertTrue(self.employee.is_active)


class DepartmentModelTest(TestCase):
    """Тесты для модели Department"""
    
    def setUp(self):
        self.parent = Department.objects.create(
            name='Руководство',
            type='directorate'
        )
        self.child = Department.objects.create(
            name='Секретариат',
            type='department',
            parent=self.parent
        )
    
    def test_department_creation(self):
        """Тест создания подразделения"""
        self.assertEqual(Department.objects.count(), 2)
        self.assertEqual(self.child.parent, self.parent)
    
    def test_full_path(self):
        """Тест полного пути"""
        self.assertEqual(self.parent.full_path, 'Руководство')
        self.assertEqual(self.child.full_path, 'Руководство / Секретариат')
    
    def test_level_auto(self):
        """Тест автоматического определения уровня"""
        self.assertEqual(self.parent.level, 0)
        self.assertEqual(self.child.level, 1)


class PositionModelTest(TestCase):
    """Тесты для модели Position"""
    
    def setUp(self):
        self.position = Position.objects.create(
            name='Разработчик',
            category='7.4.1'
        )
    
    def test_position_creation(self):
        """Тест создания должности"""
        self.assertEqual(Position.objects.count(), 1)
        self.assertEqual(self.position.name, 'Разработчик')
    
    def test_position_str(self):
        """Тест строкового представления"""
        self.assertEqual(str(self.position), 'Разработчик')


class StaffPositionModelTest(TestCase):
    """Тесты для модели StaffPosition"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.employee = Employee.objects.create(
            last_name='Иванов',
            first_name='Иван',
            email='ivanov@test.com',
            created_by=self.user
        )
        self.department = Department.objects.create(name='Разработка')
        self.position = Position.objects.create(name='Разработчик')
        
        self.staff = StaffPosition.objects.create(
            employee=self.employee,
            department=self.department,
            position=self.position,
            workload=1.0,
            employment_type='main'
        )
    
    def test_staff_creation(self):
        """Тест создания штатной единицы"""
        self.assertEqual(StaffPosition.objects.count(), 1)
        self.assertEqual(self.staff.workload, 1.0)
    
    def test_staff_str(self):
        """Тест строкового представления"""
        expected = f"{self.employee.full_name} - {self.position.name} ({self.department.name})"
        self.assertEqual(str(self.staff), expected)


class TaskModelTest(TestCase):
    """Тесты для модели Task"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.task = Task.objects.create(
            title='Тестовая задача',
            description='Описание задачи',
            user=self.user,
            status='todo',
            priority='high',
            due_date=timezone.now() + timedelta(days=7)
        )
    
    def test_task_creation(self):
        """Тест создания задачи"""
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(self.task.title, 'Тестовая задача')
    
    def test_is_overdue(self):
        """Тест проверки просрочки"""
        self.assertFalse(self.task.is_overdue())
        
        # Создаём просроченную задачу
        overdue_task = Task.objects.create(
            title='Просроченная задача',
            user=self.user,
            due_date=timezone.now() - timedelta(days=1)
        )
        self.assertTrue(overdue_task.is_overdue())
    
    def test_can_start(self):
        """Тест возможности начать задачу"""
        self.assertTrue(self.task.can_start())
        self.task.status = 'in_progress'
        self.task.save()
        self.assertFalse(self.task.can_start())
    
    def test_can_complete(self):
        """Тест возможности завершить задачу"""
        self.task.start_time = timezone.now()
        self.task.status = 'in_progress'
        self.task.save()
        self.assertTrue(self.task.can_complete())
        
        self.task.status = 'done'
        self.task.save()
        self.assertFalse(self.task.can_complete())