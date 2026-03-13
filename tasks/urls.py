from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/create/', views.task_create, name='task_create'),
    path('task/<int:task_id>/update/', views.task_update, name='task_update'),
    path('task/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('task/<int:task_id>/complete/', views.task_complete, name='task_complete'),
    path('task/<int:task_id>/start/', views.task_start, name='task_start'),
    path('task/<int:task_id>/finish/', views.task_finish, name='task_finish'),
    path('task/<int:task_id>/reset-time/', views.task_reset_time, name='task_reset_time'),
    
    # Добавьте эту строку для статистики
    path('statistics/', views.task_statistics, name='task_statistics'),
]