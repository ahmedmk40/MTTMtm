"""
URL patterns for the notifications app.
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('<int:pk>/', views.notification_detail, name='detail'),
    path('<int:pk>/mark-as-read/', views.mark_as_read, name='mark_as_read'),
    path('mark-all-as-read/', views.mark_all_as_read, name='mark_all_as_read'),
    path('<int:pk>/delete/', views.delete_notification, name='delete'),
    path('preferences/', views.preferences, name='preferences'),
    path('badge/', views.notification_badge, name='badge'),
]