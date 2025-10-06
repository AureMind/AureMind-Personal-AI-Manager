from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'notes'

urlpatterns = [
    path('', views.home, name='home'),

    # login/logout routes
    path('login/', auth_views.LoginView.as_view(template_name='notes/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),

    path('note/<int:pk>/', views.note_detail, name='detail'),
    path('note/create/', views.note_create, name='create'),
    path('note/<int:pk>/edit/', views.note_update, name='edit'),
    path('note/<int:pk>/delete/', views.note_delete, name='delete'),
]
