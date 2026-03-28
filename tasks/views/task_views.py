from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.auth import login
from ..models import Task, Employee, ResearchProduct, ResearchTask
from ..forms import TaskForm, TaskWithImportForm
from ..utils.docx_importer import ResearchDocxImporter
import tempfile
from django.db.models import Count
from django.db.models import Q
import os

from django.core.cache import cache



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
                ResearchProduct.objects.filter(research_substage=subtask).delete()
                
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
def task_list(request):
    """Список задач пользователя"""
    
    # Получаем задачи пользователя
    tasks = Task.objects.filter(user=request.user)
    
    # Получаем все НИР (доступные всем)
    research_tasks = ResearchTask.objects.all().order_by('-created_date')
    
    # Фильтрация задач (оставляем как есть)
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        tasks = tasks.filter(status=status_filter)
    
    employee_filter = request.GET.get('employee', '')
    if employee_filter:
        tasks = tasks.filter(assigned_to__id=employee_filter)
    
    search_query = request.GET.get('search', '')
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    sort_by = request.GET.get('sort', '-created_date')
    tasks = tasks.order_by(sort_by)
    
    # Статистика
    todo_count = tasks.filter(status='todo').count()
    in_progress_count = tasks.filter(status='in_progress').count()
    done_count = tasks.filter(status='done').count()
    overdue_count = tasks.filter(status__in=['todo', 'in_progress'], due_date__lt=timezone.now()).count()
    
    # Список сотрудников для фильтра
    employees = Employee.objects.filter(is_active=True)
    
    context = {
        'tasks': tasks,
        'research_tasks': research_tasks,  # <-- ДОБАВЛЯЕМ НИР
        'status_filter': status_filter,
        'employee_filter': employee_filter,
        'search_query': search_query,
        'sort_by': sort_by,
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
    
    # Отладка в консоль
    print(f"=== Отладка task_detail ===")
    print(f"Задача ID: {task.id}")
    print(f"Количество подзадач: {task.subtasks.count()}")
    print(f"Подзадачи: {[s.title for s in task.subtasks.all()]}")
    
    return render(request, 'tasks/task_detail.html', {'task': task})
