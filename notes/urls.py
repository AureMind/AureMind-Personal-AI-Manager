from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'notes'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    path('notes/', views.home, name='home'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('issues/', views.issues, name='issues'),
    path('files/', views.files, name='files'),

    # Auth routes
    path('login/', auth_views.LoginView.as_view(template_name='notes/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('about/', views.about, name='about'),

    # Notes CRUD
    path('note/create/', views.note_create, name='create'),
    path('note/<int:pk>/', views.note_detail, name='detail'),
    path('note/<int:pk>/edit/', views.note_update, name='edit'),
    path('note/<int:pk>/delete/', views.note_delete, name='delete'),
]