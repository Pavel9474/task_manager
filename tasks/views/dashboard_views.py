
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Prefetch
from ..models import Task, Employee, Department, StaffPosition 
from django.db.models import Prefetch, Count
from django.db.models import Q
import logging
from django.shortcuts import render, get_object_or_404
from datetime import date
import json

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

@login_required
def department_stats(request, dept_id=None):
    """Статистика по подразделению"""
    
    # Дерево подразделений для навигации
    root_departments = Department.objects.filter(parent__isnull=True).order_by('name')
    
    # Текущее подразделение
    if dept_id:
        current_dept = get_object_or_404(Department, id=dept_id)
    else:
        current_dept = root_departments.first()
    
    # Параметры фильтрации
    include_children = request.GET.get('include_children', 'on') == 'on'
    research_task_id = request.GET.get('research_task')
    
    # Получаем данные
    employees = current_dept.get_employees(include_children)
    research_tasks = current_dept.get_research_tasks(include_children)
    products = current_dept.get_products(include_children, research_task_id)
    
    # Статистика
    stats = current_dept.get_stats(include_children)
    
    # Детальная информация по продукции (для таблицы)
    products_detail = []
    for product in products.select_related('research_task', 'research_substage', 'responsible'):
        # Находим ответственного из этого подразделения
        responsible_from_dept = product.responsible if product.responsible in employees else None
        
        products_detail.append({
            'id': product.id,
            'name': product.name,
            'research_task': product.research_task,
            'research_substage': product.research_substage,
            'planned_start': product.planned_start,
            'planned_end': product.planned_end,
            'status': product.status,
            'status_display': product.get_status_display(),
            'completion_percent': product.completion_percent,
            'responsible': responsible_from_dept,
            'is_overdue': product.is_overdue,
        })
    
    # Сортируем по дате окончания
    products_detail.sort(key=lambda x: x['planned_end'] if x['planned_end'] else date.max)
    
    # Данные для Ганта
    gantt_data = []
    for product in products_detail:
        if product['planned_start'] and product['planned_end']:
            gantt_data.append({
                'id': product['id'],
                'name': product['name'][:50],
                'start': product['planned_start'].isoformat(),
                'end': product['planned_end'].isoformat(),
                'research_task_title': product['research_task'].title if product['research_task'] else None,
                'status': product['status'],
                'is_overdue': product['is_overdue'],
            })
    
    # Список доступных НИР для фильтра
    research_tasks_list = []
    for rt in research_tasks:
        research_tasks_list.append({
            'id': rt.id,
            'title': rt.title,
            'tz_number': rt.tz_number,
            'products_count': products.filter(research_task=rt).count(),
        })
    
    context = {
        'current_dept': current_dept,
        'root_departments': root_departments,
        'employees': employees[:100],  # Ограничиваем для производительности
        'research_tasks': research_tasks,
        'products': products_detail,
        'stats': stats,
        'gantt_data': json.dumps(gantt_data),
        'include_children': include_children,
        'selected_research_task': int(research_task_id) if research_task_id else None,
        'research_tasks_list': research_tasks_list,
        'today': date.today().isoformat(),
    }
    
    return render(request, 'tasks/department_stats.html', context)