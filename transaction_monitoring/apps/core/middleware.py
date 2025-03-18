"""
Custom middleware for the Transaction Monitoring and Fraud Detection System.
"""

import time
import logging
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)


class PerformanceMonitoringMiddleware:
    """
    Middleware to monitor the performance of requests.
    
    This middleware logs the time taken to process a request and the number of database queries executed.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Code to be executed for each request before the view is called
        start_time = time.time()
        
        # Get the number of queries before the view is called
        n_queries_before = len(connection.queries)
        
        # Process the request
        response = self.get_response(request)
        
        # Code to be executed for each request after the view is called
        if settings.DEBUG:
            # Calculate request processing time
            duration = time.time() - start_time
            
            # Calculate the number of queries
            n_queries_after = len(connection.queries)
            n_queries = n_queries_after - n_queries_before
            
            # Log the performance metrics
            logger.debug(
                f"Request: {request.method} {request.path} - "
                f"Time: {duration:.2f}s - "
                f"Queries: {n_queries}"
            )
            
            # Add performance metrics to response headers
            response['X-Request-Time'] = f"{duration:.2f}s"
            response['X-Query-Count'] = str(n_queries)
        
        return response


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to responses.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add Content Security Policy in non-debug mode
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' https://cdn.jsdelivr.net; "
                "style-src 'self' https://cdn.jsdelivr.net; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "img-src 'self' data:; "
                "connect-src 'self'"
            )
        
        return response