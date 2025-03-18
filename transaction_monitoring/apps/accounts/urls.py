"""
URL patterns for the accounts app.
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),
    
    # Password Reset
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt'
         ), 
         name='password_reset'),
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Settings
    path('settings/', views.settings, name='settings'),
    path('settings/security/', views.security_settings, name='security_settings'),
    path('settings/notifications/', views.notification_settings, name='notification_settings'),
    
    # User Management
    path('admin/users/', views.user_list, name='user_list'),
    path('admin/users/create/', views.user_create, name='user_create'),
    path('admin/users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('admin/users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('admin/users/<int:user_id>/reset-password/', views.user_reset_password, name='user_reset_password'),
    path('admin/users/<int:user_id>/activate/', views.user_activate, name='user_activate'),
    path('admin/users/<int:user_id>/deactivate/', views.user_deactivate, name='user_deactivate'),
    
    # Role Management
    path('admin/roles/', views.role_list, name='role_list'),
    path('admin/roles/create/', views.role_create, name='role_create'),
    path('admin/roles/<int:role_id>/edit/', views.role_edit, name='role_edit'),
    path('admin/roles/<int:role_id>/delete/', views.role_delete, name='role_delete'),
    path('admin/roles/<int:role_id>/permissions/', views.role_permissions, name='role_permissions'),
]