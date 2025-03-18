"""
Views for the core app.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import redis
import json


def home(request):
    """
    Home page view.
    """
    return render(request, 'core/home.html')


def health_check(request):
    """
    Health check endpoint for monitoring.
    """
    # Check database connection
    db_status = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        db_status = False
    
    # Check Redis connection
    redis_status = True
    try:
        r = redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
    except Exception:
        redis_status = False
    
    # Overall status
    status = "healthy" if db_status and redis_status else "unhealthy"
    
    # Response data
    data = {
        "status": status,
        "database": "connected" if db_status else "disconnected",
        "redis": "connected" if redis_status else "disconnected",
        "version": getattr(settings, "VERSION", "1.0.0"),
    }
    
    return JsonResponse(data)