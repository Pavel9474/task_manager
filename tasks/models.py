from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]
    
    STATUS_CHOICES = [
        ('todo', 'К выполнению'),
        ('in_progress', 'В процессе'),
        ('done', 'Выполнено'),
    ]
    
    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    created_date = models.DateTimeField('Дата создания', auto_now_add=True)
    due_date = models.DateTimeField('Срок выполнения', null=True, blank=True)
    
    # Новые поля для времени начала и окончания
    start_time = models.DateTimeField('Время начала', null=True, blank=True)
    end_time = models.DateTimeField('Время окончания', null=True, blank=True)
    
    priority = models.CharField('Приоритет', max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='todo')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь', related_name='tasks')
    
    class Meta:
        ordering = ['-created_date']
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
    
    def __str__(self):
        return self.title
    
    def is_overdue(self):
        if self.due_date and self.status != 'done':
            return timezone.now() > self.due_date
        return False
    
    def duration(self):
        """Вычисляет длительность выполнения задачи"""
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            if duration.days > 0:
                return f"{duration.days}д {hours}ч {minutes}м"
            else:
                return f"{hours}ч {minutes}м"
        return None
    
    def can_start(self):
        """Проверяет, можно ли начать задачу"""
        return self.status == 'todo' and not self.start_time
    
    def can_complete(self):
        """Проверяет, можно ли завершить задачу"""
        return self.status == 'in_progress' and self.start_time and not self.end_time