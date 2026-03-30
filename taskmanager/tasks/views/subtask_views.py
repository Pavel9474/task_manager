
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from ..models import Task, Employee, Subtask, ResearchProduct
from ..forms_subtask import SubtaskForm, SubtaskBulkCreateForm

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
