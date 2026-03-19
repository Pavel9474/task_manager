import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')
django.setup()

from tasks.models import Department, StaffPosition
from django.db import transaction

def create_institute_structure():
    """Создание правильной иерархии НИИ радиационной биологии"""
    
    print("=" * 60)
    print("🏗️  СОЗДАНИЕ СТРУКТУРЫ НИИ РАДИАЦИОННОЙ БИОЛОГИИ")
    print("=" * 60)
    
    with transaction.atomic():
        # 1. Создаем НИИ радиационной биологии (если его нет)
        institute, created = Department.objects.get_or_create(
            name="Научно-исследовательский институт радиационной биологии и радиационной медицины",
            defaults={
                'type': 'institute',
                'parent': None
            }
        )
        
        if created:
            print(f"✅ Создан институт: {institute.name}")
        else:
            print(f"🔄 Институт уже существует: {institute.name}")
        
        # 2. Создаем отделы института
        departments_data = [
            {"name": "Научно-исследовательский отдел молекулярной радиобиологии", "code": "9.1"},
            {"name": "Научно-исследовательский отдел радиационной цитогенетики", "code": "9.2"},
            {"name": "Научно-исследовательский отдел клеточных технологий", "code": "9.3"},
            {"name": "Научно-исследовательский экспериментальный отдел", "code": "9.4"},
            {"name": "Научно-исследовательский отдел обработки и анализа больших данных", "code": "9.5"},
            {"name": "Уральский радиобиологический биобанк", "code": "9.6"},
            {"name": "Научно-исследовательский центр коллективного пользования", "code": "9.7"},
            {"name": "Научно-исследовательская лаборатория экологической патопсихологии", "code": "9.8"},
            {"name": "Отдел платных услуг", "code": "9.9"},
            {"name": "Челябинский региональный межведомственный экспертный совет", "code": "9.10"},
            {"name": "Клиническое отделение", "code": "9.11"},
        ]
        
        created_departments = []
        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                name=dept_data["name"],
                defaults={
                    'type': 'department',
                    'parent': institute,
                    'code': dept_data["code"]
                }
            )
            if created:
                print(f"  ✅ Создан отдел: {dept.name}")
            else:
                print(f"  🔄 Отдел уже существует: {dept.name}")
            created_departments.append(dept)
        
        # 3. Переносим существующие лаборатории в соответствующие отделы
        # Получаем все лаборатории, которые сейчас висят напрямую
        laboratories = Department.objects.filter(
            type='laboratory',
            parent__isnull=True
        ).exclude(name__in=[d.name for d in created_departments])
        
        for lab in laboratories:
            # Пытаемся найти подходящий отдел по названию
            moved = False
            for dept in created_departments:
                if any(word in lab.name.lower() for word in ['молекулярн', 'генетик', 'постгеномн']):
                    if 'молекулярн' in dept.name.lower():
                        lab.parent = dept
                        lab.save()
                        print(f"  🔄 Лаборатория {lab.name} перемещена в отдел {dept.name}")
                        moved = True
                        break
                elif any(word in lab.name.lower() for word in ['цитогенетик', 'биодозиметр']):
                    if 'цитогенетик' in dept.name.lower():
                        lab.parent = dept
                        lab.save()
                        print(f"  🔄 Лаборатория {lab.name} перемещена в отдел {dept.name}")
                        moved = True
                        break
                elif any(word in lab.name.lower() for word in ['клеточн', 'иммунологи']):
                    if 'клеточн' in dept.name.lower():
                        lab.parent = dept
                        lab.save()
                        print(f"  🔄 Лаборатория {lab.name} перемещена в отдел {dept.name}")
                        moved = True
                        break
                elif 'экспериментальн' in lab.name.lower():
                    if 'экспериментальн' in dept.name.lower():
                        lab.parent = dept
                        lab.save()
                        print(f"  🔄 Лаборатория {lab.name} перемещена в отдел {dept.name}")
                        moved = True
                        break
            
            if not moved:
                print(f"  ⚠️ Лаборатория {lab.name} не привязана к отделу")
        
        print("\n" + "=" * 60)
        print("📊 ИТОГ")
        print("=" * 60)
        print(f"Институт: {institute.name}")
        print(f"Отделов: {institute.children.count()}")
        print(f"Всего лабораторий: {Department.objects.filter(type='laboratory').count()}")
        
        # Выводим структуру
        print("\n📋 ТЕКУЩАЯ СТРУКТУРА:")
        print(f"🏢 {institute.name}")
        for dept in institute.children.all().order_by('code'):
            print(f"  📁 {dept.name}")
            for lab in dept.children.all():
                print(f"    🔬 {lab.name}")

if __name__ == '__main__':
    create_institute_structure()