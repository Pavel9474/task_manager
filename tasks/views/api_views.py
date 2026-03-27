from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Prefetch
from ..models import Task, Employee, Department, StaffPosition
from django.template.loader import render_to_string

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
