"""
Transaction Monitoring package initialization.
"""

# Import Celery app to ensure it's loaded when Django starts
from transaction_monitoring.celery_app import app as celery

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
__all__ = ('celery',)