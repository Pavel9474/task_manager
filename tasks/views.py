from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Task
from .forms import TaskForm

@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user)
    
    # Фильтрация по статусу
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        tasks = tasks.filter(status=status_filter)
    
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
    
    context = {
        'tasks': tasks,
        'status_filter': status_filter,
        'search_query': search_query,
        'sort_by': sort_by,
        'now': timezone.now(),
        'todo_count': todo_count,
        'in_progress_count': in_progress_count,
        'done_count': done_count,
        'overdue_count': overdue_count,
    }
    return render(request, 'tasks/task_list.html', context)

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    return render(request, 'tasks/task_detail.html', {'task': task})

@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, 'Задача успешно создана!')
            return redirect('task_list')
    else:
        form = TaskForm()
    
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Создать задачу'})

@login_required
def task_update(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Задача успешно обновлена!')
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Редактировать задачу'})

@login_required
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Задача удалена!')
        return redirect('task_list')
    
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})

@login_required
def task_complete(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.status = 'done'
    task.save()
    messages.success(request, f'Задача "{task.title}" отмечена как выполненная!')
    return redirect('task_list')

@login_required
def task_statistics(request):
    tasks = Task.objects.filter(user=request.user)
    now = timezone.now()
    
    # Задачи, выполняющиеся прямо сейчас
    active_tasks = tasks.filter(
        status='in_progress',
        start_time__isnull=False,
        end_time__isnull=True
    ).count()
    
    # Среднее время выполнения завершенных задач
    completed_tasks = tasks.filter(status='done', start_time__isnull=False, end_time__isnull=False)
    total_duration = 0
    for task in completed_tasks:
        if task.end_time and task.start_time:
            duration = (task.end_time - task.start_time).total_seconds() / 3600  # в часах
            total_duration += duration
    
    avg_duration = round(total_duration / completed_tasks.count(), 1) if completed_tasks.exists() else 0
    
    # Статистика по приоритетам
    priority_stats = tasks.values('priority').annotate(count=count('priority'))
    
    # Статистика по дням (задачи созданные за последние 7 дней)
    last_week = now - timezone.timedelta(days=7)
    daily_stats = tasks.filter(created_date__gte=last_week).extra({
        'day': "date(created_date)"
    }).values('day').annotate(count=count('id')).order_by('day')
    
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
        'daily_stats': daily_stats,
    }
    
    return render(request, 'tasks/statistics.html', {'stats': stats})

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages

def register(request):
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
@login_required
def task_start(request, task_id):
    """Начать выполнение задачи"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if task.can_start():
        task.start_time = timezone.now()
        task.status = 'in_progress'
        task.save()
        messages.success(request, f'Задача "{task.title}" начата в {task.start_time.strftime("%H:%M %d.%m.%Y")}')
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
            
            duration = task.duration()
            messages.success(request, f'Задача "{task.title}" выполнена! Время выполнения: {duration}')
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
        messages.success(request, f'Время задачи "{task.title}" сброшено')
        return redirect('task_detail', task_id=task.id)
    
    return render(request, 'tasks/task_reset_time.html', {'task': task})
@login_required
def task_statistics(request):
    tasks = Task.objects.filter(user=request.user)
    now = timezone.now()
    
    # Задачи, выполняющиеся прямо сейчас
    active_tasks = tasks.filter(
        status='in_progress',
        start_time__isnull=False,
        end_time__isnull=True
    ).count()
    
    # Среднее время выполнения завершенных задач
    completed_tasks = tasks.filter(status='done', start_time__isnull=False, end_time__isnull=False)
    total_duration = sum(
        (task.end_time - task.start_time).total_seconds() / 3600  # в часах
        for task in completed_tasks if task.end_time and task.start_time
    )
    avg_duration = round(total_duration / completed_tasks.count(), 1) if completed_tasks.exists() else 0
    
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
        'active_now': active_tasks,
        'avg_duration': avg_duration,
        'completed_count': completed_tasks.count(),
    }
    
    return render(request, 'tasks/statistics.html', {'stats': stats})