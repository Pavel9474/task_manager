from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from ..models import Task, Employee, Subtask, ResearchProduct, ProductPerformer
from ..forms_employee import EmployeeForm, EmployeeImportForm
import pandas as pd
from datetime import datetime
from django.db.models import Q
import json

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
def employee_toggle_active(request, employee_id):
    """Активация/деактивация сотрудника"""
    employee = get_object_or_404(Employee, id=employee_id)
    employee.is_active = not employee.is_active
    employee.save()
    
    status = "активирован" if employee.is_active else "деактивирован"
    messages.success(request, f'Сотрудник {employee.full_name} {status}')
    
    return redirect('employee_detail', employee_id=employee.id)

@login_required
def employee_delete(request, employee_id):
    """Удаление сотрудника"""
    employee = get_object_or_404(Employee, id=employee_id)
    
    # Проверяем, есть ли у сотрудника активные задачи
    active_tasks = Task.objects.filter(assigned_to=employee, status__in=['todo', 'in_progress'])
    active_subtasks = Subtask.objects.filter(
        performers=employee, 
        status__in=['pending', 'in_progress']
    )
    
    # Проверяем продукцию, где сотрудник является ответственным или исполнителем
    products_as_responsible = ResearchProduct.objects.filter(
        responsible=employee, 
        status__in=['pending', 'in_progress']
    )
    products_as_performer = ResearchProduct.objects.filter(
        product_performers__employee=employee,
        status__in=['pending', 'in_progress']
    ).distinct()
    
    # Если есть активные задания, показываем предупреждение
    if active_tasks.exists() or active_subtasks.exists() or products_as_responsible.exists() or products_as_performer.exists():
        messages.error(
            request, 
            f'Нельзя удалить сотрудника "{employee.full_name}". '
            f'У него есть активные задачи или продукция. '
            f'Сначала завершите или переназначьте задачи.'
        )
        return redirect('employee_detail', employee_id=employee.id)
    
    if request.method == 'POST':
        full_name = employee.full_name
        try:
            # Очищаем связи перед удалением
            # Удаляем из ManyToMany полей задач
            for task in Task.objects.filter(assigned_to=employee):
                task.assigned_to.remove(employee)
            
            # Удаляем из ManyToMany полей подзадач
            for subtask in Subtask.objects.filter(performers=employee):
                subtask.performers.remove(employee)
            
            # Обнуляем ответственных
            Subtask.objects.filter(responsible=employee).update(responsible=None)
            ResearchProduct.objects.filter(responsible=employee).update(responsible=None)
            
            # Удаляем связи ProductPerformer
            ProductPerformer.objects.filter(employee=employee).delete()
            
            # Удаляем штатные позиции
            employee.staff_positions.all().delete()
            
            # Удаляем сотрудника
            employee.delete()
            
            messages.success(request, f'Сотрудник {full_name} удален из системы')
            
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')
        
        return redirect('employee_list')
    
    # GET запрос - показываем страницу подтверждения
    return render(request, 'tasks/employee_confirm_delete.html', {'employee': employee})

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

