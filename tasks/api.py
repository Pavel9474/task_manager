# tasks/api.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Task
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Task, Employee

@login_required
@require_http_methods(["GET"])
def api_tasks(request):
    tasks = Task.objects.filter(user=request.user)
    data = [{
        'id': task.id,
        'title': task.title,
        'status': task.status,
        'priority': task.priority,
        'due_date': task.due_date.isoformat() if task.due_date else None,
    } for task in tasks]
    return JsonResponse(data, safe=False)


@api_view(['POST'])
def quick_assign(request):
    """Быстрое назначение исполнителя через API"""
    task_id = request.data.get('task_id')
    employee_id = request.data.get('employee_id')
    
    task = Task.objects.get(id=task_id, user=request.user)
    employee = Employee.objects.get(id=employee_id, is_active=True)
    
    task.assigned_to.add(employee)
    
    return Response({
        'success': True,
        'task': task.title,
        'employee': employee.short_name
    })