
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Prefetch
from ..models import Task, Employee, Department, StaffPosition 
from django.db.models import Prefetch, Count
from django.db.models import Q
import logging

from django.core.cache import cache

logger = logging.getLogger('tasks')
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