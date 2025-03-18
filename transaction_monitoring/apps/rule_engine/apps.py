"""
Rule Engine app configuration.
"""

from django.apps import AppConfig


class RuleEngineConfig(AppConfig):
    """Configuration for the Rule Engine app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.rule_engine'
    verbose_name = 'Rule Engine'
    
    def ready(self):
        """
        Initialize app when Django starts.
        """
        # Import signals
        import apps.rule_engine.signals  # noqa