"""
URL patterns for the Analytics app.
"""

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.transaction_analytics_dashboard, name='dashboard'),
    path('response-codes/', views.response_code_analytics, name='response_codes'),
    path('transaction-types/', views.transaction_type_analytics, name='transaction_types'),
    path('merchant/', views.merchant_analysis, name='merchant_analysis'),
    path('user/', views.user_analysis, name='user_analysis'),
    path('risk-rankings/', views.risk_rankings, name='risk_rankings'),
]