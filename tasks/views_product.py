# tasks/views_product.py (новый файл или добавить в существующий views.py)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from .models import ResearchProduct, ProductPerformer, Employee
from .forms_product import ResearchProductForm, ProductPerformerForm, BulkAssignPerformersForm
import logging

logger = logging.getLogger('tasks')


@login_required
def research_product_list(request):
    """Список научной продукции"""
    products = ResearchProduct.objects.select_related(
        'research_task', 'research_stage', 'research_substage'
    ).prefetch_related('performers', 'product_performers')
    
    # Фильтрация
    product_type = request.GET.get('type')
    if product_type:
        products = products.filter(product_type=product_type)
    
    status = request.GET.get('status')
    if status:
        products = products.filter(status=status)
    
    research_task = request.GET.get('task')
    if research_task:
        products = products.filter(research_task_id=research_task)
    
    # Поиск
    search = request.GET.get('search')
    if search:
        products = products.filter(
            models.Q(name__icontains=search) |
            models.Q(description__icontains=search)
        )
    
    # Статистика
    from django.db.models import Count, Q
    stats = {
        'total': products.count(),
        'in_progress': products.filter(status='in_progress').count(),
        'completed': products.filter(status='completed').count(),
        'overdue': products.filter(
            status__in=['pending', 'in_progress'],
            planned_end__lt=timezone.now().date()
        ).count(),
    }
    
    context = {
        'products': products,
        'product_types': ResearchProduct.ProductType.choices,
        'statuses': ResearchProduct.STATUS_CHOICES,
        'stats': stats,
    }
    return render(request, 'tasks/research_product_list.html', context)


@login_required
def research_product_detail(request, pk):
    """Детальная страница научной продукции"""
    product = get_object_or_404(
        ResearchProduct.objects.select_related(
            'research_task', 'research_stage', 'research_substage', 'subtask'
        ),
        pk=pk
    )
    
    # Получаем исполнителей с ролями
    performers = product.product_performers.select_related('employee').all()
    
    # Форма для добавления исполнителя
    performer_form = ProductPerformerForm(product=product)
    
    context = {
        'product': product,
        'performers': performers,
        'performer_form': performer_form,
    }
    return render(request, 'tasks/research_product_detail.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def research_product_create(request):
    """Создание научной продукции"""
    if request.method == 'POST':
        form = ResearchProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()
            form.save_m2m()  # Сохраняем ManyToMany связи
            
            messages.success(request, f'Продукция "{product.name}" успешно создана')
            logger.info(f'User {request.user} created product {product.id}')
            return redirect('research_product_detail', pk=product.id)
    else:
        form = ResearchProductForm()
    
    return render(request, 'tasks/research_product_form.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def research_product_edit(request, pk):
    """Редактирование научной продукции"""
    product = get_object_or_404(ResearchProduct, pk=pk)
    
    if request.method == 'POST':
        form = ResearchProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Продукция "{product.name}" успешно обновлена')
            return redirect('research_product_detail', pk=product.id)
    else:
        form = ResearchProductForm(instance=product)
    
    return render(request, 'tasks/research_product_form.html', {'form': form, 'product': product})


@login_required
@require_POST
@transaction.atomic
def assign_product_performer(request, product_pk):
    """Назначение исполнителя на продукцию"""
    product = get_object_or_404(ResearchProduct, pk=product_pk)
    form = ProductPerformerForm(request.POST, product=product)
    
    if form.is_valid():
        performer = form.save(commit=False)
        performer.product = product
        performer.assigned_by = request.user
        performer.save()
        
        # Если это ответственный исполнитель, обновляем поле responsible в продукции
        if performer.role == 'responsible':
            product.responsible = performer.employee
            product.save(update_fields=['responsible'])
        
        messages.success(
            request,
            f'Сотрудник {performer.employee.full_name} назначен как {performer.get_role_display()}'
        )
        logger.info(f'User {request.user} assigned {performer.employee} to product {product.id}')
    else:
        messages.error(request, 'Ошибка при назначении исполнителя')
    
    return redirect('research_product_detail', pk=product_pk)


@login_required
@require_POST
def remove_product_performer(request, product_pk, performer_pk):
    """Удаление исполнителя с продукции"""
    product = get_object_or_404(ResearchProduct, pk=product_pk)
    performer = get_object_or_404(ProductPerformer, pk=performer_pk, product=product)
    
    employee_name = performer.employee.full_name
    performer.delete()
    
    # Если удалили ответственного, снимаем отметку
    if performer.role == 'responsible' and product.responsible == performer.employee:
        product.responsible = None
        product.save(update_fields=['responsible'])
    
    messages.success(request, f'Сотрудник {employee_name} удален из исполнителей')
    return redirect('research_product_detail', pk=product_pk)


@login_required
@user_passes_test(lambda u: u.is_staff)
def bulk_assign_performers(request, product_pk):
    """Массовое назначение исполнителей"""
    product = get_object_or_404(ResearchProduct, pk=product_pk)
    
    if request.method == 'POST':
        form = BulkAssignPerformersForm(request.POST)
        if form.is_valid():
            employees = form.cleaned_data['employees']
            role = form.cleaned_data['role']
            contribution_percent = form.cleaned_data.get('contribution_percent')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            
            created_count = 0
            for employee in employees:
                # Проверяем, не назначен ли уже
                if not ProductPerformer.objects.filter(product=product, employee=employee).exists():
                    ProductPerformer.objects.create(
                        product=product,
                        employee=employee,
                        role=role,
                        contribution_percent=contribution_percent,
                        start_date=start_date,
                        end_date=end_date,
                        assigned_by=request.user
                    )
                    created_count += 1
            
            messages.success(
                request,
                f'Назначено {created_count} исполнителей на продукцию "{product.name}"'
            )
            return redirect('research_product_detail', pk=product_pk)
    else:
        form = BulkAssignPerformersForm()
    
    return render(request, 'tasks/bulk_assign_performers.html', {
        'form': form,
        'product': product
    })


@login_required
def my_research_products(request):
    """Мои научные продукции (где я исполнитель)"""
    products = ResearchProduct.objects.filter(
        models.Q(performers=request.user.employee) |
        models.Q(product_performers__employee=request.user.employee)
    ).distinct().select_related('research_task', 'research_stage')
    
    context = {
        'products': products,
        'is_my_products': True,
    }
    return render(request, 'tasks/research_product_list.html', context)


@login_required
def update_product_status(request, pk):
    """Обновление статуса продукции"""
    if request.method == 'POST':
        product = get_object_or_404(ResearchProduct, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in dict(ResearchProduct.STATUS_CHOICES):
            old_status = product.status
            product.status = new_status
            
            # Обновляем фактические даты
            if new_status == 'in_progress' and not product.actual_start:
                product.actual_start = timezone.now().date()
            elif new_status == 'completed':
                product.actual_end = timezone.now().date()
                product.completion_percent = 100
            
            product.save()
            
            messages.success(request, f'Статус продукции изменен на "{product.get_status_display()}"')
            logger.info(f'User {request.user} changed product {product.id} status from {old_status} to {new_status}')
    
    return redirect('research_product_detail', pk=pk)