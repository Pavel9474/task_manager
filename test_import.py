import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')
django.setup()

from django.contrib.auth.models import User
from tasks.models import Task, Subtask

# Очищаем все
print("Очищаем базу...")
Subtask.objects.all().delete()
Task.objects.all().delete()

# Создаем пользователя
user = User.objects.first()
if not user:
    user = User.objects.create_user('test', 'test@test.com', 'test123')

# Создаем задачу
task = Task.objects.create(
    title="Тестовая задача",
    description="Для проверки",
    user=user
)
print(f"Создана задача ID: {task.id}")

# Создаем этап
stage = Subtask.objects.create(
    task=task,
    stage_number=1,
    title="Этап 1",
    status='pending'
)
print(f"Создан этап ID: {stage.id}")

# Создаем подэтап
try:
    substage = Subtask.objects.create(
        task=task,
        stage_number=1.1,
        title="Подэтап 1.1",
        status='pending'
    )
    print(f"Создан подэтап ID: {substage.id}")
    
    # Проверяем, что создалось
    count = Subtask.objects.filter(task=task).count()
    print(f"Всего подэтапов: {count}")
    
    for s in task.subtasks.all():
        print(f"  {s.stage_number}: {s.title}")
        
except Exception as e:
    print(f"ОШИБКА: {e}")