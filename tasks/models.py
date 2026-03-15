from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Employee(models.Model):
    DEPARTMENT_CHOICES = [
        ('development', 'Разработка'),
        ('design', 'Дизайн'),
        ('marketing', 'Маркетинг'),
        ('sales', 'Продажи'),
        ('hr', 'HR'),
        ('administration', 'Администрация'),
        ('research', 'Исследования'),
        ('other', 'Другое'),
    ]
    
    LABORATORY_CHOICES = [
        ('lab1', 'Лаборатория №1'),
        ('lab2', 'Лаборатория №2'),
        ('lab3', 'Лаборатория №3'),
        ('research_lab', 'Исследовательская лаборатория'),
        ('test_lab', 'Тестовая лаборатория'),
        ('other', 'Другая'),
    ]
    
    # Основная информация
    last_name = models.CharField('Фамилия', max_length=100)
    first_name = models.CharField('Имя', max_length=100)
    patronymic = models.CharField('Отчество', max_length=100, blank=True, null=True)
    position = models.CharField('Должность', max_length=200)
    
    # Контактная информация
    email = models.EmailField('Email', unique=True)
    phone = models.CharField('Телефон', max_length=20, blank=True, null=True)
    
    # Организационная информация
    department = models.CharField('Отдел', max_length=50, choices=DEPARTMENT_CHOICES, default='other')
    laboratory = models.CharField('Лаборатория', max_length=50, choices=LABORATORY_CHOICES, blank=True, null=True)
    
    # Дополнительная информация
    hire_date = models.DateField('Дата найма', null=True, blank=True)
    is_active = models.BooleanField('Активный сотрудник', default=True)
    notes = models.TextField('Заметки', blank=True, null=True)
    
    # Системная информация
    created_date = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_date = models.DateTimeField('Дата обновления', auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_employees')
    
    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return self.full_name
    
    @property
    def full_name(self):
        """Полное имя сотрудника"""
        parts = [self.last_name, self.first_name]
        if self.patronymic:
            parts.append(self.patronymic)
        return ' '.join(parts)
    
    @property
    def short_name(self):
        """Краткое имя (Фамилия И.О.)"""
        name_parts = [self.last_name]
        if self.first_name:
            name_parts.append(f"{self.first_name[0]}.")
        if self.patronymic:
            name_parts.append(f"{self.patronymic[0]}.")
        return ' '.join(name_parts)


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
    
    # Связь с сотрудниками
    assigned_to = models.ManyToManyField(
        Employee, 
        verbose_name='Исполнители', 
        blank=True,
        related_name='tasks'
    )
    
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

class Subtask(models.Model):
    """Подзадача (этап) основной задачи"""
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        verbose_name='Основная задача',
        related_name='subtasks'
    )
    
    # Основные поля
    stage_number = models.PositiveIntegerField('Номер этапа')
    title = models.CharField('Название этапа', max_length=200)
    description = models.TextField('Описание', blank=True, null=True)
    output = models.TextField('Выход/Результат', blank=True, null=True)
    
    # Исполнители (множественный выбор)
    performers = models.ManyToManyField(
        Employee,
        verbose_name='Исполнители',
        related_name='subtasks',
        blank=True
    )
    
    # Ответственный исполнитель (один из performers)
    responsible = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        verbose_name='Ответственный',
        related_name='responsible_subtasks',
        null=True,
        blank=True
    )
    
    # Временные параметры
    planned_start = models.DateTimeField('Планируемое начало', null=True, blank=True)
    planned_end = models.DateTimeField('Планируемое окончание', null=True, blank=True)
    actual_start = models.DateTimeField('Фактическое начало', null=True, blank=True)
    actual_end = models.DateTimeField('Фактическое окончание', null=True, blank=True)
    
    # Статус
    STATUS_CHOICES = [
        ('pending', 'Ожидание'),
        ('in_progress', 'В процессе'),
        ('completed', 'Завершен'),
        ('delayed', 'Задержка'),
    ]
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Дополнительно
    notes = models.TextField('Заметки', blank=True, null=True)
    created_date = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_date = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Подзадача'
        verbose_name_plural = 'Подзадачи'
        ordering = ['stage_number']
        unique_together = ['task', 'stage_number']  # Уникальный номер этапа в рамках задачи
    
    def __str__(self):
        return f"{self.task.title} - Этап {self.stage_number}: {self.title}"
    
    def save(self, *args, **kwargs):
        # Автоматическое назначение ответственного, если исполнитель один
        if not self.responsible and self.performers.count() == 1:
            self.responsible = self.performers.first()
        super().save(*args, **kwargs)
    
    def is_overdue(self):
        """Проверка просрочки"""
        if self.planned_end and self.status != 'completed':
            return timezone.now() > self.planned_end
        return False
    
    @property
    def progress(self):
        """Прогресс выполнения (для отображения)"""
        if self.status == 'completed':
            return 100
        elif self.status == 'in_progress':
            if self.planned_start and self.planned_end:
                total = (self.planned_end - self.planned_start).total_seconds()
                elapsed = (timezone.now() - self.actual_start).total_seconds() if self.actual_start else 0
                if total > 0:
                    return min(int((elapsed / total) * 100), 99)
            return 50
        return 0