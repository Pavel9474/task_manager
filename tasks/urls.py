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
]