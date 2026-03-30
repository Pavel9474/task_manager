from django.db.models import Prefetch, Count, Q
from ..models import Department, StaffPosition

class OrganizationService:
    """Сервис для работы с организационной структурой"""
    
    @staticmethod
    def get_full_structure():
        """Получить полную структуру организации с оптимизацией"""
        return Department.objects.all().prefetch_related(
            Prefetch('children', queryset=Department.objects.all().order_by('name')),
            Prefetch('staff_positions', 
                    queryset=StaffPosition.objects.filter(is_active=True).select_related('employee', 'position')),
        ).order_by('name')
    
    @staticmethod
    def get_statistics():
        """Получить статистику по организации"""
        return Department.objects.aggregate(
            total_departments=Count('id'),
            total_employees=Count('staff_positions__employee', distinct=True),
            total_staff_positions=Count('staff_positions', filter=Q(staff_positions__is_active=True))
        )
    
    @staticmethod
    def get_department_with_relations(dept_id):
        """Получить подразделение со всеми связями"""
        return Department.objects.prefetch_related(
            'children',
            Prefetch('staff_positions', 
                    queryset=StaffPosition.objects.filter(is_active=True).select_related('employee', 'position'))
        ).get(id=dept_id)
    
    @staticmethod
    def get_root_departments(departments=None):
        """Получить корневые подразделения"""
        if departments is None:
            departments = OrganizationService.get_full_structure()
        return [d for d in departments if d.parent is None]
    
    @staticmethod
    def group_by_type(departments=None):
        """Сгруппировать подразделения по типу"""
        if departments is None:
            departments = OrganizationService.get_full_structure()
        
        return {
            'institute': [d for d in departments if d.type in ['institute', 'directorate']],
            'department': [d for d in departments if d.type == 'department'],
            'laboratory': [d for d in departments if d.type == 'laboratory'],
            'group': [d for d in departments if d.type == 'group'],
            'service': [d for d in departments if d.type == 'service'],
        }