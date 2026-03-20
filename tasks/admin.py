from django.contrib import admin
from django.core.cache import cache
from .models import Department, StaffPosition, Employee, Position

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'parent', 'level']
    list_filter = ['type']
    search_fields = ['name']
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache.delete('org_chart_data_v3')
        print(f"🗑️ Кэш оргструктуры очищен (админка: изменено подразделение)")
    
    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        cache.delete('org_chart_data_v3')
        print(f"🗑️ Кэш оргструктуры очищен (админка: удалено подразделение)")

# Аналогично для других моделей...