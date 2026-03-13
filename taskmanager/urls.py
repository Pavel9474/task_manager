from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from tasks import views as task_views  # Правильный импорт из приложения tasks

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tasks.urls')),  # Подключаем URLs из приложения tasks
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', task_views.register, name='register'),  # Используем task_views
]