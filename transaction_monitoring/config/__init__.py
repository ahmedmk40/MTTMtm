"""
Config package initialization.
"""

# Import the Celery app from the transaction_monitoring package
from transaction_monitoring import celery as celery_app

__all__ = ('celery_app',)