"""
Velocity Engine app configuration.
"""

from django.apps import AppConfig


class VelocityEngineConfig(AppConfig):
    """Configuration for the Velocity Engine app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.velocity_engine'
    verbose_name = 'Velocity Engine'