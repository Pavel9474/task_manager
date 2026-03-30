import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')
django.setup()

from tasks.models import Department

def fix_parent_relations():
    """Исправление родительских связей между подразделениями"""
    
    print("=" * 60)
    print("🔧 ИСПРАВЛЕНИЕ РОДИТЕЛЬСКИХ СВЯЗЕЙ")
    print("=" * 60)
    
    # Получаем все подразделения
    departments = {d.name: d for d in Department.objects.all()}
    
    # Связи: дочернее -> родительское
    relations = [
        # Руководство и его дочерние
        ('Секретариат', 'Руководство'),
        
        # Информационно-аналитический отдел и его группы
        ('Группа международных отношений', 'Информационно-аналитический отдел'),
        
        # Отдел бухгалтерского учета и его группа
        ('Планово-экономическая группа', 'Отдел бухгалтерского учета и отчетности'),
        
        # Научно-исследовательский институт и его отделы (уже есть, но проверим)
        ('Клиническое отделение', 'Научно-исследовательский институт радиационной биологии и радиационной медицины'),
        ('Научно-исследовательская лаборатория экологической патопсихологии', 'Научно-исследовательский институт радиационной биологии и радиационной медицины'),
        ('Научно-исследовательский экспериментальный отдел', 'Научно-исследовательский институт радиационной биологии и радиационной медицины'),
        ('Научно-исследовательский отдел клеточных технологий', 'Научно-исследовательский институт радиационной биологии и радиационной медицины'),
        ('Научно-исследовательский отдел молекулярной радиобиологии', 'Научно-исследовательский институт радиационной биологии и радиационной медицины'),
    ]
    
    updated = 0
    for child_name, parent_name in relations:
        child = departments.get(child_name)
        parent = departments.get(parent_name)
        
        if child and parent:
            if child.parent != parent:
                child.parent = parent
                child.save()
                print(f"✅ {child_name} -> {parent_name}")
                updated += 1
            else:
                print(f"🔄 {child_name} уже привязан к {parent_name}")
        else:
            if not child:
                print(f"❌ Не найдено подразделение: {child_name}")
            if not parent:
                print(f"❌ Не найдено подразделение: {parent_name}")
    
    print(f"\n✅ Обновлено связей: {updated}")
    
    # Проверяем результат
    print("\n📊 Проверка структуры:")
    root = Department.objects.filter(name='Руководство').first()
    if root:
        print(f"\nРуководство (ID: {root.id}) - детей: {root.children.count()}")
        for child in root.children.all():
            print(f"  └─ {child.name}")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    fix_parent_relations()