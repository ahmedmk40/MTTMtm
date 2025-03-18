"""
Transaction Monitoring and Fraud Detection System.
"""

# Import Celery app
from .celery import app as celery_app

__all__ = ('celery_app',)