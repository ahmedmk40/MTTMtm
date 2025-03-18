"""
URL patterns for the API app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from apps.transactions.views import (
    TransactionViewSet,
    POSTransactionViewSet,
    EcommerceTransactionViewSet,
    WalletTransactionViewSet
)
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'transactions', TransactionViewSet)
router.register(r'pos-transactions', POSTransactionViewSet)
router.register(r'ecommerce-transactions', EcommerceTransactionViewSet)
router.register(r'wallet-transactions', WalletTransactionViewSet)

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    path('token/', obtain_auth_token, name='token_obtain'),
    path('process-transaction/', views.process_transaction, name='process_transaction'),
    path('health/', views.health_check, name='health_check'),
]