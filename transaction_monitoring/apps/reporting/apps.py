"""
Reporting app configuration.
"""

from django.apps import AppConfig


class ReportingConfig(AppConfig):
    """Configuration for the reporting app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reporting'
    verbose_name = 'Reporting'