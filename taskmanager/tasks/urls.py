# tasks/urls.py
from django.urls import path
from .views import (
    # Задачи
    task_list, task_detail, task_create, task_update, task_delete,
    task_complete, task_start, task_finish, task_reset_time,
    task_statistics, task_assign_employees, task_update_status_ajax,
    
    # Сотрудники
    employee_list, employee_create, employee_detail, employee_update,
    employee_delete, employee_toggle_active, employee_import,
    employee_export, employee_export_template, employee_tasks,
    employee_search_api,
    
    # Подзадачи
    subtask_list, subtask_create, subtask_update, subtask_delete,
    subtask_bulk_create, subtask_update_status,
    
    # НИР
    research_task_list, research_task_create, research_task_detail,
    research_task_edit, research_stage_detail, research_substage_detail,
    assign_research_performers, research_product_detail,
    update_product_status,
    
    # Продукция
    product_assign_performers, create_external_employee,
    
    # Импорт
    import_research_from_docx, import_staff_from_excel, preview_import,
    
    # Другое
    organization_chart, team_dashboard, department_detail_ajax,
)

from .views import product_views as views_product

urlpatterns = [
    # Главная
    path('', task_list, name='task_list'),
    
    # Задачи
    path('task/<int:task_id>/', task_detail, name='task_detail'),
    path('task/create/', task_create, name='task_create'),
    path('task/<int:task_id>/update/', task_update, name='task_update'),
    path('task/<int:task_id>/delete/', task_delete, name='task_delete'),
    path('task/<int:task_id>/complete/', task_complete, name='task_complete'),
    path('task/<int:task_id>/start/', task_start, name='task_start'),
    path('task/<int:task_id>/finish/', task_finish, name='task_finish'),
    path('task/<int:task_id>/reset-time/', task_reset_time, name='task_reset_time'),
    path('statistics/', task_statistics, name='task_statistics'),
    path('task/<int:task_id>/assign/', task_assign_employees, name='task_assign_employees'),
    path('task/<int:task_id>/status/', task_update_status_ajax, name='task_update_status_ajax'),
    
    # Сотрудники
    path('employees/', employee_list, name='employee_list'),
    path('employee/create/', employee_create, name='employee_create'),
    path('employee/<int:employee_id>/', employee_detail, name='employee_detail'),
    path('employee/<int:employee_id>/update/', employee_update, name='employee_update'),
    path('employee/<int:employee_id>/delete/', employee_delete, name='employee_delete'),
    path('employee/<int:employee_id>/toggle-active/', employee_toggle_active, name='employee_toggle_active'),
    path('employee/<int:employee_id>/tasks/', employee_tasks, name='employee_tasks'),
    path('employees/import/', employee_import, name='employee_import'),
    path('employees/export/', employee_export, name='employee_export'),
    path('employees/export-template/', employee_export_template, name='employee_export_template'),
    path('api/employee-search/', employee_search_api, name='employee_search_api'),
    
    # Подзадачи
    path('task/<int:task_id>/subtasks/', subtask_list, name='subtask_list'),
    path('task/<int:task_id>/subtask/create/', subtask_create, name='subtask_create'),
    path('subtask/<int:subtask_id>/update/', subtask_update, name='subtask_update'),
    path('subtask/<int:subtask_id>/delete/', subtask_delete, name='subtask_delete'),
    path('task/<int:task_id>/subtasks/bulk-create/', subtask_bulk_create, name='subtask_bulk_create'),
    path('subtask/<int:subtask_id>/update-status/', subtask_update_status, name='subtask_update_status'),
    
    # НИР
    path('research/', research_task_list, name='research_task_list'),
    path('research/create/', research_task_create, name='research_task_create'),
    path('research/<int:task_id>/', research_task_detail, name='research_task_detail'),
    path('research/<int:task_id>/edit/', research_task_edit, name='research_task_edit'),
    path('research/stage/<int:stage_id>/', research_stage_detail, name='research_stage_detail'),
    path('research/substage/<int:substage_id>/', research_substage_detail, name='research_substage_detail'),
    path('research/product/<int:product_id>/', research_product_detail, name='research_product_detail'),
    path('research/assign/<str:item_type>/<int:item_id>/', assign_research_performers, name='assign_research_performers'),
    path('research/product/<int:product_id>/status/', update_product_status, name='update_product_status'),
    
    # Импорт
    path('research/import/', import_research_from_docx, name='import_research'),
    path('staff/import/', import_staff_from_excel, name='import_staff'),
    path('task/preview-import/', preview_import, name='preview_import'),
    
    # Структура и дашборды
    path('org-chart/', organization_chart, name='organization_chart'),
    path('department/<int:dept_id>/ajax/', department_detail_ajax, name='department_detail_ajax'),
    path('team/dashboard/', team_dashboard, name='team_dashboard'),
    
    # Продукция
    path('research/products/', views_product.research_product_list, name='research_product_list'),
    path('research/products/<int:product_id>/', views_product.research_product_detail, name='research_product_detail'),
    path('research/products/<int:product_id>/assign/', views_product.assign_product_performer, name='assign_product_performer'),
    path('research/products/<int:product_id>/remove/<int:performer_id>/', views_product.remove_product_performer, name='remove_product_performer'),
    path('research/products/<int:pk>/status/', views_product.update_product_status, name='update_product_status'),
    path('product/<int:product_id>/assign-performers/', product_assign_performers, name='product_assign_performers'),
    path('create-external-employee/', create_external_employee, name='create_external_employee'),
]