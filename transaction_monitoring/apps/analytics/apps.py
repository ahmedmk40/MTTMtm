from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.analytics'
    verbose_name = 'Transaction Analytics'
    
    def ready(self):
        """
        Initialize app when Django starts.
        """
        try:
            # Import signals
            import apps.analytics.signals  # noqa
        except ImportError:
            pass
