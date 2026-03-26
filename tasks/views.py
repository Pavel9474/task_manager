from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import Task, Employee, Subtask, ResearchTask, ResearchStage, ResearchSubstage, Department, Position, StaffPosition, ResearchProduct
from .forms import TaskForm, TaskWithImportForm, StaffImportForm
from .forms import ResearchTaskForm, ResearchStageForm, ResearchSubstageForm
from .forms_subtask import SubtaskForm, SubtaskBulkCreateForm
from .forms_employee import EmployeeForm, EmployeeImportForm
from .utils.docx_importer import ResearchDocxImporter
import pandas as pd
from django.template.loader import render_to_string
from datetime import datetime
import tempfile
from django.db.models import Prefetch, Count
from django.db.models import Q
from .services.org_service import OrganizationService
import os
from .decorators import log_view
from django.db import transaction
import logging

from django.core.cache import cache

logger = logging.getLogger('tasks')
# ============= АУТЕНТИФИКАЦИЯ =============

@login_required
def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать!')
            return redirect('task_list')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


# ============= УПРАВЛЕНИЕ ЗАДАЧАМИ =============

@login_required
def task_list(request):

    """Список задач пользователя"""
    tasks = Task.objects.filter(user=request.user)
    
    # Фильтрация по статусу
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        tasks = tasks.filter(status=status_filter)
    
    # Фильтрация по исполнителю
    employee_filter = request.GET.get('employee', '')
    if employee_filter:
        tasks = tasks.filter(assigned_to__id=employee_filter)
    
    # Поиск
    search_query = request.GET.get('search', '')
    if search_query:
        tasks = tasks.filter(title__icontains=search_query)
    
    # Сортировка
    sort_by = request.GET.get('sort', '-created_date')
    tasks = tasks.order_by(sort_by)
    
    # Подсчет задач по статусам для статистики
    todo_count = tasks.filter(status='todo').count()
    in_progress_count = tasks.filter(status='in_progress').count()
    done_count = tasks.filter(status='done').count()
    overdue_count = tasks.filter(
        status__in=['todo', 'in_progress'],
        due_date__lt=timezone.now()
    ).count()
    
    # Получаем всех сотрудников для фильтра
    employees = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
    
    context = {
        'tasks': tasks,
        'status_filter': status_filter,
        'employee_filter': employee_filter,
        'search_query': search_query,
        'sort_by': sort_by,
        'now': timezone.now(),
        'todo_count': todo_count,
        'in_progress_count': in_progress_count,
        'done_count': done_count,
        'overdue_count': overdue_count,
        'employees': employees,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_detail(request, task_id):
    """Детальная информация о задаче"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    return render(request, 'tasks/task_detail.html', {'task': task})

@login_required
def task_create(request):
    """Создание новой задачи с возможностью импорта из ТЗ"""
    if request.method == 'POST':
        form = TaskWithImportForm(request.POST, request.FILES)
        
        # Проверяем, загружен ли файл ТЗ
        tz_file = request.FILES.get('tz_file')
        
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            
            # Если есть файл ТЗ - импортируем из него
            if tz_file:
                try:
                    # Сохраняем файл временно
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                        for chunk in tz_file.chunks():
                            tmp_file.write(chunk)
                        tmp_path = tmp_file.name
                    
                    print(f"\n=== НАЧАЛО ИМПОРТА ===")
                    print(f"Файл сохранен: {tmp_path}")
                    
                    # Импортируем структуру из ТЗ
                    importer = ResearchDocxImporter(tmp_path)
                    
                    # Получаем данные из ТЗ
                    tz_data = importer.parse_research_task()
                    
                    print(f"\nДанные из ТЗ:")
                    print(f"Название: {tz_data.get('title')}")
                    print(f"Количество этапов: {len(tz_data.get('stages', []))}")
                    
                    # Устанавливаем название задачи из ТЗ, если не указано вручную
                    if not task.title and tz_data.get('title'):
                        task.title = tz_data['title']
                    
                    # Сохраняем задачу
                    task.save()
                    form.save_m2m()  # Сохраняем связи many-to-many
                    
                    print(f"\nСоздана задача ID: {task.id}")
                    
                    # ВАЖНО: Удаляем существующие подзадачи, если они есть
                    existing_count = task.subtasks.count()
                    if existing_count > 0:
                        print(f"Удаляем {existing_count} существующих подзадач")
                        task.subtasks.all().delete()
                    
                    # Создаем этапы и подэтапы
                    if tz_data.get('stages'):
                        importer.create_task_structure(task, tz_data['stages'])
                        
                        # Назначаем исполнителей по умолчанию, если они выбраны в форме
                        if form.cleaned_data.get('assigned_to'):
                            default_performers = form.cleaned_data['assigned_to']
                            importer.assign_default_performers(task, default_performers)
                        
                        messages.success(request, f'Задача успешно создана с импортом из ТЗ. Создано этапов: {len(tz_data.get("stages", []))}')
                    else:
                        messages.warning(request, 'Задача создана, но этапы не найдены в ТЗ')
                    
                    # Удаляем временный файл
                    os.unlink(tmp_path)
                    print(f"Временный файл удален")
                    print(f"=== КОНЕЦ ИМПОРТА ===\n")
                    
                except Exception as e:
                    print(f"\n❌ ОШИБКА ИМПОРТА: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    messages.error(request, f'Ошибка при импорте из ТЗ: {str(e)}')
                    
                    # Если импорт не удался, но задача создана без названия - показываем форму с ошибкой
                    if not task.title:
                        return render(request, 'tasks/task_form.html', {
                            'form': form, 
                            'title': 'Создать задачу',
                            'employees': Employee.objects.filter(is_active=True),
                            'is_create': True,
                            'error': str(e)
                        })
            else:
                # Обычное создание задачи без импорта
                task.save()
                form.save_m2m()
                messages.success(request, 'Задача успешно создана!')
            
            return redirect('task_list')
    else:
        form = TaskWithImportForm()
    
    employees = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
    
    return render(request, 'tasks/task_form.html', {
        'form': form, 
        'title': 'Создать задачу',
        'employees': employees,
        'is_create': True
    })
@login_required
def task_update(request, task_id):
    """Редактирование задачи"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Задача успешно обновлена!')
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    
    # Получаем всех активных сотрудников для отображения в шаблоне
    employees = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
    
    return render(request, 'tasks/task_form.html', {
        'form': form, 
        'title': 'Редактировать задачу',
        'task': task,
        'employees': employees,
        'is_create': False
    })

@login_required
def task_delete(request, task_id):
    """Удаление задачи"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        try:
            # Отключаем каскадное удаление
            # Сначала обнуляем связи
            for subtask in task.subtasks.all():
                # Обнуляем ссылки на подэтапы в продукции
                ResearchProduct.objects.filter(subtask=subtask).update(subtask=None)
                
                # Очищаем связи исполнителей
                subtask.performers.clear()
            
            # Удаляем подэтапы
            task.subtasks.all().delete()
            
            # Удаляем задачу
            task.delete()
            
            messages.success(request, f'Задача "{task.title}" успешно удалена')
            
        except Exception as e:
            messages.error(request, f'Ошибка при удалении задачи: {str(e)}')
            import traceback
            print(traceback.format_exc())
        
        return redirect('task_list')
    
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})

@login_required
def task_complete(request, task_id):
    """Отметить задачу как выполненную"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.status = 'done'
    task.end_time = timezone.now()
    task.save()
    messages.success(request, f'Задача "{task.title}" отмечена как выполненная!')
    return redirect('task_list')


@login_required
def task_start(request, task_id):
    """Начать выполнение задачи"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if task.can_start():
        task.start_time = timezone.now()
        task.status = 'in_progress'
        task.save()
        messages.success(request, f'Задача "{task.title}" начата')
    else:
        messages.error(request, 'Нельзя начать эту задачу')
    
    return redirect('task_detail', task_id=task.id)


@login_required
def task_finish(request, task_id):
    """Завершить выполнение задачи"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        if task.can_complete():
            task.end_time = timezone.now()
            task.status = 'done'
            task.save()
            messages.success(request, f'Задача "{task.title}" выполнена!')
        else:
            messages.error(request, 'Нельзя завершить эту задачу')
        
        return redirect('task_detail', task_id=task.id)
    
    return render(request, 'tasks/task_finish.html', {'task': task})


@login_required
def task_reset_time(request, task_id):
    """Сбросить время начала/окончания задачи"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        task.start_time = None
        task.end_time = None
        if task.status == 'in_progress':
            task.status = 'todo'
        task.save()
        messages.success(request, f'Время задачи сброшено')
        return redirect('task_detail', task_id=task.id)
    
    return render(request, 'tasks/task_reset_time.html', {'task': task})


# ============= УПРАВЛЕНИЕ СОТРУДНИКАМИ =============

@login_required
def employee_list(request):
    """Список сотрудников"""
    employees = Employee.objects.all()
    
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
    
    context = {
        'page_obj': page_obj,
        'departments': Employee.DEPARTMENT_CHOICES,
        'laboratories': Employee.LABORATORY_CHOICES,
        'current_filters': {
            'department': department,
            'laboratory': laboratory,
            'is_active': is_active,
            'search': search,
            'sort': sort,
        }
    }
    return render(request, 'tasks/employee_list.html', context)


@login_required
def employee_detail(request, employee_id):
    """Детальная информация о сотруднике"""
    employee = get_object_or_404(Employee, id=employee_id)
    
    # 👇 НОВЫЙ КОД: Получаем штатные позиции сотрудника
    staff_positions = employee.staff_positions.filter(is_active=True)
    
    # 👇 НОВЫЙ КОД: Получаем организационную структуру
    org_structure = employee.get_organization_structure()
    
    # Получаем тип отображения (все, только задачи, только этапы)
    item_type = request.GET.get('type', 'all')
    
    # Собираем все задачи и подзадачи сотрудника
    items = []
    
    # Добавляем задачи, где сотрудник является исполнителем
    tasks = employee.tasks.all()
    for task in tasks:
        # Определяем дату для сортировки (дедлайн задачи)
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
            'assigned_to': task.assigned_to,
            'task': task,  # оригинальный объект для ссылок
            'get_priority_display': task.get_priority_display,
            'get_status_display': task.get_status_display,
            'priority_color': {
                'critical': 'danger',
                'high': 'warning',
                'medium': 'info',
                'low': 'success'
            }.get(task.priority, 'secondary')
        })
    
    # Добавляем подзадачи, где сотрудник является исполнителем или ответственным
    subtasks_as_performer = employee.subtasks.all()
    subtasks_as_responsible = employee.responsible_subtasks.all()
    all_subtasks = (subtasks_as_performer | subtasks_as_responsible).distinct()
    
    for subtask in all_subtasks:
        # Определяем дату для сортировки (планируемое окончание этапа)
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
            'stage_number': subtask.stage_number,
            'task': subtask.task,  # родительская задача
            'responsible': subtask.responsible,
            'performers': subtask.performers,
            'progress': subtask.progress,
            'get_priority_display': subtask.get_priority_display,
            'get_status_display': subtask.get_status_display,
            'priority_color': subtask.priority_color
        })
    
    # Фильтрация по типу
    if item_type == 'tasks':
        items = [item for item in items if item['type'] == 'task']
    elif item_type == 'subtasks':
        items = [item for item in items if item['type'] == 'subtask']
    
    # Сортировка: сначала по дате (чем ближе к сегодня, тем выше),
    # затем просроченные в начало, затем без даты в конец
    from datetime import date, datetime
    today = timezone.now().date()
    
    def sort_key(item):
        date_val = item['sort_date']
        if date_val:
            # Преобразуем datetime в date для сравнения
            if isinstance(date_val, datetime):
                date_val = date_val.date()
            # Считаем разницу в днях от сегодня
            days_diff = (date_val - today).days if date_val else 9999
            # Отрицательные значения (просроченные) должны быть в начале
            return (days_diff if days_diff >= 0 else -9999 + days_diff, 0)
        else:
            return (9999, 1)  # без даты в самый конец
    
    items.sort(key=sort_key)
    
    context = {
        'employee': employee,
        'items': items,
        'current_type': item_type,
        # 👇 НОВЫЙ КОД: Добавляем новые переменные в контекст
        'staff_positions': staff_positions,
        'org_structure': org_structure,
    }
    return render(request, 'tasks/employee_detail.html', context)



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
def employee_delete(request, employee_id):
    """Удаление сотрудника"""
    employee = get_object_or_404(Employee, id=employee_id)
    
    if request.method == 'POST':
        full_name = employee.full_name
        employee.delete()
        messages.success(request, f'Сотрудник {full_name} удален из системы')
        return redirect('employee_list')
    
    return render(request, 'tasks/employee_confirm_delete.html', {'employee': employee})


@login_required
def employee_toggle_active(request, employee_id):
    """Активация/деактивация сотрудника"""
    employee = get_object_or_404(Employee, id=employee_id)
    employee.is_active = not employee.is_active
    employee.save()
    
    status = "активирован" if employee.is_active else "деактивирован"
    messages.success(request, f'Сотрудник {employee.full_name} {status}')
    
    return redirect('employee_detail', employee_id=employee.id)


# ============= ИМПОРТ/ЭКСПОРТ EXCEL =============

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


# ============= НАЗНАЧЕНИЕ ИСПОЛНИТЕЛЕЙ =============

@login_required
def task_assign_employees(request, task_id):
    """Назначение исполнителей на задачу"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        employee_ids = request.POST.getlist('employees')
        task.assigned_to.set(employee_ids)
        task.save()
        
        count = len(employee_ids)
        messages.success(request, f'На задачу назначено {count} исполнителей')
        return redirect('task_detail', task_id=task.id)
    
    employees = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
    
    department = request.GET.get('department', '')
    if department:
        employees = employees.filter(department=department)
    
    search = request.GET.get('search', '')
    if search:
        employees = employees.filter(
            Q(last_name__icontains=search) |
            Q(first_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    assigned_ids = task.assigned_to.values_list('id', flat=True)
    
    context = {
        'task': task,
        'employees': employees,
        'assigned_ids': list(assigned_ids),
        'departments': Employee.DEPARTMENT_CHOICES,
        'current_filters': {
            'department': department,
            'search': search,
        }
    }
    return render(request, 'tasks/task_assign_employees.html', context)


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


# ============= СТАТИСТИКА И ДАШБОРДЫ =============

@login_required
def task_statistics(request):
    """Статистика по задачам"""
    tasks = Task.objects.filter(user=request.user)
    now = timezone.now()
    
    active_tasks = tasks.filter(
        status='in_progress',
        start_time__isnull=False,
        end_time__isnull=True
    ).count()
    
    completed_tasks = tasks.filter(status='done', start_time__isnull=False, end_time__isnull=False)
    total_duration = 0
    for task in completed_tasks:
        if task.end_time and task.start_time:
            duration = (task.end_time - task.start_time).total_seconds() / 3600
            total_duration += duration
    
    avg_duration = round(total_duration / completed_tasks.count(), 1) if completed_tasks.exists() else 0
    
    priority_stats = tasks.values('priority').annotate(count=Count('priority'))
    
    stats = {
        'total': tasks.count(),
        'todo': tasks.filter(status='todo').count(),
        'in_progress': tasks.filter(status='in_progress').count(),
        'done': tasks.filter(status='done').count(),
        'overdue': tasks.filter(
            status__in=['todo', 'in_progress'],
            due_date__lt=now
        ).count(),
        'high_priority': tasks.filter(priority='high').count(),
        'medium_priority': tasks.filter(priority='medium').count(),
        'low_priority': tasks.filter(priority='low').count(),
        'active_now': active_tasks,
        'avg_duration': avg_duration,
        'completed_count': completed_tasks.count(),
        'priority_stats': priority_stats,
    }
    
    return render(request, 'tasks/statistics.html', {'stats': stats})


@login_required
def team_dashboard(request):
    """Дашборд команды"""
    total_employees = Employee.objects.filter(is_active=True).count()
    
    all_tasks = Task.objects.all()
    active_tasks = all_tasks.filter(
        status='in_progress',
        start_time__isnull=False,
        end_time__isnull=True
    ).count()
    
    employees_with_tasks = Employee.objects.filter(
        is_active=True,
        tasks__isnull=False
    ).distinct().annotate(
        task_count=Count('tasks'),
        todo_count=Count('tasks', filter=Q(tasks__status='todo')),
        in_progress_count=Count('tasks', filter=Q(tasks__status='in_progress')),
        done_count=Count('tasks', filter=Q(tasks__status='done'))
    ).order_by('-task_count')[:10]
    
    recent_assignments = Task.objects.filter(
        assigned_to__isnull=False
    ).order_by('-created_date')[:10]
    
    context = {
        'total_employees': total_employees,
        'active_tasks': active_tasks,
        'employees_with_tasks': employees_with_tasks,
        'recent_assignments': recent_assignments,
    }
    return render(request, 'tasks/team_dashboard.html', context)


# ============= API =============

@login_required
def employee_search_api(request):
    """API для поиска сотрудников"""
    query = request.GET.get('q', '')
    employees = Employee.objects.filter(is_active=True)
    
    if query:
        employees = employees.filter(
            Q(last_name__icontains=query) |
            Q(first_name__icontains=query) |
            Q(email__icontains=query)
        )
    
    employees = employees[:10]
    
    data = [{
        'id': emp.id,
        'text': f"{emp.full_name} ({emp.position})",
        'email': emp.email
    } for emp in employees]
    
    return JsonResponse({'results': data})

@login_required
def task_assign_employees_ajax(request, task_id):
    """AJAX версия назначения исполнителей"""
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id, user=request.user)
        employee_ids = request.POST.getlist('employees[]')
        task.assigned_to.set(employee_ids)
        
        return JsonResponse({
            'success': True,
            'message': f'Назначено {len(employee_ids)} исполнителей',
            'assigned': list(employee_ids)
        })
    
    elif request.method == 'GET':
        task = get_object_or_404(Task, id=task_id, user=request.user)
        employees = Employee.objects.filter(is_active=True)
        
        # Фильтрация
        search = request.GET.get('search', '')
        if search:
            employees = employees.filter(
                Q(last_name__icontains=search) |
                Q(first_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        html = render_to_string('tasks/partials/employee_list_ajax.html', {
            'employees': employees,
            'assigned_ids': task.assigned_to.values_list('id', flat=True)
        })
        
        return JsonResponse({
            'success': True,
            'html': html,
            'count': employees.count()
        })
@login_required
def task_update_status_ajax(request, task_id):
    """AJAX обновление статуса задачи"""
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id, user=request.user)
        new_status = request.POST.get('status')
        
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            if new_status == 'in_progress' and not task.start_time:
                task.start_time = timezone.now()
            elif new_status == 'done' and not task.end_time:
                task.end_time = timezone.now()
            
            task.save()
            
            return JsonResponse({
                'success': True,
                'status': task.status,
                'status_display': task.get_status_display(),
                'start_time': task.start_time.strftime('%H:%M %d.%m.%Y') if task.start_time else None,
                'end_time': task.end_time.strftime('%H:%M %d.%m.%Y') if task.end_time else None,
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})
from .models import Subtask
from .forms_subtask import SubtaskForm, SubtaskBulkCreateForm


# ============= УПРАВЛЕНИЕ ПОДЗАДАЧАМИ (ЭТАПАМИ) =============

@login_required
def subtask_list(request, task_id):
    """Список подзадач для задачи с группировкой по этапам"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    # Получаем все подзадачи
    all_subtasks = task.subtasks.all()
    
    # Разделяем на этапы (целые числа) и подэтапы (с точкой)
    stages = []
    substages_by_stage = {}
    
    for subtask in all_subtasks:
        stage_num = subtask.stage_number
        # Проверяем, является ли номер этапа целым числом (нет точки)
        if '.' not in stage_num:
            stages.append(subtask)
            substages_by_stage[stage_num] = []
    
    # Сортируем этапы по номеру
    stages.sort(key=lambda x: float(x.stage_number))
    
    # Группируем подэтапы по этапам
    for subtask in all_subtasks:
        if '.' in subtask.stage_number:
            # Получаем номер основного этапа (до точки)
            main_stage = subtask.stage_number.split('.')[0]
            if main_stage in substages_by_stage:
                substages_by_stage[main_stage].append(subtask)
    
    # Сортируем подэтапы в каждом этапе
    for stage_num in substages_by_stage:
        substages_by_stage[stage_num].sort(key=lambda x: float(x.stage_number))
    
    # Добавляем количество подэтапов в каждый этап
    for stage in stages:
        stage.substages_count = len(substages_by_stage.get(stage.stage_number, []))
    
    # Загружаем продукцию из базы данных для каждого подэтапа
    for subtask in all_subtasks:
        # Получаем объекты ResearchProduct, связанные с этим подэтапом
        subtask.products_list = ResearchProduct.objects.filter(subtask=subtask)
    
    # Вычисляем общий прогресс
    total_subtasks = all_subtasks.count()
    completed_subtasks = all_subtasks.filter(status='completed').count()
    progress = int((completed_subtasks / total_subtasks) * 100) if total_subtasks > 0 else 0
    
    context = {
        'task': task,
        'stages': stages,
        'substages_by_stage': substages_by_stage,
        'employees': Employee.objects.filter(is_active=True),
        'progress': progress,
    }
    return render(request, 'tasks/subtask_list.html', context)


@login_required
def subtask_create(request, task_id):
    """Создание подзадачи"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        form = SubtaskForm(request.POST, task=task)
        if form.is_valid():
            subtask = form.save(commit=False)
            subtask.task = task
            subtask.save()
            form.save_m2m()
            
            if subtask.performers.count() == 1 and not subtask.responsible:
                subtask.responsible = subtask.performers.first()
                subtask.save()
            
            messages.success(request, f'Этап {subtask.stage_number} успешно создан')
            return redirect('subtask_list', task_id=task.id)
    else:
        form = SubtaskForm(task=task)
    
    return render(request, 'tasks/subtask_form.html', {
        'form': form,
        'task': task,
        'title': f'Добавление этапа к задаче: {task.title}'
    })


@login_required
def subtask_update(request, subtask_id):
    """Редактирование подзадачи"""
    subtask = get_object_or_404(Subtask, id=subtask_id, task__user=request.user)
    
    if request.method == 'POST':
        form = SubtaskForm(request.POST, instance=subtask, task=subtask.task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Этап {subtask.stage_number} обновлен')
            return redirect('subtask_list', task_id=subtask.task.id)
    else:
        form = SubtaskForm(instance=subtask, task=subtask.task)
    
    return render(request, 'tasks/subtask_form.html', {
        'form': form,
        'task': subtask.task,
        'subtask': subtask,
        'title': f'Редактирование этапа {subtask.stage_number}'
    })


@login_required
def subtask_delete(request, subtask_id):
    """Удаление подзадачи"""
    subtask = get_object_or_404(Subtask, id=subtask_id, task__user=request.user)
    task_id = subtask.task.id
    
    if request.method == 'POST':
        subtask.delete()
        messages.success(request, 'Этап удален')
        return redirect('subtask_list', task_id=task_id)
    
    return render(request, 'tasks/subtask_confirm_delete.html', {'subtask': subtask})


@login_required
def subtask_bulk_create(request, task_id):
    """Массовое создание подзадач"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        form = SubtaskBulkCreateForm(request.POST)
        if form.is_valid():
            stages = form.cleaned_data['stages_data']
            created = 0
            errors = []
            
            for stage_data in stages:
                try:
                    performers = []
                    if stage_data.get('performers'):
                        for name in stage_data['performers'].split(','):
                            parts = name.strip().split()
                            if len(parts) >= 2:
                                employee = Employee.objects.filter(
                                    last_name__icontains=parts[0],
                                    first_name__icontains=parts[1]
                                ).first()
                                if employee:
                                    performers.append(employee)
                    
                    subtask = Subtask.objects.create(
                        task=task,
                        stage_number=stage_data['stage_number'],
                        title=stage_data['title'],
                        description=stage_data.get('description', '')
                    )
                    
                    if performers:
                        subtask.performers.set(performers)
                        if len(performers) == 1:
                            subtask.responsible = performers[0]
                            subtask.save()
                    
                    created += 1
                    
                except Exception as e:
                    errors.append(f"Ошибка при создании этапа {stage_data.get('stage_number')}: {str(e)}")
            
            if created > 0:
                messages.success(request, f'Создано {created} этапов')
            if errors:
                messages.warning(request, '\n'.join(errors))
            
            return redirect('subtask_list', task_id=task.id)
    else:
        form = SubtaskBulkCreateForm()
    
    return render(request, 'tasks/subtask_bulk_create.html', {
        'form': form,
        'task': task
    })


@login_required
def subtask_update_status(request, subtask_id):
    """Быстрое обновление статуса подзадачи"""
    if request.method == 'POST':
        subtask = get_object_or_404(Subtask, id=subtask_id, task__user=request.user)
        new_status = request.POST.get('status')
        
        if new_status in dict(Subtask.STATUS_CHOICES):
            subtask.status = new_status
            
            if new_status == 'in_progress' and not subtask.actual_start:
                subtask.actual_start = timezone.now()
            elif new_status == 'completed' and not subtask.actual_end:
                subtask.actual_end = timezone.now()
            
            subtask.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'status': subtask.status,
                    'status_display': subtask.get_status_display()
                })
        
        return redirect('subtask_list', task_id=subtask.task.id)
    return JsonResponse({'success': False, 'error': 'Invalid request'})
@login_required
def task_detail(request, task_id):
    """Детальная информация о задаче"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    # Отладка в консоль
    print(f"=== Отладка task_detail ===")
    print(f"Задача ID: {task.id}")
    print(f"Количество подзадач: {task.subtasks.count()}")
    print(f"Подзадачи: {[s.title for s in task.subtasks.all()]}")
    
    return render(request, 'tasks/task_detail.html', {'task': task})

from .utils.docx_importer import ResearchDocxImporter
from .forms import ResearchImportForm

@login_required
def import_research_from_docx(request):
    """Импорт НИР из DOCX файла"""
    if request.method == 'POST':
        form = ResearchImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Сохраняем загруженный файл
                docx_file = request.FILES['docx_file']
                file_path = f'/tmp/{docx_file.name}'
                
                with open(file_path, 'wb+') as destination:
                    for chunk in docx_file.chunks():
                        destination.write(chunk)
                
                # Импортируем
                importer = ResearchDocxImporter(file_path)
                
                # Получаем выбранных исполнителей по умолчанию
                default_performers = form.cleaned_data['default_performers']
                
                task = importer.import_research(default_performers)
                
                messages.success(request, f'Успешно импортирована НИР: {task.title}')
                return redirect('research_task_detail', task_id=task.id)
                
            except Exception as e:
                messages.error(request, f'Ошибка при импорте: {str(e)}')
    else:
        form = ResearchImportForm()
    
    return render(request, 'tasks/import_research.html', {'form': form})
# ============= УПРАВЛЕНИЕ НИР (НАУЧНО-ИССЛЕДОВАТЕЛЬСКИМИ РАБОТАМИ) =============

@login_required
def research_task_detail(request, task_id):
    """Детальная информация о НИР"""
    research_task = get_object_or_404(ResearchTask, id=task_id)
    
    # Получаем все этапы с подэтапами и продукцией
    stages = research_task.stages.all().prefetch_related('substages__products')
    
    # Статистика
    total_stages = stages.count()
    total_substages = sum(stage.substages.count() for stage in stages)
    total_products = sum(
        sum(substage.products.count() for substage in stage.substages.all()) 
        for stage in stages
    )
    
    # Прогресс выполнения
    completed_products = 0
    for stage in stages:
        for substage in stage.substages.all():
            completed_products += substage.products.filter(status='completed').count()
    
    progress = int((completed_products / total_products) * 100) if total_products > 0 else 0
    
    context = {
        'research_task': research_task,
        'stages': stages,
        'total_stages': total_stages,
        'total_substages': total_substages,
        'total_products': total_products,
        'completed_products': completed_products,
        'progress': progress,
    }
    return render(request, 'tasks/research_task_detail.html', context)


@login_required
def research_stage_detail(request, stage_id):
    """Детальная информация об этапе НИР"""
    stage = get_object_or_404(ResearchStage, id=stage_id)
    substages = stage.substages.all().prefetch_related('products')
    
    context = {
        'stage': stage,
        'substages': substages,
    }
    return render(request, 'tasks/research_stage_detail.html', context)


@login_required
def research_substage_detail(request, substage_id):
    """Детальная информация о подэтапе НИР"""
    substage = get_object_or_404(ResearchSubstage, id=substage_id)
    products = substage.products.all()
    
    # Доступные исполнители для назначения
    employees = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
    
    context = {
        'substage': substage,
        'products': products,
        'employees': employees,
    }
    return render(request, 'tasks/research_substage_detail.html', context)


@login_required
def research_product_detail(request, product_id):
    """Детальная информация о продукции"""
    product = get_object_or_404(ResearchProduct, id=product_id)
    
    context = {
        'product': product,
    }
    return render(request, 'tasks/research_product_detail.html', context)


@login_required
def assign_research_performers(request, item_type, item_id):
    """Назначение исполнителей для элементов НИР"""
    model_map = {
        'stage': ResearchStage,
        'substage': ResearchSubstage,
        'product': ResearchProduct,
    }
    
    if item_type not in model_map:
        return HttpResponseNotFound("Неверный тип элемента")
    
    item = get_object_or_404(model_map[item_type], id=item_id)
    
    if request.method == 'POST':
        performer_ids = request.POST.getlist('performers')
        responsible_id = request.POST.get('responsible')
        
        # Назначаем исполнителей
        if performer_ids:
            item.performers.set(performer_ids)
        
        # Назначаем ответственного
        if responsible_id:
            item.responsible_id = responsible_id
            item.save()
        
        messages.success(request, 'Исполнители успешно назначены')
        
        # Перенаправляем в зависимости от типа
        if item_type == 'stage':
            return redirect('research_stage_detail', stage_id=item.id)
        elif item_type == 'substage':
            return redirect('research_substage_detail', substage_id=item.id)
        else:
            return redirect('research_product_detail', product_id=item.id)
    
    # GET запрос - показываем форму назначения
    employees = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
    current_performers = item.performers.values_list('id', flat=True)
    
    context = {
        'item': item,
        'item_type': item_type,
        'employees': employees,
        'current_performers': list(current_performers),
        'current_responsible': item.responsible_id if item.responsible else None,
    }
    return render(request, 'tasks/assign_research_performers.html', context)


@login_required
def update_product_status(request, product_id):
    """Обновление статуса продукции"""
    if request.method == 'POST':
        product = get_object_or_404(ResearchProduct, id=product_id)
        new_status = request.POST.get('status')
        
        if new_status in dict(ResearchProduct.STATUS_CHOICES):
            product.status = new_status
            product.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'status': product.status,
                    'status_display': product.get_status_display()
                })
        
        return redirect('research_substage_detail', substage_id=product.substage.id)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def research_task_list(request):
    """Список всех НИР"""
    research_tasks = ResearchTask.objects.all().order_by('-created_date')
    
    context = {
        'research_tasks': research_tasks,
    }
    return render(request, 'tasks/research_task_list.html', context)


@login_required
def research_task_create(request):
    """Создание новой НИР вручную"""
    if request.method == 'POST':
        form = ResearchTaskForm(request.POST)
        if form.is_valid():
            research_task = form.save()
            messages.success(request, f'НИР "{research_task.title}" успешно создана')
            return redirect('research_task_detail', task_id=research_task.id)
    else:
        form = ResearchTaskForm()
    
    return render(request, 'tasks/research_task_form.html', {'form': form, 'title': 'Создание НИР'})


@login_required
def research_task_edit(request, task_id):
    """Редактирование НИР"""
    research_task = get_object_or_404(ResearchTask, id=task_id)
    
    if request.method == 'POST':
        form = ResearchTaskForm(request.POST, instance=research_task)
        if form.is_valid():
            form.save()
            messages.success(request, 'НИР успешно обновлена')
            return redirect('research_task_detail', task_id=research_task.id)
    else:
        form = ResearchTaskForm(instance=research_task)
    
    return render(request, 'tasks/research_task_form.html', {
        'form': form, 
        'title': f'Редактирование: {research_task.title}',
        'research_task': research_task
    })

@login_required
def preview_import(request):
    """Предпросмотр данных из ТЗ перед импортом"""
    if request.method == 'POST' and request.FILES.get('tz_file'):
        tz_file = request.FILES['tz_file']
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                for chunk in tz_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            importer = ResearchDocxImporter(tmp_path)
            tz_data = importer.parse_research_task()
            
            os.unlink(tmp_path)
            
            return JsonResponse({
                'success': True,
                'title': tz_data.get('title'),
                'stages_count': len(tz_data.get('stages', [])),
                'stages': tz_data.get('stages', [])
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def import_staff_from_excel(request):
    """Импорт штатного расписания из Excel"""
    if request.method == 'POST':
        form = StaffImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                excel_file = request.FILES['excel_file']
                
                # Сохраняем файл временно
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    for chunk in excel_file.chunks():
                        tmp_file.write(chunk)
                    tmp_path = tmp_file.name
                
                # Импортируем
                importer = StaffImporter(tmp_path)
                imported_count = importer.import_staff()
                
                # Удаляем временный файл
                import os
                os.unlink(tmp_path)
                
                # Очищаем кэш оргструктуры после импорта
                cache.delete('org_chart_data_v3')
                print(f"🗑️ Кэш оргструктуры очищен после импорта штатного расписания")
                
                messages.success(request, f'Успешно импортировано {imported_count} штатных единиц')
                return redirect('employee_list')
                
            except Exception as e:
                messages.error(request, f'Ошибка при импорте: {str(e)}')
    else:
        form = StaffImportForm()
    
    return render(request, 'tasks/import_staff.html', {'form': form})

@login_required
def organization_chart(request):
    # Пытаемся получить данные из кэша
    cache_key = 'org_chart_data_v3'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        print("📦 Данные загружены из кэша")
        return render(request, 'tasks/organization_chart.html', cached_data)
    
    print("🔄 Загружаем данные из базы...")
    
    # 1. Загружаем все подразделения с аннотированным количеством сотрудников
    #    и предварительной загрузкой сотрудников на всех уровнях
    departments = Department.objects.annotate(
        staff_count=Count('staff_positions', filter=Q(staff_positions__is_active=True))
    ).prefetch_related(
        # Загружаем сотрудников для всех отделов
        Prefetch('staff_positions', 
                queryset=StaffPosition.objects.filter(is_active=True).select_related('employee', 'position')),
        # Загружаем дочерние подразделения с их сотрудниками
        Prefetch('children', 
                queryset=Department.objects.annotate(
                    child_staff_count=Count('staff_positions', filter=Q(staff_positions__is_active=True))
                ).prefetch_related(
                    Prefetch('staff_positions', 
                            queryset=StaffPosition.objects.filter(is_active=True).select_related('employee', 'position')),
                    Prefetch('children',
                            queryset=Department.objects.annotate(
                                grandchild_staff_count=Count('staff_positions', filter=Q(staff_positions__is_active=True))
                            ).prefetch_related(
                                Prefetch('staff_positions', 
                                        queryset=StaffPosition.objects.filter(is_active=True).select_related('employee', 'position'))
                            ))
                ))
    ).order_by('name')
    
    # Преобразуем в список
    dept_list = list(departments)
    
    # 2. Создаём словарь для быстрого доступа по ID
    dept_dict = {d.id: d for d in dept_list}
    
    # 3. Инициализируем children_list для всех подразделений
    for dept in dept_list:
        dept.children_list = []
    
    # 4. Строим дерево
    root_departments = []
    for dept in dept_list:
        if dept.parent_id:
            parent = dept_dict.get(dept.parent_id)
            if parent:
                parent.children_list.append(dept)
        else:
            root_departments.append(dept)
    
    # 5. Группируем по типам
    departments_by_type = {
        'institute': [],
        'department': [],
        'laboratory': [],
        'group': [],
        'service': [],
    }
    for dept in dept_list:
        dept_type = dept.type
        if dept_type in ['institute', 'directorate']:
            departments_by_type['institute'].append(dept)
        elif dept_type in departments_by_type:
            departments_by_type[dept_type].append(dept)
    
    # 6. Ищем НИИ радиационной биологии
    radiobiology_institute = None
    for dept in dept_list:
        if 'радиационной биологии' in dept.name.lower():
            radiobiology_institute = dept
            break
    
    # 7. Статистика
    total_departments = len(dept_list)
    total_staff_positions = StaffPosition.objects.filter(is_active=True).count()
    total_employees = StaffPosition.objects.filter(is_active=True).values('employee').distinct().count()
    
    context = {
        'root_departments': root_departments,
        'departments_by_type': departments_by_type,
        'radiobiology_institute': radiobiology_institute,
        'total_departments': total_departments,
        'total_employees': total_employees,
        'total_staff_positions': total_staff_positions,
    }
    
    # Сохраняем в кэш на 10 минут
    cache.set(cache_key, context, 60 * 10)
    
    return render(request, 'tasks/organization_chart.html', context)

@login_required
def department_detail_ajax(request, dept_id):
    """Оптимизированный AJAX запрос - 2 запроса вместо N"""
    
    # 1. Загружаем отдел с его сотрудниками и детьми
    department = Department.objects.prefetch_related(
        Prefetch('staff_positions', 
                queryset=StaffPosition.objects.filter(is_active=True).select_related('employee', 'position')),
        Prefetch('children',
                queryset=Department.objects.all().prefetch_related(
                    Prefetch('staff_positions',
                            queryset=StaffPosition.objects.filter(is_active=True).select_related('employee', 'position'))
                ))
    ).get(id=dept_id)
    
    # 2. Дети уже загружены, просто считаем сотрудников
    children = list(department.children.all())
    for child in children:
        child.staff_count = len(list(child.staff_positions.all()))
    
    # 3. Сотрудники уже загружены
    staff_positions = list(department.staff_positions.all())
    
    html = render_to_string('tasks/partials/department_children.html', {
        'department': department,
        'children': children,
        'staff_positions': staff_positions,
    })
    
    return JsonResponse({
        'success': True,
        'html': html,
        'children_count': len(children),
        'staff_count': len(staff_positions),
    })

@login_required
def product_assign_performers(request, product_id):
    """Назначение исполнителей на продукцию с фильтрацией"""
    from .models import ResearchProduct, Employee, ProductPerformer, Department, StaffPosition
    from django.db.models import Q
    
    product = get_object_or_404(ResearchProduct, id=product_id)
    
    if request.method == 'POST':
        performer_ids = request.POST.getlist('performers')
        responsible_id = request.POST.get('responsible')
        
        # Очищаем существующих исполнителей
        product.product_performers.all().delete()
        
        # Создаем новых исполнителей
        for performer_id in performer_ids:
            ProductPerformer.objects.create(
                product=product,
                employee_id=performer_id,
                role='executor'
            )
        
        # Обновляем ответственного
        if responsible_id:
            product.responsible_id = responsible_id
        else:
            product.responsible = None
        product.save()
        
        messages.success(request, 'Исполнители назначены')
        
        if product.substage and product.substage.task:
            return redirect('subtask_list', task_id=product.substage.task.id)
        return redirect('task_list')
    
    # Получаем параметры фильтрации
    department_id = request.GET.get('department')
    search_query = request.GET.get('search', '').strip()
    
    # Базовый queryset
    employees = Employee.objects.filter(is_active=True)
    
    # Фильтр по подразделению (через штатные позиции)
    if department_id:
        employees = employees.filter(
            staff_positions__department_id=department_id,
            staff_positions__is_active=True
        ).distinct()
    
    # Поиск по ФИО и должности - расширенный поиск
    if search_query:
        # Разбиваем поисковый запрос на слова
        search_parts = search_query.split()
        
        # Создаем Q объекты для каждого слова
        q_objects = Q()
        for part in search_parts:
            q_objects |= Q(last_name__icontains=part)
            q_objects |= Q(first_name__icontains=part)
            q_objects |= Q(patronymic__icontains=part)
            q_objects |= Q(position__icontains=part)
            # Поиск по полному имени (Фамилия Имя Отчество)
            q_objects |= Q(last_name__icontains=part) & Q(first_name__icontains=part)
        
        employees = employees.filter(q_objects).distinct()
    
    # Сортируем результат
    employees = employees.order_by('last_name', 'first_name')
    
    # Получаем все подразделения для фильтра (только те, где есть сотрудники)
    departments = Department.objects.filter(
        staff_positions__is_active=True,
        staff_positions__employee__is_active=True
    ).distinct().order_by('level', 'full_path')
    
    # Добавляем количество сотрудников для каждого подразделения
    for dept in departments:
        dept.staff_count = StaffPosition.objects.filter(
            department=dept,
            is_active=True,
            employee__is_active=True
        ).count()
    
    # Получаем название выбранного подразделения для отображения
    selected_department_name = None
    if department_id:
        selected_dept = Department.objects.filter(id=department_id).first()
        if selected_dept:
            selected_department_name = selected_dept.full_path
    
    # Добавляем информацию о подразделении к каждому сотруднику
    for emp in employees:
        staff_pos = emp.staff_positions.filter(is_active=True).first()
        if staff_pos:
            emp.dept_full_path = staff_pos.department.full_path
            emp.dept_id = staff_pos.department.id
            emp.position_name = staff_pos.position.name
        else:
            emp.dept_full_path = None
            emp.dept_id = None
            emp.position_name = None
    
    current_performers = product.product_performers.values_list('employee_id', flat=True)
    
    context = {
        'product': product,
        'employees': employees,
        'departments': departments,
        'current_performers': list(current_performers),
        'current_responsible': product.responsible_id,
        'selected_department': department_id,
        'selected_department_name': selected_department_name,
        'search_query': search_query,
    }
    return render(request, 'tasks/product_assign_performers.html', context)

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

# @login_required
# def update_product_status(request, product_id):
#     """Обновление статуса продукции"""
#     if request.method == 'POST':
#         product = get_object_or_404(ResearchProduct, id=product_id)
#         new_status = request.POST.get('status')
        
#         if new_status in dict(ResearchProduct.STATUS_CHOICES):
#             product.status = new_status
#             product.save()
#             messages.success(request, f'Статус продукции обновлён на "{product.get_status_display()}"')
        
#         return redirect('subtask_list', task_id=product.subtask.task.id)
    
#     return redirect('subtask_list', task_id=product.subtask.task.id)