"""
URL patterns for the Fraud Engine app.
"""

from django.urls import path
from . import views

app_name = 'fraud_engine'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Blocklist
    path('blocklist/', views.blocklist, name='blocklist'),
    path('blocklist/add/', views.blocklist_add, name='blocklist_add'),
    path('blocklist/<int:blocklist_id>/edit/', views.blocklist_edit, name='blocklist_edit'),
    path('blocklist/<int:blocklist_id>/delete/', views.blocklist_delete, name='blocklist_delete'),
    
    # Fraud Cases
    path('cases/', views.fraud_cases, name='cases'),
    path('cases/<str:case_id>/', views.fraud_case_detail, name='case_detail'),
    
    # Detection Results
    path('results/', views.detection_results, name='results'),
    path('results/<str:transaction_id>/', views.detection_result_detail, name='result_detail'),
]