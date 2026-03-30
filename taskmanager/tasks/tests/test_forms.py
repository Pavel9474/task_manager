from django.test import TestCase
from tasks.forms import TaskForm, TaskWithImportForm
from tasks.models import Employee
from django.contrib.auth.models import User


class TaskFormTest(TestCase):
    """Тесты для формы задачи"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_valid_form(self):
        """Тест валидной формы"""
        form_data = {
            'title': 'Тестовая задача',
            'description': 'Описание',
            'status': 'todo',
            'priority': 'medium'
        }
        form = TaskForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_empty_title(self):
        """Тест формы без названия"""
        form_data = {
            'description': 'Описание',
            'status': 'todo',
            'priority': 'medium'
        }
        form = TaskForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_invalid_dates(self):
        """Тест невалидных дат"""
        form_data = {
            'title': 'Тест',
            'start_time': '2024-01-10 10:00',
            'end_time': '2024-01-01 10:00'
        }
        form = TaskForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Время окончания не может быть раньше времени начала', str(form.errors))


class TaskWithImportFormTest(TestCase):
    """Тесты для формы с импортом ТЗ"""
    
    def test_form_without_file(self):
        """Тест формы без файла"""
        form_data = {
            'title': 'Тестовая задача',
            'description': 'Описание',
            'status': 'todo',
            'priority': 'medium'
        }
        form = TaskWithImportForm(data=form_data)
        # Проверяем, что форма валидна (все обязательные поля заполнены)
        self.assertTrue(form.is_valid(), f"Ошибки формы: {form.errors}")
        
    def test_form_fields(self):
        """Тест наличия всех полей"""
        form = TaskWithImportForm()
        self.assertIn('title', form.fields)
        self.assertIn('tz_file', form.fields)