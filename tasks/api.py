# tasks/api.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Task

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