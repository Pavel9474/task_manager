from django.urls import path
from . import views

urlpatterns = [
    # ===== Задачи =====
    path('', views.task_list, name='task_list'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/create/', views.task_create, name='task_create'),
    path('task/<int:task_id>/update/', views.task_update, name='task_update'),
    path('task/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('task/<int:task_id>/complete/', views.task_complete, name='task_complete'),
    path('task/<int:task_id>/start/', views.task_start, name='task_start'),
    path('task/<int:task_id>/finish/', views.task_finish, name='task_finish'),
    path('task/<int:task_id>/reset-time/', views.task_reset_time, name='task_reset_time'),
    path('research/import/', views.import_research_from_docx, name='import_research'),
    path('research/<int:task_id>/', views.research_task_detail, name='research_task_detail'),
    
    # ===== Статистика =====
    path('statistics/', views.task_statistics, name='task_statistics'),
    
    # ===== СОТРУДНИКИ (НОВЫЕ МАРШРУТЫ) =====
    # Список сотрудников
    path('employees/', views.employee_list, name='employee_list'),
    
    # Создание сотрудника
    path('employee/create/', views.employee_create, name='employee_create'),
    
    # Детали сотрудника
    path('employee/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    
    # Редактирование сотрудника
    path('employee/<int:employee_id>/update/', views.employee_update, name='employee_update'),
    
    # Удаление сотрудника
    path('employee/<int:employee_id>/delete/', views.employee_delete, name='employee_delete'),
    
    # Активация/деактивация сотрудника
    path('employee/<int:employee_id>/toggle-active/', views.employee_toggle_active, name='employee_toggle_active'),
    
    # ===== ИМПОРТ/ЭКСПОРТ EXCEL =====
    # Импорт из Excel
    path('employees/import/', views.employee_import, name='employee_import'),
    
    # Экспорт в Excel
    path('employees/export/', views.employee_export, name='employee_export'),
    
    # Скачать шаблон Excel
    path('employees/export-template/', views.employee_export_template, name='employee_export_template'),
    
    # ===== НАЗНАЧЕНИЕ ИСПОЛНИТЕЛЕЙ =====
    # Назначение исполнителей на задачу
    path('task/<int:task_id>/assign/', views.task_assign_employees, name='task_assign_employees'),
    
    # Задачи конкретного сотрудника
    path('employee/<int:employee_id>/tasks/', views.employee_tasks, name='employee_tasks'),
    
    # ===== ДАШБОРДЫ =====
    # Дашборд команды
    path('team/dashboard/', views.team_dashboard, name='team_dashboard'),
    
    # ===== API (если нужно) =====
    # API для поиска сотрудников
    path('api/employee-search/', views.employee_search_api, name='employee_search_api'),

    path('task/<int:task_id>/status/', views.task_update_status_ajax, name='task_update_status_ajax'),
    # Подзадачи (этапы)
    path('task/<int:task_id>/subtasks/', views.subtask_list, name='subtask_list'),
    path('task/<int:task_id>/subtask/create/', views.subtask_create, name='subtask_create'),
    path('subtask/<int:subtask_id>/update/', views.subtask_update, name='subtask_update'),
    path('subtask/<int:subtask_id>/delete/', views.subtask_delete, name='subtask_delete'),
    path('task/<int:task_id>/subtasks/bulk-create/', views.subtask_bulk_create, name='subtask_bulk_create'),
    path('subtask/<int:subtask_id>/update-status/', views.subtask_update_status, name='subtask_update_status'),

    # ===== УПРАВЛЕНИЕ НИР =====
    path('research/', views.research_task_list, name='research_task_list'),
    path('research/create/', views.research_task_create, name='research_task_create'),
    path('research/<int:task_id>/', views.research_task_detail, name='research_task_detail'),
    path('research/<int:task_id>/edit/', views.research_task_edit, name='research_task_edit'),
    path('research/stage/<int:stage_id>/', views.research_stage_detail, name='research_stage_detail'),
    path('research/substage/<int:substage_id>/', views.research_substage_detail, name='research_substage_detail'),
    path('research/product/<int:product_id>/', views.research_product_detail, name='research_product_detail'),
    path('research/assign/<str:item_type>/<int:item_id>/', views.assign_research_performers, name='assign_research_performers'),
    path('research/product/<int:product_id>/status/', views.update_product_status, name='update_product_status'),
    path('task/preview-import/', views.preview_import, name='preview_import'),
]