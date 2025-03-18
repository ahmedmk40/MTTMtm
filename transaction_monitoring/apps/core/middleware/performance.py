"""
Performance monitoring middleware for the Transaction Monitoring and Fraud Detection System.
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
        n_queries_before = len(connection.queries) if settings.DEBUG else 0
        
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
            
            # Log slow queries (more than 100ms)
            if n_queries > 0:
                for i, query in enumerate(connection.queries[n_queries_before:n_queries_after]):
                    query_time = float(query.get('time', 0))
                    if query_time > 0.1:  # 100ms
                        logger.warning(
                            f"Slow query ({query_time:.2f}s): {query.get('sql', '')}"
                        )
        
        return response