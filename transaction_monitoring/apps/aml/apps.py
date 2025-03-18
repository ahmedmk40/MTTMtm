"""
AML app configuration.
"""

from django.apps import AppConfig


class AmlConfig(AppConfig):
    """Configuration for the AML app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.aml'
    verbose_name = 'Anti-Money Laundering'