"""
Security middleware for the Transaction Monitoring and Fraud Detection System.
"""

from django.conf import settings


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.
    
    This middleware adds various security headers to HTTP responses to enhance
    the security of the application against common web vulnerabilities.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add Content-Security-Policy header
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' https://cdn.jsdelivr.net",
            "style-src 'self' https://cdn.jsdelivr.net",
            "font-src 'self' https://cdn.jsdelivr.net",
            "img-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "base-uri 'self'",
            "object-src 'none'",
        ]
        
        # In development, allow unsafe-inline and unsafe-eval for debugging
        if settings.DEBUG:
            csp_directives[1] += " 'unsafe-inline' 'unsafe-eval'"  # script-src
            csp_directives[2] += " 'unsafe-inline'"  # style-src
        
        response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # Add X-Content-Type-Options header to prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Add X-Frame-Options header to prevent clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Add X-XSS-Protection header to enable browser's XSS filter
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Add Referrer-Policy header to control referrer information
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add Permissions-Policy header to control browser features
        permissions_policy = [
            'accelerometer=()',
            'camera=()',
            'geolocation=()',
            'gyroscope=()',
            'magnetometer=()',
            'microphone=()',
            'payment=()',
            'usb=()'
        ]
        response['Permissions-Policy'] = ', '.join(permissions_policy)
        
        # Add Feature-Policy header for backward compatibility
        response['Feature-Policy'] = ', '.join(permissions_policy)
        
        return response


class ContentSecurityPolicyReportingMiddleware:
    """
    Middleware to add Content-Security-Policy-Report-Only header.
    
    This middleware is useful during the testing phase of CSP implementation
    to monitor violations without blocking content.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only add the header in non-production environments
        if settings.DEBUG or getattr(settings, 'TESTING', False):
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline' 'unsafe-eval'",
                "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'",
                "font-src 'self' https://cdn.jsdelivr.net",
                "img-src 'self' data:",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "form-action 'self'",
                "base-uri 'self'",
                "object-src 'none'",
                "report-uri /api/csp-report/"
            ]
            
            response['Content-Security-Policy-Report-Only'] = '; '.join(csp_directives)
        
        return response


class StrictTransportSecurityMiddleware:
    """
    Middleware to add HTTP Strict Transport Security (HSTS) header.
    
    This middleware adds the HSTS header to enforce HTTPS connections.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only add HSTS header in production
        if not settings.DEBUG:
            # max-age is set to 1 year in seconds
            # includeSubDomains ensures all subdomains are also HTTPS
            # preload allows inclusion in browser preload lists
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response