from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from tasks.models import Task, Employee


class TaskViewsTest(TestCase):
    """Тесты для представлений задач"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.task = Task.objects.create(
            title='Тестовая задача',
            user=self.user,
            status='todo'
        )
    
    def test_task_list_view(self):
        """Тест списка задач"""
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/task_list.html')
        self.assertContains(response, 'Тестовая задача')
    
    def test_task_detail_view(self):
        """Тест детальной страницы задачи"""
        response = self.client.get(reverse('task_detail', args=[self.task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/task_detail.html')
        self.assertContains(response, 'Тестовая задача')
    
    def test_task_create_view_get(self):
        """Тест GET запроса создания задачи"""
        response = self.client.get(reverse('task_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/task_form.html')
    
    def test_task_create_view_post(self):
        """Тест POST запроса создания задачи"""
        response = self.client.post(reverse('task_create'), {
            'title': 'Новая задача',
            'description': 'Описание',
            'status': 'todo',
            'priority': 'medium'
        })
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertEqual(Task.objects.count(), 2)
    
    def test_task_complete_view(self):
        """Тест завершения задачи"""
        response = self.client.get(reverse('task_complete', args=[self.task.id]))
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'done')
    
    def test_task_delete_view(self):
        """Тест удаления задачи"""
        response = self.client.post(reverse('task_delete', args=[self.task.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.count(), 0)


class AuthViewsTest(TestCase):
    """Тесты для аутентификации"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_login_view(self):
        """Тест входа в систему"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_register_view(self):
        """Тест регистрации"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'newpass123',
            'password2': 'newpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())


class UnauthorizedViewsTest(TestCase):
    """Тесты для неавторизованного доступа"""
    
    def setUp(self):
        self.client = Client()
    
    def test_task_list_redirect(self):
        """Тест: неавторизованный пользователь перенаправляется на логин"""
        response = self.client.get(reverse('task_list'))
        # Проверяем, что код ответа 302 (редирект)
        self.assertEqual(response.status_code, 302)
        # Проверяем, что редирект ведёт на страницу логина
        self.assertTrue(response.url.startswith('/login/'))
    
    def test_org_chart_redirect(self):
        """Тест: неавторизованный пользователь не видит оргструктуру"""
        response = self.client.get(reverse('organization_chart'))
        self.assertEqual(response.status_code, 302)