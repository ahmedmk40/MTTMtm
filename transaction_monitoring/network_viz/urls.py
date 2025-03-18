"""
URL patterns for the network visualization app.
"""

from django.urls import path
from . import views

app_name = 'network_viz'

urlpatterns = [
    path('', views.network_dashboard, name='dashboard'),
    path('data/', views.network_data, name='data'),
]