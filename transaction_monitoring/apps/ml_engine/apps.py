"""
ML Engine app configuration.
"""

from django.apps import AppConfig


class MlEngineConfig(AppConfig):
    """Configuration for the ML Engine app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ml_engine'
    verbose_name = 'ML Engine'