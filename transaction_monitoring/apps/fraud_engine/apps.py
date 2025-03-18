"""
Fraud Engine app configuration.
"""

from django.apps import AppConfig


class FraudEngineConfig(AppConfig):
    """Configuration for the Fraud Engine app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.fraud_engine'
    verbose_name = 'Fraud Engine'