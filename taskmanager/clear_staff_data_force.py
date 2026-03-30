import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')
django.setup()

from tasks.models import Employee, Department, Position, StaffPosition

# Удаляем в правильном порядке (сначала зависимые, потом родительские)
StaffPosition.objects.all().delete()
Position.objects.all().delete()
Department.objects.all().delete()
Employee.objects.all().delete()

print("✅ Все данные по сотрудникам и структуре удалены!")