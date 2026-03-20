from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Department, StaffPosition, Employee, Position


@receiver([post_save, post_delete], sender=Department)
def clear_department_cache(sender, instance, **kwargs):
    """Очищаем кэш оргструктуры при изменении подразделений"""
    cache.delete('org_chart_data_v3')
    print(f"🗑️ Кэш оргструктуры очищен (изменено подразделение: {instance.name})")


@receiver([post_save, post_delete], sender=StaffPosition)
def clear_staff_cache(sender, instance, **kwargs):
    """Очищаем кэш оргструктуры при изменении штатных единиц"""
    cache.delete('org_chart_data_v3')
    print(f"🗑️ Кэш оргструктуры очищен (изменена штатная единица для: {instance.employee.full_name if instance.employee else 'вакансия'})")


@receiver([post_save, post_delete], sender=Employee)
def clear_employee_cache(sender, instance, **kwargs):
    """Очищаем кэш оргструктуры при изменении сотрудников"""
    cache.delete('org_chart_data_v3')
    print(f"🗑️ Кэш оргструктуры очищен (изменён сотрудник: {instance.full_name})")


@receiver([post_save, post_delete], sender=Position)
def clear_position_cache(sender, instance, **kwargs):
    """Очищаем кэш оргструктуры при изменении должностей"""
    cache.delete('org_chart_data_v3')
    print(f"🗑️ Кэш оргструктуры очищен (изменена должность: {instance.name})")