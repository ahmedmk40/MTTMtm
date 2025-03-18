"""
URL patterns for the transactions app.
"""

from django.urls import path
from . import views
from . import views_network
from . import views_test
from . import views_simple

app_name = 'transactions'

urlpatterns = [
    path('', views.transaction_list, name='list'),
    path('create/', views.transaction_create, name='create'),
    path('process/', views.transaction_create, name='process'),  # Redirect to create view for backward compatibility
    path('flagged/', views.flagged_transactions, name='flagged'),
    path('test/', views_test.test_view, name='test_view'),
    path('simple-network/', views_simple.simple_network, name='simple_network'),
    path('<str:transaction_id>/', views.transaction_detail, name='detail'),
    
    # Network visualization
    path('network/', views_network.network_dashboard, name='network_dashboard'),
    path('network/data/', views_network.network_data, name='network_data'),
    path('network/user/<str:user_id>/', views_network.user_network, name='user_network'),
    path('network/user/<str:user_id>/data/', views_network.user_network_data, name='user_network_data'),
    path('network/merchant/<str:merchant_id>/', views_network.merchant_network, name='merchant_network'),
    path('network/merchant/<str:merchant_id>/data/', views_network.merchant_network_data, name='merchant_network_data'),
    path('network/patterns/', views_network.unusual_patterns, name='unusual_patterns'),
]