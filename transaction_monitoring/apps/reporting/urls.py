"""
URL patterns for the reporting app.
"""

from django.urls import path
from . import views

app_name = 'reporting'

urlpatterns = [
    path('', views.report_list, name='list'),
    path('transaction/', views.transaction_report, name='transaction'),
    path('fraud/', views.fraud_report, name='fraud'),
    path('aml/', views.aml_report, name='aml'),
    path('performance/', views.performance_report, name='performance'),
    path('export/<str:report_type>/', views.export_report, name='export'),
]