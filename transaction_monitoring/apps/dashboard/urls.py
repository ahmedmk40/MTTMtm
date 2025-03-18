"""
URL patterns for the dashboard app.
"""

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='index'),
    path('compliance/', views.compliance_dashboard, name='compliance'),
    path('analyst/', views.analyst_dashboard, name='analyst'),
    path('risk/', views.risk_dashboard, name='risk'),
    path('executive/', views.executive_dashboard, name='executive'),
]