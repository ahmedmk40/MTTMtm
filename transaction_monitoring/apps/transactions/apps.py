"""
Transactions app configuration.
"""

from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    """Configuration for the transactions app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.transactions'
    verbose_name = 'Transactions'
    
    def ready(self):
        """
        Initialize app when Django starts.
        """
        import apps.transactions.signals  # noqa