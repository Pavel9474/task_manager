# taskmanager/urls.py

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from tasks.views import register  # теперь должно работать

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tasks.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', register, name='register'),
]