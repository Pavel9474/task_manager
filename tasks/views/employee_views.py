from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from ..models import Employee, Task, Subtask, ResearchTask, ResearchStage, ResearchSubstage, ResearchProduct, ProductPerformer
from ..forms_employee import EmployeeForm, EmployeeImportForm
import pandas as pd
from datetime import datetime, timedelta, date
from django.db.models import Q
import json
# В самом верху файла, после импортов
print("=" * 60)
print("ФАЙЛ employee_views.py ЗАГРУЖЕН")
print("=" * 60)
@login_required
def employee_list(request):
    """Список сотрудников с задачами и научной продукцией, отсортированными по близости к текущей дате"""
    employees = Employee.objects.all()
    print(f"DEBUG: Найдено сотрудников: {employees.count()}") 
    
    # Фильтрация
    department = request.GET.get('department', '')
    if department:
        employees = employees.filter(department=department)
    
    laboratory = request.GET.get('laboratory', '')
    if laboratory:
        employees = employees.filter(laboratory=laboratory)
    
    is_active = request.GET.get('is_active', '')
    if is_active == 'active':
        employees = employees.filter(is_active=True)
    elif is_active == 'inactive':
        employees = employees.filter(is_active=False)
    
    # Поиск
    search = request.GET.get('search', '')
    if search:
        employees = employees.filter(
            Q(last_name__icontains=search) |
            Q(first_name__icontains=search) |
            Q(email__icontains=search) |
            Q(position__icontains=search)
        )
    
    # Сортировка
    sort = request.GET.get('sort', 'last_name')
    employees = employees.order_by(sort)
    
    # Пагинация
    paginator = Paginator(employees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем текущую дату для расчетов
    today = timezone.now().date()
    
    # Цвета для разных исследовательских задач (НИР)
    research_task_colors = [
        '#0d6efd',  # Blue
        '#198754',  # Green
        '#dc3545',  # Red
        '#fd7e14',  # Orange
        '#6f42c1',  # Purple
        '#d63384',  # Pink
        '#0dcaf0',  # Cyan
        '#ffc107',  # Yellow
        '#20c997',  # Teal
        '#6610f2',  # Indigo
    ]
    
    # Для каждого сотрудника получаем и сортируем задачи
    employee_tasks_data = {}
    employee_research_products = {}
    gantt_data = {}
    
    for employee in page_obj:
        # Собираем все задачи сотрудника
        all_tasks = []
        
        # Обычные задачи
        for task in employee.tasks.all():
            task_date = task.due_date.date() if task.due_date else None
            all_tasks.append({
                'type': 'task',
                'id': task.id,
                'title': task.title,
                'date': task_date,
                'status': task.status,
                'priority': task.priority,
                'is_overdue': task.is_overdue() if task.due_date else False,
            })
        
        # Подзадачи (этапы)
        for subtask in employee.subtasks.all():
            subtask_date = subtask.planned_end.date() if subtask.planned_end else None
            all_tasks.append({
                'type': 'subtask',
                'id': subtask.id,
                'title': subtask.title,
                'date': subtask_date,
                'status': subtask.status,
                'priority': subtask.priority,
                'is_overdue': subtask.is_overdue() if subtask.planned_end else False,
                'stage_number': subtask.stage_number,
            })
        
        # Сортируем задачи: ближайшие к сегодня первыми
        def sort_key(task):
            task_date = task['date']
            if task_date is None:
                return (9999, 1)  # Без даты в конец
            days_diff = (task_date - today).days
            if days_diff < 0:
                # Просроченные: чем больше просрочка, тем ниже в списке просроченных
                return (-9999 - days_diff, 0)
            else:
                # Будущие: чем ближе, тем выше
                return (days_diff, 0)
        
        all_tasks.sort(key=sort_key)
        employee_tasks_data[employee.id] = all_tasks
        
        # Получаем научную продукцию сотрудника через разные связи
        research_products = []
        research_task_color_map = {}  # Map research task ID to color
        color_index = 0
        processed_product_ids = set()  # Track already processed products
        
        # 1. Get products through ProductPerformer (with role info)
        for product_performer in employee.product_performers.select_related(
            'product', 
            'product__research_task',
            'product__research_stage',
            'product__research_substage'
        ).all():
            product = product_performer.product
            if product.id in processed_product_ids:
                continue
            processed_product_ids.add(product.id)
            
            # Get research task info
            research_task = product.research_task
            research_stage = product.research_stage
            research_substage = product.research_substage
            
            # Assign color to research task
            if research_task:
                if research_task.id not in research_task_color_map:
                    research_task_color_map[research_task.id] = research_task_colors[color_index % len(research_task_colors)]
                    color_index += 1
                task_color = research_task_color_map[research_task.id]
            else:
                task_color = '#6c757d'  # Gray for products without research task
            
            product_date = product.planned_end if product.planned_end else product.due_date
            product_date = product_date if isinstance(product_date, date) else (product_date.date() if product_date else None)
            
            is_overdue = False
            if product_date and product.status not in ['completed', 'cancelled']:
                is_overdue = today > product_date
            
            research_products.append({
                'id': product.id,
                'name': product.name,
                'date': product_date,
                'status': product.status,
                'product_type': product.product_type,
                'is_overdue': is_overdue,
                'role': product_performer.role,
                'contribution': str(product_performer.contribution_percent) if product_performer.contribution_percent else None,
                'research_task': {
                    'id': research_task.id if research_task else None,
                    'title': research_task.title if research_task else None,
                    'tz_number': research_task.tz_number if research_task else None,
                    'color': task_color,
                } if research_task else None,
                'research_stage': {
                    'id': research_stage.id if research_stage else None,
                    'title': research_stage.title if research_stage else None,
                    'stage_number': research_stage.stage_number if research_stage else None,
                } if research_stage else None,
                'research_substage': {
                    'id': research_substage.id if research_substage else None,
                    'title': research_substage.title if research_substage else None,
                    'substage_number': research_substage.substage_number if research_substage else None,
                } if research_substage else None,
            })
        
        # 2. Also get products through ProductPerformer intermediate model
        # The ResearchProduct model uses ProductPerformer for employee assignments
        from ..models import ProductPerformer
        for product_performer in ProductPerformer.objects.filter(employee=employee).select_related('product', 'product__research_task', 'product__research_stage', 'product__research_substage'):
            product = product_performer.product
            if product.id in processed_product_ids:
                continue
            processed_product_ids.add(product.id)
            
            # Get research task info directly from product
            research_task = product.research_task
            research_stage = product.research_stage
            research_substage = product.research_substage
            
            # Assign color to research task
            if research_task:
                if research_task.id not in research_task_color_map:
                    research_task_color_map[research_task.id] = research_task_colors[color_index % len(research_task_colors)]
                    color_index += 1
                task_color = research_task_color_map[research_task.id]
            else:
                task_color = '#6c757d'
            
            product_date = product.planned_end or product.due_date
            product_date = product_date if isinstance(product_date, date) else (product_date.date() if product_date else None)
            
            is_overdue = False
            if product_date and product.status not in ['completed', 'cancelled']:
                is_overdue = today > product_date
            
            research_products.append({
                'id': product.id,
                'name': product.name,
                'date': product_date,
                'status': product.status,
                'product_type': product.product_type if hasattr(product, 'product_type') else 'other',
                'is_overdue': is_overdue,
                'role': product_performer.role,
                'contribution': product_performer.contribution_percent,
                'research_task': {
                    'id': research_task.id if research_task else None,
                    'title': research_task.title if research_task else None,
                    'tz_number': research_task.tz_number if research_task else None,
                    'color': task_color,
                } if research_task else None,
                'research_stage': {
                    'id': research_stage.id if research_stage else None,
                    'title': research_stage.title if research_stage else None,
                    'stage_number': research_stage.stage_number if research_stage else None,
                } if research_stage else None,
                'research_substage': {
                    'id': research_substage.id if research_substage else None,
                    'title': research_substage.title if research_substage else None,
                    'substage_number': research_substage.substage_number if research_substage else None,
                } if research_substage else None,
            })
        
        # Sort research products by date (closest to today first)
        research_products.sort(key=sort_key)
        employee_research_products[employee.id] = research_products
        
        # Данные для Gantt-диаграммы
        gantt_tasks = []
        
        # Add regular tasks to Gantt
        for task in all_tasks:
            if task['date']:
                task_date = task['date']
                # Определяем длительность (для визуализации)
                if task['type'] == 'subtask':
                    duration = 7  # По умолчанию 7 дней для подзадач
                else:
                    duration = 14  # По умолчанию 14 дней для задач
                
                # Определяем цвет в зависимости от статуса и просрочки
                if task['is_overdue']:
                    color = '#dc3545'  # Красный - просрочено
                elif task['status'] in ['completed', 'done']:
                    color = '#198754'  # Зеленый - выполнено
                elif task['status'] == 'in_progress':
                    color = '#0d6efd'  # Синий - в работе
                else:
                    color = '#6c757d'  # Серый - ожидание
                
                gantt_tasks.append({
                    'id': f"{task['type']}_{task['id']}",
                    'name': task['title'][:30] + '...' if len(task['title']) > 30 else task['title'],
                    'start': (task_date - timedelta(days=duration)).isoformat() if task_date else today.isoformat(),
                    'end': task_date.isoformat() if task_date else (today + timedelta(days=duration)).isoformat(),
                    'progress': 100 if task['status'] in ['completed', 'done'] else (50 if task['status'] == 'in_progress' else 0),
                    'color': color,
                    'status': task['status'],
                    'type': 'regular',
                })
        
        # Add research products to Gantt with research task colors
        for product in research_products:
            if product['date']:
                product_date = product['date']
                duration = 21  # Default 21 days for research products
                
                # Use research task color
                color = product['research_task']['color'] if product['research_task'] else '#6c757d'
                
                # Darken color if overdue
                if product['is_overdue']:
                    color = '#dc3545'  # Red for overdue
                
                gantt_tasks.append({
                    'id': f"product_{product['id']}",
                    'name': product['name'][:30] + '...' if len(product['name']) > 30 else product['name'],
                    'start': (product_date - timedelta(days=duration)).isoformat(),
                    'end': product_date.isoformat(),
                    'progress': 100 if product['status'] == 'completed' else (50 if product['status'] == 'in_progress' else 0),
                    'color': color,
                    'status': product['status'],
                    'type': 'research',
                    'research_task_title': product['research_task']['title'] if product['research_task'] else None,
                })
        
        gantt_data[employee.id] = gantt_tasks
    
    context = {
        'page_obj': employees,  # Для пагинации
        'employee_list': employees,  # Простой список
        'page_obj': page_obj,
        'departments': Employee.DEPARTMENT_CHOICES,
        'laboratories': Employee.LABORATORY_CHOICES,
        'current_filters': {
            'department': department,
            'laboratory': laboratory,
            'is_active': is_active,
            'search': search,
            'sort': sort,
        },
        'employee_tasks': employee_tasks_data,
        'employee_research_products': employee_research_products,
        'gantt_data_json': json.dumps(gantt_data),
        'today': today.isoformat(),
    }
    return render(request, 'tasks/employee_list.html', context)

@login_required
def employee_detail(request, employee_id):
    """Детальная информация о сотруднике"""
    print(f"=== employee_detail вызван для id={employee_id} ===")
    
    try:
        # Используем get_object_or_404 для автоматического 404
        employee = get_object_or_404(Employee, id=employee_id)
        print(f"=== Найден сотрудник: {employee.full_name} ===")
        
        # Получаем параметры фильтрации для Ганта
        gantt_year = request.GET.get('year')
        gantt_start = request.GET.get('start_date')
        gantt_end = request.GET.get('end_date')
        
        # Определяем период для Ганта
        if gantt_year and gantt_year.isdigit():
            year = int(gantt_year)
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
        elif gantt_start and gantt_end:
            start_date = datetime.strptime(gantt_start, '%Y-%m-%d').date()
            end_date = datetime.strptime(gantt_end, '%Y-%m-%d').date()
        else:
            # По умолчанию - текущий год
            current_year = timezone.now().year
            start_date = date(current_year, 1, 1)
            end_date = date(current_year, 12, 31)
        # Штатные позиции
        staff_positions = employee.staff_positions.filter(is_active=True)
        org_structure = employee.get_organization_structure()
        
        # Тип отображения
        item_type = request.GET.get('type', 'all')
        
        items = []
        
        # ===== 1. Обычные задачи =====
        tasks = employee.tasks.all()
        for task in tasks:
            sort_date = task.due_date if task.due_date else task.created_date
            items.append({
                'type': 'task',
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'due_date': task.due_date,
                'sort_date': sort_date,
                'is_overdue': task.is_overdue() if task.due_date else False,
                'get_priority_display': task.get_priority_display(),
                'get_status_display': task.get_status_display(),
                'priority_color': {'high': 'warning', 'medium': 'info', 'low': 'success'}.get(task.priority, 'secondary')
            })
        
        # ===== 2. Подзадачи =====
        subtasks_as_performer = employee.subtasks.all()
        subtasks_as_responsible = employee.responsible_subtasks.all()
        all_subtasks = (subtasks_as_performer | subtasks_as_responsible).distinct()
        
        for subtask in all_subtasks:
            sort_date = subtask.planned_end if subtask.planned_end else subtask.created_date
            items.append({
                'type': 'subtask',
                'id': subtask.id,
                'title': subtask.title,
                'description': subtask.description,
                'status': subtask.status,
                'priority': subtask.priority,
                'due_date': subtask.planned_end,
                'sort_date': sort_date,
                'is_overdue': subtask.is_overdue() if subtask.planned_end else False,
                'task': subtask.task,
                'progress': getattr(subtask, 'progress', 0),
                'get_priority_display': subtask.get_priority_display(),
                'get_status_display': subtask.get_status_display(),
                'priority_color': getattr(subtask, 'priority_color', 'secondary')
            })
        
        # ===== 3. НИР =====
        research_tasks_as_performer = ResearchTask.objects.filter(
            stages__substages__products__product_performers__employee=employee
        ).distinct()
        research_tasks_as_responsible = ResearchTask.objects.filter(
            stages__substages__products__responsible=employee
        ).distinct()
        all_research_tasks = (research_tasks_as_performer | research_tasks_as_responsible).distinct()
        
        for rt in all_research_tasks:
            sort_date = rt.end_date if rt.end_date else rt.created_date
            items.append({
                'type': 'research_task',
                'id': rt.id,
                'title': rt.title,
                'tz_number': rt.tz_number,
                'start_date': rt.start_date,
                'end_date': rt.end_date,
                'sort_date': sort_date,
                'is_overdue': rt.end_date and rt.end_date < timezone.now().date() if rt.end_date else False,
                'stages_count': rt.stages.count(),
                'url': 'research_task_detail',
                'url_args': {'task_id': rt.id},
            })
        
        # ===== 4. Этапы НИР =====
        stages = ResearchStage.objects.filter(performers=employee) | ResearchStage.objects.filter(responsible=employee)
        stages = stages.select_related('research_task').distinct()
        
        for stage in stages:
            sort_date = stage.end_date if stage.end_date else stage.created_date
            items.append({
                'type': 'research_stage',
                'id': stage.id,
                'title': stage.title,
                'stage_number': stage.stage_number,
                'research_task': stage.research_task,
                'start_date': stage.start_date,
                'end_date': stage.end_date,
                'sort_date': sort_date,
                'is_overdue': stage.end_date and stage.end_date < timezone.now().date() if stage.end_date else False,
                'substages_count': stage.substages.count(),
                'url': 'research_stage_detail',
                'url_args': {'stage_id': stage.id},
            })
        
        # ===== 5. Подэтапы НИР =====
        substages = ResearchSubstage.objects.filter(performers=employee) | ResearchSubstage.objects.filter(responsible=employee)
        substages = substages.select_related('stage', 'stage__research_task').distinct()
        
        for substage in substages:
            sort_date = substage.end_date if substage.end_date else substage.created_date
            items.append({
                'type': 'research_substage',
                'id': substage.id,
                'title': substage.title,
                'substage_number': substage.substage_number,
                'stage': substage.stage,
                'research_task': substage.stage.research_task,
                'start_date': substage.start_date,
                'end_date': substage.end_date,
                'sort_date': sort_date,
                'is_overdue': substage.end_date and substage.end_date < timezone.now().date() if substage.end_date else False,
                'products_count': substage.products.count(),
                'url': 'research_substage_detail',
                'url_args': {'substage_id': substage.id},
            })
        
        # ===== 6. Продукция =====
        # Собираем ID продукции через исполнителя и ответственного
        product_ids = set()
        
        # Продукция где сотрудник исполнитель
        performer_product_ids = ResearchProduct.objects.filter(
            product_performers__employee=employee
        ).values_list('id', flat=True)
        product_ids.update(performer_product_ids)
        
        # Продукция где сотрудник ответственный
        responsible_product_ids = ResearchProduct.objects.filter(
            responsible=employee
        ).values_list('id', flat=True)
        product_ids.update(responsible_product_ids)
        
        # Получаем все продукты по ID с оптимизацией
        all_products = ResearchProduct.objects.filter(
            id__in=product_ids
        ).select_related(
            'research_task', 'research_stage', 'research_substage', 'responsible'
        )
        
        print(f"\n=== ОТЛАДКА ПРОДУКЦИИ ===")
        print(f"Продукция как исполнитель: {len(performer_product_ids)}")
        print(f"Продукция как ответственный: {len(responsible_product_ids)}")
        print(f"Всего продукции: {all_products.count()}")
        print(f"Date range for Gantt: {start_date} to {end_date}")
        for p in all_products:
            print(f"  Product {p.id}: planned_start={p.planned_start}, planned_end={p.planned_end}, substage={p.research_substage_id}")
        
        # Подготовка данных для диаграммы Ганта
        gantt_data = []
        today = timezone.now().date()
        
        # Собираем все даты окончания для определения ближайших к сегодня
        all_end_dates = []
        
        # Словарь для хранения цветов НИР
        research_task_colors = {}
        color_palette = [
            '#0d6efd', '#198754', '#dc3545', '#fd7e14', '#6f42c1',
            '#d63384', '#20c997', '#0dcaf0', '#ffc107', '#6610f2',
            '#009688', '#9c27b0', '#ff9800', '#795548', '#607d8b'
        ]
        color_index = 0
        
        for product in all_products:
            # Получаем связанные объекты
            research_substage = product.research_substage
            research_stage = product.research_stage
            if not research_stage and research_substage:
                research_stage = research_substage.stage
            research_task = product.research_task
            if not research_task and research_stage:
                research_task = research_stage.research_task
            
            # Получаем информацию о подэтапе
            substage_info = None
            substage_start = None
            substage_end = None
            
            if research_substage:
                substage_info = {
                    'id': research_substage.id,
                    'number': research_substage.substage_number,
                    'title': research_substage.title,
                    'start_date': research_substage.start_date,
                    'end_date': research_substage.end_date,
                }
                # Срок продукции = срок подэтапа
                substage_start = research_substage.start_date
                substage_end = research_substage.end_date
            
            # Используем сроки подэтапа как основные
            planned_start = substage_start or product.planned_start
            planned_end = substage_end or product.planned_end
            
            # Сортировочная дата
            sort_date = planned_end if planned_end else product.created_date
            
            # Вычисляем статус выполнения и цвет
            today = timezone.now().date()
            is_completed = product.status == 'completed'
            
            # Проверяем, осталось ли менее 2 месяцев до срока
            days_until_due = None
            due_date_warning = False
            if planned_end and not is_completed:
                days_until_due = (planned_end - today).days
                due_date_warning = days_until_due <= 60
            
            # Цвет индикатора выполнения
            status_color = 'success' if is_completed else 'danger'
            
            # Назначаем цвет для НИР (для Ганта)
            research_task_color = '#6c757d'  # серый по умолчанию
            if research_task:
                if research_task.id not in research_task_colors:
                    research_task_colors[research_task.id] = color_palette[color_index % len(color_palette)]
                    color_index += 1
                research_task_color = research_task_colors[research_task.id]
            
            items.append({
                'type': 'product',
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'status': product.status,
                'is_completed': is_completed,
                'status_color': status_color,
                'due_date': planned_end,
                'due_date_warning': due_date_warning,
                'days_until_due': days_until_due,
                'planned_start': planned_start,
                'planned_end': planned_end,
                'sort_date': sort_date,
                'is_overdue': product.is_overdue,
                'responsible': product.responsible,
                'substage': substage_info,
                'stage': research_stage,
                'research_task': research_task,
                'get_status_display': product.get_status_display(),
                'status_color_badge': {
                    'pending': 'secondary',
                    'in_progress': 'primary',
                    'completed': 'success',
                    'delayed': 'danger',
                    'cancelled': 'dark'
                }.get(product.status, 'secondary'),
                'completion_percent': product.completion_percent,
            })
            
            # Добавляем в данные для Ганта
            # Используем даты подэтапа, продукции или значения по умолчанию
            gantt_start = planned_start
            gantt_end = planned_end
            
            # Если не хватает одной из дат, пробуем получить из подэтапа
            if (not gantt_start or not gantt_end) and research_substage:
                gantt_start = gantt_start or research_substage.start_date
                gantt_end = gantt_end or research_substage.end_date
            
            # Если всё ещё не хватает дат, пробуем этап
            if (not gantt_start or not gantt_end) and research_stage:
                gantt_start = gantt_start or research_stage.start_date
                gantt_end = gantt_end or research_stage.end_date
            
            # Если всё ещё не хватает дат, пробуем НИР
            if (not gantt_start or not gantt_end) and research_task:
                gantt_start = gantt_start or research_task.start_date
                gantt_end = gantt_end or research_task.end_date
            
            # Если всё ещё нет дат, используем текущий год как запасной вариант
            if not gantt_start or not gantt_end:
                current_year = timezone.now().year
                gantt_start = gantt_start or date(current_year, 1, 1)
                gantt_end = gantt_end or date(current_year, 12, 31)
            
            # DEBUG: Print what dates we're using
            print(f"Product {product.id}: gantt_start={gantt_start}, gantt_end={gantt_end}")
            
            # Проверяем, попадает ли продукция в выбранный период
            if gantt_end >= start_date and gantt_start <= end_date:
                # Считаем разницу в днях от сегодня (для определения ближайших)
                days_diff = abs((gantt_end - today).days)
                all_end_dates.append({
                    'product_id': product.id,
                    'days_diff': days_diff,
                    'end_date': gantt_end
                })
                
                gantt_data.append({
                    'id': product.id,
                    'name': product.name,
                    'start': gantt_start.isoformat(),
                    'end': gantt_end.isoformat(),
                    'status': product.status,
                    'color': research_task_color,
                    'completion': product.completion_percent,
                    'is_overdue': product.is_overdue,
                    'due_date_warning': due_date_warning,
                    'substage_number': research_substage.substage_number if research_substage else None,
                    'research_task_title': research_task.title if research_task else None,
                    'research_task_color': research_task_color,
                    'days_to_end': days_diff,
                })
        
        # Определяем ближайшие к сегодня даты (минимальная разница в днях)
        closest_product_ids = set()
        if all_end_dates:
            min_days = min(item['days_diff'] for item in all_end_dates)
            # Находим все продукты с минимальной разницей (может быть несколько)
            closest_product_ids = {item['product_id'] for item in all_end_dates if item['days_diff'] == min_days}
            print(f"Ближайшие продукты (мин. дней: {min_days}): {closest_product_ids}")
        
        # Помечаем ближайшие продукты в gantt_data
        for item in gantt_data:
            item['is_closest'] = item['id'] in closest_product_ids
        
        # Формируем список уникальных НИР для легенды
        research_tasks_list = []
        for rt_id, color in research_task_colors.items():
            rt = ResearchTask.objects.filter(id=rt_id).first()
            if rt:
                research_tasks_list.append({
                    'id': rt.id,
                    'title': rt.title,
                    'color': color
                })
        # Фильтрация по типу
        if item_type != 'all':
            items = [item for item in items if item['type'] == item_type]
        
        # Сортировка по дате
        today = timezone.now().date()
        
        def sort_key(item):
            date_val = item.get('sort_date')
            if date_val:
                if isinstance(date_val, datetime):
                    date_val = date_val.date()
                return (date_val - today).days if date_val else 9999
            return 9999
        
        items.sort(key=sort_key)
        
        # Создаем список доступных годов для фильтра
        available_years = set()
        for product in all_products:
            if product.planned_start:
                available_years.add(product.planned_start.year)
            if product.planned_end:
                available_years.add(product.planned_end.year)
        available_years = sorted(list(available_years))
        if not available_years:
            available_years = [timezone.now().year]
        
        # Статистика
        context = {
            'employee': employee,
            'items': items,
            'current_type': item_type,
            'staff_positions': staff_positions,
            'org_structure': org_structure,
            'tasks_count': len([i for i in items if i['type'] == 'task']),
            'subtasks_count': len([i for i in items if i['type'] == 'subtask']),
            'products_count': len([i for i in items if i['type'] == 'product']),
            'research_tasks_count': len([i for i in items if i['type'] == 'research_task']),
            'research_stages_count': len([i for i in items if i['type'] == 'research_stage']),
            'research_substages_count': len([i for i in items if i['type'] == 'research_substage']),
            'overdue_count': len([i for i in items if i.get('is_overdue')]),
            # Данные для Ганта
            'gantt_data': json.dumps(gantt_data),
            'gantt_year': int(gantt_year) if gantt_year and gantt_year.isdigit() else timezone.now().year,
            'gantt_start_date': start_date.isoformat(),
            'gantt_end_date': end_date.isoformat(),
            'available_years': available_years,
            'research_tasks_list': research_tasks_list,
            # Сегодняшняя дата для отображения линии
            'today_date': today.isoformat(),
        }
        
        print(f"\n=== СТАТИСТИКА ===")
        print(f"products_count в контексте: {context['products_count']}")
        print(f"gantt_data count: {len(gantt_data)}")
        print(f"gantt_data sample: {gantt_data[:2] if gantt_data else 'EMPTY'}")
        print(f"start_date: {start_date}, end_date: {end_date}")
        print(f"today_date: {context['today_date']}")
        
        return render(request, 'tasks/employee_detail.html', context)
        
    except Exception as e:
        print(f"ОШИБКА в employee_detail: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Ошибка при загрузке данных: {str(e)}')
        return redirect('employee_list')
    
@login_required
def employee_create(request):
    """Создание нового сотрудника"""
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.created_by = request.user
            employee.save()
            messages.success(request, f'Сотрудник {employee.full_name} успешно добавлен!')
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    
    return render(request, 'tasks/employee_form.html', {
        'form': form,
        'title': 'Добавление сотрудника'
    })


@login_required
def employee_update(request, employee_id):
    """Редактирование сотрудника"""
    employee = get_object_or_404(Employee, id=employee_id)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f'Данные сотрудника {employee.full_name} обновлены!')
            return redirect('employee_detail', employee_id=employee.id)
    else:
        form = EmployeeForm(instance=employee)
    
    return render(request, 'tasks/employee_form.html', {
        'form': form,
        'title': f'Редактирование: {employee.full_name}',
        'employee': employee
    })

@login_required
def employee_toggle_active(request, employee_id):
    """Активация/деактивация сотрудника"""
    employee = get_object_or_404(Employee, id=employee_id)
    employee.is_active = not employee.is_active
    employee.save()
    
    status = "активирован" if employee.is_active else "деактивирован"
    messages.success(request, f'Сотрудник {employee.full_name} {status}')
    
    return redirect('employee_detail', employee_id=employee.id)

@login_required
def employee_delete(request, employee_id):
    """Удаление сотрудника"""
    employee = get_object_or_404(Employee, id=employee_id)
    
    # Проверяем, есть ли у сотрудника активные задачи
    active_tasks = Task.objects.filter(assigned_to=employee, status__in=['todo', 'in_progress'])
    active_subtasks = Subtask.objects.filter(
        performers=employee, 
        status__in=['pending', 'in_progress']
    )
    
    # Проверяем продукцию, где сотрудник является ответственным или исполнителем
    products_as_responsible = ResearchProduct.objects.filter(
        responsible=employee, 
        status__in=['pending', 'in_progress']
    )
    products_as_performer = ResearchProduct.objects.filter(
        product_performers__employee=employee,
        status__in=['pending', 'in_progress']
    ).distinct()
    
    # Если есть активные задания, показываем предупреждение
    if active_tasks.exists() or active_subtasks.exists() or products_as_responsible.exists() or products_as_performer.exists():
        messages.error(
            request, 
            f'Нельзя удалить сотрудника "{employee.full_name}". '
            f'У него есть активные задачи или продукция. '
            f'Сначала завершите или переназначьте задачи.'
        )
        return redirect('employee_detail', employee_id=employee.id)
    
    if request.method == 'POST':
        full_name = employee.full_name
        try:
            # Очищаем связи перед удалением
            # Удаляем из ManyToMany полей задач
            for task in Task.objects.filter(assigned_to=employee):
                task.assigned_to.remove(employee)
            
            # Удаляем из ManyToMany полей подзадач
            for subtask in Subtask.objects.filter(performers=employee):
                subtask.performers.remove(employee)
            
            # Обнуляем ответственных
            Subtask.objects.filter(responsible=employee).update(responsible=None)
            ResearchProduct.objects.filter(responsible=employee).update(responsible=None)
            
            # Удаляем связи ProductPerformer
            ProductPerformer.objects.filter(employee=employee).delete()
            
            # Удаляем штатные позиции
            employee.staff_positions.all().delete()
            
            # Удаляем сотрудника
            employee.delete()
            
            messages.success(request, f'Сотрудник {full_name} удален из системы')
            
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')
        
        return redirect('employee_list')
    
    # GET запрос - показываем страницу подтверждения
    return render(request, 'tasks/employee_confirm_delete.html', {'employee': employee})

@login_required
def employee_import(request):
    """Импорт сотрудников из Excel"""
    if request.method == 'POST':
        form = EmployeeImportForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            
            try:
                # Читаем Excel файл
                df = pd.read_excel(excel_file)
                
                # Проверяем наличие необходимых колонок
                required_columns = ['Фамилия', 'Имя', 'Должность', 'Email']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    messages.error(request, f'В файле отсутствуют обязательные колонки: {", ".join(missing_columns)}')
                    return redirect('employee_import')
                
                # Импортируем данные
                success_count = 0
                error_count = 0
                errors = []
                
                for index, row in df.iterrows():
                    try:
                        email = row.get('Email', '')
                        if not email:
                            errors.append(f'Строка {index + 2}: отсутствует Email')
                            error_count += 1
                            continue
                        
                        employee, created = Employee.objects.update_or_create(
                            email=email,
                            defaults={
                                'last_name': row.get('Фамилия', ''),
                                'first_name': row.get('Имя', ''),
                                'patronymic': row.get('Отчество', ''),
                                'position': row.get('Должность', ''),
                                'phone': row.get('Телефон', ''),
                                'department': row.get('Отдел', 'other'),
                                'laboratory': row.get('Лаборатория', ''),
                                'notes': row.get('Заметки', ''),
                                'created_by': request.user,
                            }
                        )
                        success_count += 1
                            
                    except Exception as e:
                        errors.append(f'Строка {index + 2}: {str(e)}')
                        error_count += 1
                
                if success_count > 0:
                    messages.success(request, f'Успешно импортировано {success_count} сотрудников')
                if error_count > 0:
                    messages.warning(request, f'Ошибок при импорте: {error_count}')
                if errors:
                    request.session['import_errors'] = errors[:10]
                
                return redirect('employee_list')
                
            except Exception as e:
                messages.error(request, f'Ошибка при чтении файла: {str(e)}')
                return redirect('employee_import')
    else:
        form = EmployeeImportForm()
    
    errors = request.session.pop('import_errors', [])
    
    return render(request, 'tasks/employee_import.html', {
        'form': form,
        'errors': errors
    })


@login_required
def employee_export(request):
    """Экспорт сотрудников в Excel"""
    employees = Employee.objects.all().order_by('last_name', 'first_name')
    
    data = []
    for emp in employees:
        data.append({
            'Фамилия': emp.last_name,
            'Имя': emp.first_name,
            'Отчество': emp.patronymic or '',
            'Должность': emp.position,
            'Email': emp.email,
            'Телефон': emp.phone or '',
            'Отдел': emp.get_department_display(),
            'Лаборатория': emp.get_laboratory_display() if emp.laboratory else '',
            'Дата найма': emp.hire_date.strftime('%d.%m.%Y') if emp.hire_date else '',
            'Активен': 'Да' if emp.is_active else 'Нет',
            'Заметки': emp.notes or '',
        })
    
    df = pd.DataFrame(data)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=employees_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Сотрудники', index=False)
    
    return response


@login_required
def employee_export_template(request):
    """Скачать шаблон Excel для импорта"""
    template_data = [{
        'Фамилия': 'Иванов',
        'Имя': 'Иван',
        'Отчество': 'Иванович',
        'Должность': 'Разработчик',
        'Email': 'ivanov@example.com',
        'Телефон': '+7 (999) 123-45-67',
        'Отдел': 'development',
        'Лаборатория': 'lab1',
        'Заметки': 'Пример заполнения',
    }]
    
    df = pd.DataFrame(template_data)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=employee_import_template.xlsx'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Шаблон', index=False)
    
    return response

@login_required
def create_external_employee(request):
    """Создание внешнего сотрудника (которого нет в штате)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            full_name = data.get('full_name', '').strip()
            position = data.get('position', '').strip()
            organization = data.get('organization', '').strip()
            notes = data.get('notes', '').strip()
            
            if not full_name:
                return JsonResponse({'success': False, 'error': 'ФИО обязательно'})
            
            # Разбираем ФИО
            name_parts = full_name.split()
            last_name = name_parts[0] if len(name_parts) > 0 else ''
            first_name = name_parts[1] if len(name_parts) > 1 else ''
            patronymic = name_parts[2] if len(name_parts) > 2 else ''
            
            # Создаем сотрудника
            employee = Employee.objects.create(
                last_name=last_name,
                first_name=first_name,
                patronymic=patronymic,
                position=position or 'Внешний сотрудник',
                email=f"external_{hash(full_name)}@temp.local",  # Временный email
                department='other',
                is_active=True,
                notes=f"Внешний сотрудник. Организация: {organization}\n{notes}".strip()
            )
            
            return JsonResponse({
                'success': True,
                'employee_id': employee.id,
                'full_name': employee.full_name
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})

@login_required
def employee_tasks(request, employee_id):
    """Список задач сотрудника"""
    employee = get_object_or_404(Employee, id=employee_id)
    
    tasks = employee.tasks.all().order_by('-created_date')
    
    status = request.GET.get('status', '')
    if status:
        tasks = tasks.filter(status=status)
    
    context = {
        'employee': employee,
        'tasks': tasks,
        'status_choices': Task.STATUS_CHOICES,
        'current_status': status,
    }
    return render(request, 'tasks/employee_tasks.html', context)
