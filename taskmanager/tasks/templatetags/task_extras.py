# tasks/templatetags/task_extras.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Получить элемент из словаря по ключу"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def get_status_color(status):
    """Возвращает цвет для статуса"""
    colors = {
        'pending': 'secondary',
        'in_progress': 'primary',
        'completed': 'success',
        'delayed': 'danger',
        'cancelled': 'dark',
        'todo': 'secondary',
        'done': 'success',
    }
    return colors.get(status, 'secondary')

@register.filter
def get_priority_color(priority):
    """Возвращает цвет для приоритета"""
    colors = {
        'low': 'success',
        'medium': 'info',
        'high': 'warning',
        'critical': 'danger',
    }
    return colors.get(priority, 'secondary')