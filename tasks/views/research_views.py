from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Employee, ResearchTask, ResearchStage, ResearchSubstage, ResearchProduct
from ..forms import ResearchTaskForm
from django.core.cache import cache
from django.http import HttpResponseNotFound
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