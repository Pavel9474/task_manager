from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from ..models import Employee, Department, StaffPosition, ResearchProduct, ProductPerformer
from django.db.models import Q
from django.utils import timezone

@login_required
def research_product_detail(request, product_id):
    """Детальная информация о продукции"""
    product = get_object_or_404(ResearchProduct, id=product_id)
    
    # Get performers with their details
    performers = product.product_performers.select_related('employee').all()
    
    # Create a simple form for adding performers
    from ..forms_product import ProductPerformerForm
    performer_form = ProductPerformerForm()
    
    context = {
        'product': product,
        'performers': performers,
        'performer_form': performer_form,
    }
    return render(request, 'tasks/research_product_detail.html', context)

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
def product_assign_performers(request, product_id):
    """Назначение исполнителей на продукцию с фильтрацией"""
  
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
        
        # Исправленная часть - убираем обращение к subtask
        # Перенаправляем на страницу подэтапа или НИР
        if product.research_substage:
            return redirect('research_substage_detail', substage_id=product.research_substage.id)
        elif product.research_stage:
            return redirect('research_stage_detail', stage_id=product.research_stage.id)
        elif product.research_task:
            return redirect('research_task_detail', task_id=product.research_task.id)
        else:
            return redirect('research_task_list')
    
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
def assign_product_performer(request, product_id):
    """Назначение исполнителя на продукцию"""
    product = get_object_or_404(ResearchProduct, id=product_id)
    
    if request.method == 'POST':
        from ..forms_product import ProductPerformerForm
        form = ProductPerformerForm(request.POST)
        if form.is_valid():
            performer = form.save(commit=False)
            performer.product = product
            performer.save()
            messages.success(request, f'Исполнитель {performer.employee.full_name} назначен')
        else:
            messages.error(request, 'Ошибка при назначении исполнителя')
    
    return redirect('research_product_detail', product_id=product.id)


@login_required
def remove_product_performer(request, product_id, performer_id):
    """Удаление исполнителя с продукции"""
    product = get_object_or_404(ResearchProduct, id=product_id)
    performer = get_object_or_404(ProductPerformer, id=performer_id, product=product)
    
    if request.method == 'POST':
        employee_name = performer.employee.full_name
        performer.delete()
        messages.success(request, f'Исполнитель {employee_name} удален')
    
    return redirect('research_product_detail', product_id=product.id)


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
            Q(name__icontains=search) |
            Q(description__icontains=search)
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
