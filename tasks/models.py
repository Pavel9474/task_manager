from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Meta:
    indexes = [
        models.Index(fields=['parent']),
        models.Index(fields=['type']),
        models.Index(fields=['name']),
    ]

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
        indexes = [
            models.Index(fields=['last_name', 'first_name'], name='emp_name_idx'),
            models.Index(fields=['email'], name='emp_email_idx'),
            models.Index(fields=['is_active'], name='emp_active_idx'),
            models.Index(fields=['department'], name='emp_dept_idx'),
        ]
    
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
        result = self.last_name
        if self.first_name:
            result += f" {self.first_name[0]}."
        if self.patronymic:
            result += f"{self.patronymic[0]}."  # Убираем пробел перед отчеством
        return result
    
    def get_department_path(self):
        """Получить полный путь подразделения сотрудника"""
        staff_pos = self.staff_positions.filter(is_active=True).first()
        if staff_pos and staff_pos.department:
            return staff_pos.department.full_path
        return None
    
    def get_main_department(self):
        """Получить основное подразделение (уровень 1)"""
        staff_pos = self.staff_positions.filter(is_active=True).first()
        if staff_pos and staff_pos.department:
            # Поднимаемся до корня
            dept = staff_pos.department
            while dept.parent:
                dept = dept.parent
            return dept.name
        return None
    
    def get_division(self):
        """Получить отдел (уровень 2)"""
        staff_pos = self.staff_positions.filter(is_active=True).first()
        if staff_pos and staff_pos.department:
            # Ищем подразделение 2-го уровня
            dept = staff_pos.department
            # Если текущее подразделение уже 2-го уровня (одна точка)
            if dept.level == 1:  # Уровень 1 - это основное подразделение, уровень 2 - отдел
                return dept.name
            # Иначе ищем родителя 2-го уровня
            while dept.parent:
                if dept.parent.level == 1:
                    return dept.name
                dept = dept.parent
        return None
    
    def get_laboratory(self):
        """Получить лабораторию (уровень 3 и ниже)"""
        staff_pos = self.staff_positions.filter(is_active=True).first()
        if staff_pos and staff_pos.department:
            # Если текущее подразделение - лаборатория (уровень 3+)
            if staff_pos.department.type in ['laboratory', 'group']:
                return staff_pos.department.name
            # Ищем среди дочерних? Но сотрудник привязан к конкретному подразделению
        return None
    
    def get_organization_structure(self):
        """Получить полную структуру организации для сотрудника"""
        staff_pos = self.staff_positions.filter(is_active=True).first()
        if not staff_pos or not staff_pos.department:
            return None
        
        dept = staff_pos.department
        structure = {
            'institute': None,      # Институт (уровень 1)
            'department': None,     # Отдел (уровень 2)
            'laboratory': None,     # Лаборатория (уровень 3)
            'group': None,          # Группа (уровень 4)
            'full_path': dept.full_path
        }
        
        # Собираем все уровни
        current = dept
        while current:
            if current.level == 0:  # Институт/основное подразделение
                structure['institute'] = current.name
            elif current.level == 1:  # Отдел
                structure['department'] = current.name
            elif current.level == 2:  # Лаборатория
                structure['laboratory'] = current.name
            elif current.level >= 3:  # Группа и ниже
                structure['group'] = current.name
            current = current.parent
        
        return structure


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
        indexes = [
            models.Index(fields=['user'], name='task_user_idx'),
            models.Index(fields=['status'], name='task_status_idx'),
            models.Index(fields=['priority'], name='task_priority_idx'),
            models.Index(fields=['due_date'], name='task_due_date_idx'),
            models.Index(fields=['created_date'], name='task_created_idx'),
        ]
    
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
    
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('critical', 'Критический'),
    ]
    
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        verbose_name='Основная задача',
        related_name='subtasks'
    )
    
    # Основные поля
    stage_number = models.CharField('Номер этапа', max_length=10)  # Изменено на CharField
    title = models.CharField('Название этапа', max_length=200)
    description = models.TextField('Описание', blank=True, null=True)
    output = models.TextField('Выход/Результат', blank=True, null=True)
    
    priority = models.CharField(
        'Приоритет', 
        max_length=20, 
        choices=PRIORITY_CHOICES, 
        default='medium'
    )
    
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
        unique_together = ['task', 'stage_number']
        indexes = [
            models.Index(fields=['task'], name='subtask_task_idx'),
            models.Index(fields=['status'], name='subtask_status_idx'),
            models.Index(fields=['priority'], name='subtask_priority_idx'),
            models.Index(fields=['planned_end'], name='subtask_planned_end_idx'),
        ]  # Это теперь работает со строками
    
    def __str__(self):
        priority_icon = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }.get(self.priority, '')
        return f"{priority_icon} {self.task.title} - Этап {self.stage_number}: {self.title}"
    
    def save(self, *args, **kwargs):
        # Сначала сохраняем объект
        super().save(*args, **kwargs)
        
        # Автоматическое назначение ответственного, если исполнитель один
        try:
            if not self.responsible and self.performers.count() == 1:
                self.responsible = self.performers.first()
                if self.responsible:
                    self.save(update_fields=['responsible'])
        except:
            pass
    
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
    
    @property
    def priority_color(self):
        """Цвет для отображения приоритета"""
        colors = {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'info',
            'low': 'success'
        }
        return colors.get(self.priority, 'secondary')
    
    @property
    def priority_icon(self):
        """Иконка для отображения приоритета"""
        icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }
        return icons.get(self.priority, '⚪')
    
# Сначала определите ResearchTask (самый верхний уровень)
class ResearchTask(models.Model):
    """Основная НИР (научно-исследовательская работа) - соответствует ТЗ"""
    title = models.CharField('Наименование ТЗ', max_length=500)
    tz_number = models.CharField('Номер ТЗ', max_length=100, blank=True)
    customer = models.CharField('Госзаказчик', max_length=500, blank=True)
    executor = models.CharField('Исполнитель', max_length=500, blank=True)
    start_date = models.DateField('Дата начала', null=True, blank=True)
    end_date = models.DateField('Дата окончания', null=True, blank=True)
    funding = models.DecimalField('Финансирование', max_digits=15, decimal_places=2, null=True, blank=True)
    
    created_date = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_date = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'НИР'
        verbose_name_plural = 'НИР'
    
    def __str__(self):
        return self.title


# Затем ResearchStage (зависит от ResearchTask)
class ResearchStage(models.Model):
    """Этап НИР - соответствует основным этапам (1, 2, 3)"""
    research_task = models.ForeignKey(
        ResearchTask,  # Теперь ResearchTask уже определен
        on_delete=models.CASCADE,
        related_name='stages',
        verbose_name='НИР'
    )
    stage_number = models.IntegerField('Номер этапа')
    title = models.TextField('Наименование этапа')
    start_date = models.DateField('Дата начала', null=True, blank=True)
    end_date = models.DateField('Дата окончания', null=True, blank=True)
    
    # Исполнители
    performers = models.ManyToManyField(
        'Employee',  # Используем строку вместо прямого импорта
        verbose_name='Исполнители',
        related_name='research_stages',
        blank=True
    )
    responsible = models.ForeignKey(
        'Employee',  # Используем строку вместо прямого импорта
        on_delete=models.SET_NULL,
        verbose_name='Ответственный',
        related_name='responsible_stages',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Этап НИР'
        verbose_name_plural = 'Этапы НИР'
        ordering = ['stage_number']
    
    def __str__(self):
        return f"Этап {self.stage_number}: {self.title[:50]}"


# Затем ResearchSubstage (зависит от ResearchStage)
class ResearchSubstage(models.Model):
    """Подэтап НИР - соответствует 1.1, 1.2, 1.3 и т.д."""
    stage = models.ForeignKey(
        ResearchStage,  # ResearchStage уже определен
        on_delete=models.CASCADE,
        related_name='substages',
        verbose_name='Этап'
    )
    substage_number = models.CharField('Номер подэтапа', max_length=10)
    title = models.TextField('Наименование подэтапа')
    description = models.TextField('Описание', blank=True)
    start_date = models.DateField('Дата начала', null=True, blank=True)
    end_date = models.DateField('Дата окончания', null=True, blank=True)
    
    # Исполнители
    performers = models.ManyToManyField(
        'Employee',  # Используем строку
        verbose_name='Исполнители',
        related_name='research_substages',
        blank=True
    )
    responsible = models.ForeignKey(
        'Employee',  # Используем строку
        on_delete=models.SET_NULL,
        verbose_name='Ответственный',
        related_name='responsible_substages',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Подэтап НИР'
        verbose_name_plural = 'Подэтапы НИР'
        ordering = ['substage_number']
    
    def __str__(self):
        return f"Подэтап {self.substage_number}: {self.title[:50]}"
    
    def inherit_performers_from_stage(self):
        """Наследовать исполнителей от родительского этапа"""
        if not self.performers.exists() and self.stage.performers.exists():
            self.performers.set(self.stage.performers.all())
        if not self.responsible and self.stage.responsible:
            self.responsible = self.stage.responsible


# Затем ResearchProduct (зависит от ResearchSubstage)
class ResearchProduct(models.Model):
    """Научно-техническая продукция (результаты)"""
    substage = models.ForeignKey(
        ResearchSubstage,  # ResearchSubstage уже определен
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Подэтап'
    )
    name = models.CharField('Наименование продукции', max_length=500)
    description = models.TextField('Описание', blank=True)
    due_date = models.DateField('Срок представления', null=True, blank=True)
    
    # Исполнители
    performers = models.ManyToManyField(
        'Employee',  # Используем строку
        verbose_name='Исполнители',
        related_name='research_products',
        blank=True
    )
    responsible = models.ForeignKey(
        'Employee',  # Используем строку
        on_delete=models.SET_NULL,
        verbose_name='Ответственный',
        related_name='responsible_products',
        null=True,
        blank=True
    )
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('in_progress', 'В работе'),
        ('completed', 'Выполнено'),
        ('delayed', 'Задержка')
    ]
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    class Meta:
        verbose_name = 'Продукция'
        verbose_name_plural = 'Продукция'
    
    def __str__(self):
        return self.name
    
    def inherit_performers_from_substage(self):
        """Наследовать исполнителей от подэтапа"""
        if not self.performers.exists() and self.substage.performers.exists():
            self.performers.set(self.substage.performers.all())
        if not self.responsible and self.substage.responsible:
            self.responsible = self.substage.responsible

class Department(models.Model):
    """Структурное подразделение (отдел, лаборатория, группа)"""
    name = models.CharField('Название', max_length=255)
    code = models.CharField('Код', max_length=50, blank=True, null=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        verbose_name='Вышестоящее подразделение',
        related_name='children',
        null=True, 
        blank=True
    )
    level = models.IntegerField('Уровень вложенности', default=0)
    full_path = models.CharField('Полный путь', max_length=500, blank=True)
    
    # Тип подразделения
    TYPE_CHOICES = [
        ('directorate', 'Дирекция'),
        ('department', 'Отдел'),
        ('laboratory', 'Лаборатория'),
        ('group', 'Группа'),
        ('service', 'Служба'),
        ('division', 'Отделение'),
    ]
    type = models.CharField('Тип', max_length=20, choices=TYPE_CHOICES, default='department')
    
    created_date = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_date = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'
        ordering = ['full_path']
        indexes = [
            models.Index(fields=['parent'], name='dept_parent_idx'),
            models.Index(fields=['type'], name='dept_type_idx'),
            models.Index(fields=['name'], name='dept_name_idx'),
            models.Index(fields=['full_path'], name='dept_full_path_idx'),
            models.Index(fields=['level'], name='dept_level_idx'),
        ]
    
    def __str__(self):
        return self.full_path or self.name
    
    def save(self, *args, **kwargs):
        # Автоматически определяем уровень вложенности
        if self.parent:
            self.level = self.parent.level + 1
            self.full_path = f"{self.parent.full_path} / {self.name}"
        else:
            self.level = 0
            self.full_path = self.name
        super().save(*args, **kwargs)


class Position(models.Model):
    """Должность"""
    name = models.CharField('Название должности', max_length=255)
    code = models.CharField('Код', max_length=50, blank=True, null=True)
    category = models.CharField('Категория (ПКГ)', max_length=50, blank=True, null=True)
    
    created_date = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_date = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'
    
    def __str__(self):
        return self.name


class StaffPosition(models.Model):
    """Штатная единица (связь сотрудника с должностью и подразделением)"""
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE,
        verbose_name='Сотрудник',
        related_name='staff_positions'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        verbose_name='Подразделение',
        related_name='staff_positions'
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        verbose_name='Должность',
        related_name='staff_positions'
    )
    
    # Рабочая нагрузка
    workload = models.DecimalField(
        'Ставка', 
        max_digits=3, 
        decimal_places=2, 
        default=1.0,
        help_text='Например: 1.0, 0.5, 0.25'
    )
    
    # Тип занятости
    EMPLOYMENT_TYPE_CHOICES = [
        ('main', 'Основное'),
        ('internal_combination', 'Внутреннее совместительство'),
        ('external_combination', 'Внешнее совместительство'),
        ('combination', 'Совмещение'),
        ('part_time', 'Частичная занятость'),
        ('vacant', 'Вакансия'),
        ('decree', 'Декретный отпуск'),
        ('allowance', 'Надбавка'),
    ]
    employment_type = models.CharField(
        'Тип занятости', 
        max_length=30, 
        choices=EMPLOYMENT_TYPE_CHOICES,
        default='main'
    )
    
    # Примечание (для особых случаев)
    notes = models.TextField('Примечание', blank=True, null=True)
    
    # Период действия
    start_date = models.DateField('Дата начала', null=True, blank=True)
    end_date = models.DateField('Дата окончания', null=True, blank=True)
    
    is_active = models.BooleanField('Активная', default=True)
    
    created_date = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_date = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Штатная единица'
        verbose_name_plural = 'Штатные единицы'
        unique_together = ['employee', 'department', 'position', 'start_date']
        indexes = [
            models.Index(fields=['department'], name='staff_dept_idx'),
            models.Index(fields=['employee'], name='staff_employee_idx'),
            models.Index(fields=['position'], name='staff_position_idx'),
            models.Index(fields=['is_active'], name='staff_active_idx'),
            models.Index(fields=['employment_type'], name='staff_empl_type_idx'),
        ]
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.position.name} ({self.department.name})"

# tasks/models.py - проверка и дополнение модели ResearchProduct

class ResearchProduct(models.Model):
    """Научная продукция"""
    subtask = models.ForeignKey(Subtask, on_delete=models.CASCADE, related_name='products',
                                verbose_name='Подэтап', null=True, blank=True)
    name = models.CharField('Наименование продукции', max_length=500)
    description = models.TextField('Описание', blank=True)
    due_date = models.DateField('Срок выполнения', null=True, blank=True)
      
    # Оставляем ответственного (можно будет назначать через ProductPerformer)
    responsible = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        verbose_name='Ответственный',
        related_name='responsible_products', 
        null=True, 
        blank=True
    )
    
    # Связи с этапами НИР
    research_task = models.ForeignKey(
        'ResearchTask',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='НИР'
    )
    research_stage = models.ForeignKey(
        'ResearchStage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='Этап НИР'
    )
    research_substage = models.ForeignKey(
        'ResearchSubstage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='Подэтап НИР'
    )
    
    # Тип продукции
    product_type = models.CharField(
        'Тип продукции',
        max_length=50,
        choices=[
            ('report', 'Отчет'),
            ('article', 'Статья'),
            ('patent', 'Патент'),
            ('methodology', 'Методика'),
            ('software', 'Программное обеспечение'),
            ('other', 'Другое'),
        ],
        default='report'
    )
    
    # Плановые и фактические даты
    planned_start = models.DateField('Планируемая дата начала', null=True, blank=True)
    planned_end = models.DateField('Планируемая дата окончания', null=True, blank=True)
    actual_start = models.DateField('Фактическая дата начала', null=True, blank=True)
    actual_end = models.DateField('Фактическая дата окончания', null=True, blank=True)
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('in_progress', 'В работе'),
        ('completed', 'Выполнено'),
        ('delayed', 'Задержка'),
        ('cancelled', 'Отменена'),
    ]
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    completion_percent = models.IntegerField('Процент выполнения', default=0)
    notes = models.TextField('Примечания', blank=True)
    
    created_date = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_date = models.DateTimeField('Дата обновления', auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_products'
    )
    
    class Meta:
        verbose_name = 'Научная продукция'
        verbose_name_plural = 'Научная продукция'
        ordering = ['-created_date']
    
    def __str__(self):
        return self.name
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.status not in ['completed', 'cancelled'] and self.planned_end:
            return timezone.now().date() > self.planned_end
        return False
    
    @property
    def performers_list(self):
        return ', '.join([p.employee.full_name for p in self.product_performers.all()])


class ProductPerformer(models.Model):
    """Связь продукции с исполнителем (с указанием роли)"""
    
    ROLE_CHOICES = [
        ('responsible', 'Ответственный исполнитель'),
        ('executor', 'Исполнитель'),
        ('consultant', 'Консультант'),
        ('reviewer', 'Рецензент'),
        ('approver', 'Утверждающий'),
    ]
    
    product = models.ForeignKey(
        ResearchProduct,
        on_delete=models.CASCADE,
        related_name='product_performers',
        verbose_name='Продукция'
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='product_performers',
        verbose_name='Сотрудник'
    )
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default='executor')
    contribution_percent = models.DecimalField(
        'Доля участия (%)',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Сумма долей всех исполнителей может быть больше 100%'
    )
    start_date = models.DateField('Дата начала работы', null=True, blank=True)
    end_date = models.DateField('Дата окончания работы', null=True, blank=True)
    notes = models.TextField('Примечания', blank=True)
    assigned_date = models.DateTimeField('Дата назначения', auto_now_add=True)
    assigned_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_performers'
    )
    
    class Meta:
        verbose_name = 'Исполнитель продукции'
        verbose_name_plural = 'Исполнители продукции'
        unique_together = ['product', 'employee']  # Один сотрудник на продукцию - одна запись
        ordering = ['-role', 'employee__last_name']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.product.name} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        # Если это ответственный исполнитель, обновляем поле responsible в продукции
        super().save(*args, **kwargs)
        if self.role == 'responsible':
            self.product.responsible = self.employee
            self.product.save(update_fields=['responsible'])
        elif self.product.responsible == self.employee and self.role != 'responsible':
            # Если был ответственным, а теперь роль изменилась
            other_responsible = ProductPerformer.objects.filter(
                product=self.product,
                role='responsible'
            ).exclude(id=self.id).first()
            self.product.responsible = other_responsible.employee if other_responsible else None
            self.product.save(update_fields=['responsible'])