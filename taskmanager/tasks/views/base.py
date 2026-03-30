def update_substage_performers(substage):
    """Обновляет исполнителей подэтапа на основе исполнителей всех продуктов"""
    from ..models import ProductPerformer, Employee
    
    # Получаем всех исполнителей из всех продуктов подэтапа
    all_performers = Employee.objects.filter(
        product_performers__product__subtask=substage
    ).distinct()
    
    # Обновляем исполнителей подэтапа
    substage.performers.set(all_performers)
    
    # Если есть ответственный в подэтапе, но его нет в исполнителях - добавляем
    if substage.responsible and substage.responsible not in all_performers:
        substage.performers.add(substage.responsible)
    
    # Логируем обновление
    print(f"Обновлены исполнители подэтапа {substage.id}: {[p.full_name for p in all_performers]}")

