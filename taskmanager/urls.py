# taskmanager/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from tasks.views.auth_views import register

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', register, name='register'),  # добавьте эту строку
    path('', include('tasks.urls')),
]