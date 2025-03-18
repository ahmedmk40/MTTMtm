#!/usr/bin/env python
"""
Script to check Django security settings.

This script analyzes Django settings files for security issues and provides recommendations.
"""

import os
import sys
import re
import json
from pathlib import Path
import importlib.util
import datetime

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Output file setup
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'django_security_check_{timestamp}.json'
output_path = project_root / 'reports' / output_file

# Create reports directory if it doesn't exist
os.makedirs(project_root / 'reports', exist_ok=True)

# Initialize the report
report = {
    'timestamp': datetime.datetime.now().isoformat(),
    'project': 'Transaction Monitoring and Fraud Detection System',
    'settings_files': [],
    'issues': [],
    'recommendations': [],
}


def load_settings_module(settings_path):
    """Load a Django settings module from a file path."""
    try:
        # Get the module name from the file path
        module_name = settings_path.stem
        
        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, settings_path)
        settings_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings_module)
        
        return settings_module
    except Exception as e:
        print(f"Error loading settings module {settings_path}: {e}")
        return None


def check_security_settings(settings_module, settings_path):
    """Check Django security settings in a settings module."""
    issues = []
    
    # Get the relative path for reporting
    rel_path = settings_path.relative_to(project_root)
    
    # Add the settings file to the report
    report['settings_files'].append(str(rel_path))
    
    # Check DEBUG setting
    debug = getattr(settings_module, 'DEBUG', None)
    if debug is True:
        issues.append({
            'file': str(rel_path),
            'setting': 'DEBUG',
            'value': debug,
            'issue': 'DEBUG is set to True. This should be False in production.',
            'severity': 'high',
        })
    
    # Check SECRET_KEY
    secret_key = getattr(settings_module, 'SECRET_KEY', None)
    if secret_key:
        # Check if it's a default or weak secret key
        if 'django-insecure' in str(secret_key) or len(str(secret_key)) < 32:
            issues.append({
                'file': str(rel_path),
                'setting': 'SECRET_KEY',
                'value': '***REDACTED***',
                'issue': 'SECRET_KEY appears to be default or weak. Use a strong, unique secret key.',
                'severity': 'high',
            })
    
    # Check ALLOWED_HOSTS
    allowed_hosts = getattr(settings_module, 'ALLOWED_HOSTS', None)
    if allowed_hosts is not None:
        if not allowed_hosts or '*' in allowed_hosts:
            issues.append({
                'file': str(rel_path),
                'setting': 'ALLOWED_HOSTS',
                'value': allowed_hosts,
                'issue': 'ALLOWED_HOSTS is empty or contains "*". Specify the exact hostnames in production.',
                'severity': 'medium',
            })
    
    # Check CSRF settings
    csrf_middleware = 'django.middleware.csrf.CsrfViewMiddleware'
    middleware = getattr(settings_module, 'MIDDLEWARE', [])
    if csrf_middleware not in middleware:
        issues.append({
            'file': str(rel_path),
            'setting': 'MIDDLEWARE',
            'value': '***TRUNCATED***',
            'issue': f'CSRF middleware ({csrf_middleware}) is missing from MIDDLEWARE.',
            'severity': 'high',
        })
    
    # Check session cookie settings
    session_cookie_secure = getattr(settings_module, 'SESSION_COOKIE_SECURE', False)
    if not session_cookie_secure:
        issues.append({
            'file': str(rel_path),
            'setting': 'SESSION_COOKIE_SECURE',
            'value': session_cookie_secure,
            'issue': 'SESSION_COOKIE_SECURE is not set to True. Cookies should be served over HTTPS only.',
            'severity': 'medium',
        })
    
    session_cookie_httponly = getattr(settings_module, 'SESSION_COOKIE_HTTPONLY', False)
    if not session_cookie_httponly:
        issues.append({
            'file': str(rel_path),
            'setting': 'SESSION_COOKIE_HTTPONLY',
            'value': session_cookie_httponly,
            'issue': 'SESSION_COOKIE_HTTPONLY is not set to True. Cookies should not be accessible via JavaScript.',
            'severity': 'medium',
        })
    
    # Check CSRF cookie settings
    csrf_cookie_secure = getattr(settings_module, 'CSRF_COOKIE_SECURE', False)
    if not csrf_cookie_secure:
        issues.append({
            'file': str(rel_path),
            'setting': 'CSRF_COOKIE_SECURE',
            'value': csrf_cookie_secure,
            'issue': 'CSRF_COOKIE_SECURE is not set to True. CSRF cookies should be served over HTTPS only.',
            'severity': 'medium',
        })
    
    csrf_cookie_httponly = getattr(settings_module, 'CSRF_COOKIE_HTTPONLY', False)
    if not csrf_cookie_httponly:
        issues.append({
            'file': str(rel_path),
            'setting': 'CSRF_COOKIE_HTTPONLY',
            'value': csrf_cookie_httponly,
            'issue': 'CSRF_COOKIE_HTTPONLY is not set to True. CSRF cookies should not be accessible via JavaScript.',
            'severity': 'medium',
        })
    
    # Check SECURE_BROWSER_XSS_FILTER
    secure_browser_xss_filter = getattr(settings_module, 'SECURE_BROWSER_XSS_FILTER', False)
    if not secure_browser_xss_filter:
        issues.append({
            'file': str(rel_path),
            'setting': 'SECURE_BROWSER_XSS_FILTER',
            'value': secure_browser_xss_filter,
            'issue': 'SECURE_BROWSER_XSS_FILTER is not set to True. XSS filtering should be enabled in the browser.',
            'severity': 'medium',
        })
    
    # Check SECURE_CONTENT_TYPE_NOSNIFF
    secure_content_type_nosniff = getattr(settings_module, 'SECURE_CONTENT_TYPE_NOSNIFF', False)
    if not secure_content_type_nosniff:
        issues.append({
            'file': str(rel_path),
            'setting': 'SECURE_CONTENT_TYPE_NOSNIFF',
            'value': secure_content_type_nosniff,
            'issue': 'SECURE_CONTENT_TYPE_NOSNIFF is not set to True. Browser should not guess content types.',
            'severity': 'medium',
        })
    
    # Check SECURE_SSL_REDIRECT
    secure_ssl_redirect = getattr(settings_module, 'SECURE_SSL_REDIRECT', False)
    if not secure_ssl_redirect:
        issues.append({
            'file': str(rel_path),
            'setting': 'SECURE_SSL_REDIRECT',
            'value': secure_ssl_redirect,
            'issue': 'SECURE_SSL_REDIRECT is not set to True. HTTP requests should be redirected to HTTPS.',
            'severity': 'medium',
        })
    
    # Check SECURE_HSTS_SECONDS
    secure_hsts_seconds = getattr(settings_module, 'SECURE_HSTS_SECONDS', 0)
    if secure_hsts_seconds < 31536000:  # 1 year in seconds
        issues.append({
            'file': str(rel_path),
            'setting': 'SECURE_HSTS_SECONDS',
            'value': secure_hsts_seconds,
            'issue': 'SECURE_HSTS_SECONDS is not set to a sufficiently high value. Recommended: 31536000 (1 year).',
            'severity': 'low',
        })
    
    # Check SECURE_HSTS_INCLUDE_SUBDOMAINS
    secure_hsts_include_subdomains = getattr(settings_module, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False)
    if not secure_hsts_include_subdomains:
        issues.append({
            'file': str(rel_path),
            'setting': 'SECURE_HSTS_INCLUDE_SUBDOMAINS',
            'value': secure_hsts_include_subdomains,
            'issue': 'SECURE_HSTS_INCLUDE_SUBDOMAINS is not set to True. HSTS should include subdomains.',
            'severity': 'low',
        })
    
    # Check SECURE_HSTS_PRELOAD
    secure_hsts_preload = getattr(settings_module, 'SECURE_HSTS_PRELOAD', False)
    if not secure_hsts_preload:
        issues.append({
            'file': str(rel_path),
            'setting': 'SECURE_HSTS_PRELOAD',
            'value': secure_hsts_preload,
            'issue': 'SECURE_HSTS_PRELOAD is not set to True. Site should be submitted to HSTS preload list.',
            'severity': 'low',
        })
    
    # Check X_FRAME_OPTIONS
    x_frame_options = getattr(settings_module, 'X_FRAME_OPTIONS', None)
    if x_frame_options != 'DENY':
        issues.append({
            'file': str(rel_path),
            'setting': 'X_FRAME_OPTIONS',
            'value': x_frame_options,
            'issue': 'X_FRAME_OPTIONS is not set to "DENY". Site should not be displayed in frames.',
            'severity': 'medium',
        })
    
    # Check database settings
    databases = getattr(settings_module, 'DATABASES', {})
    for db_name, db_config in databases.items():
        # Check for hardcoded credentials
        if 'PASSWORD' in db_config and db_config['PASSWORD'] and db_config['PASSWORD'] != '':
            issues.append({
                'file': str(rel_path),
                'setting': f'DATABASES["{db_name}"]["PASSWORD"]',
                'value': '***REDACTED***',
                'issue': 'Database password is hardcoded in settings. Use environment variables instead.',
                'severity': 'high',
            })
    
    # Check email settings
    email_host = getattr(settings_module, 'EMAIL_HOST', None)
    email_host_user = getattr(settings_module, 'EMAIL_HOST_USER', None)
    email_host_password = getattr(settings_module, 'EMAIL_HOST_PASSWORD', None)
    
    if email_host and email_host_user and email_host_password:
        issues.append({
            'file': str(rel_path),
            'setting': 'EMAIL_HOST_PASSWORD',
            'value': '***REDACTED***',
            'issue': 'Email password is hardcoded in settings. Use environment variables instead.',
            'severity': 'high',
        })
    
    # Check for insecure authentication backends
    authentication_backends = getattr(settings_module, 'AUTHENTICATION_BACKENDS', [])
    for backend in authentication_backends:
        if 'AllowAllUsersModelBackend' in backend or 'AllowAllUsersRemoteUserBackend' in backend:
            issues.append({
                'file': str(rel_path),
                'setting': 'AUTHENTICATION_BACKENDS',
                'value': backend,
                'issue': f'Insecure authentication backend: {backend}',
                'severity': 'high',
            })
    
    # Check password validators
    password_validators = getattr(settings_module, 'AUTH_PASSWORD_VALIDATORS', [])
    if not password_validators:
        issues.append({
            'file': str(rel_path),
            'setting': 'AUTH_PASSWORD_VALIDATORS',
            'value': password_validators,
            'issue': 'No password validators configured. Password strength is not enforced.',
            'severity': 'medium',
        })
    
    return issues


def generate_recommendations(issues):
    """Generate recommendations based on identified issues."""
    recommendations = []
    
    # Group issues by severity
    high_issues = [issue for issue in issues if issue['severity'] == 'high']
    medium_issues = [issue for issue in issues if issue['severity'] == 'medium']
    low_issues = [issue for issue in issues if issue['severity'] == 'low']
    
    # Add recommendations for high severity issues
    if high_issues:
        recommendations.append({
            'priority': 'Critical',
            'description': 'Address all high severity issues immediately as they pose significant security risks.',
            'issues': [issue['issue'] for issue in high_issues],
        })
    
    # Add specific recommendations based on issue types
    if any(issue['setting'] == 'DEBUG' for issue in issues):
        recommendations.append({
            'priority': 'High',
            'description': 'Set DEBUG = False in production settings and ensure proper error handling.',
        })
    
    if any(issue['setting'] == 'SECRET_KEY' for issue in issues):
        recommendations.append({
            'priority': 'High',
            'description': 'Generate a new strong SECRET_KEY and store it securely (e.g., in environment variables).',
        })
    
    if any('PASSWORD' in issue['setting'] for issue in issues):
        recommendations.append({
            'priority': 'High',
            'description': 'Move all sensitive credentials to environment variables or a secure vault.',
        })
    
    if any(issue['setting'] in ['SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE', 'SECURE_SSL_REDIRECT'] for issue in issues):
        recommendations.append({
            'priority': 'Medium',
            'description': 'Configure HTTPS-related settings to ensure secure communication.',
        })
    
    if any(issue['setting'] in ['SECURE_BROWSER_XSS_FILTER', 'SECURE_CONTENT_TYPE_NOSNIFF', 'X_FRAME_OPTIONS'] for issue in issues):
        recommendations.append({
            'priority': 'Medium',
            'description': 'Configure security headers to protect against common web vulnerabilities.',
        })
    
    if any(issue['setting'] in ['SECURE_HSTS_SECONDS', 'SECURE_HSTS_INCLUDE_SUBDOMAINS', 'SECURE_HSTS_PRELOAD'] for issue in issues):
        recommendations.append({
            'priority': 'Medium',
            'description': 'Configure HTTP Strict Transport Security (HSTS) for enhanced HTTPS security.',
        })
    
    # Add general recommendations
    recommendations.extend([
        {
            'priority': 'Medium',
            'description': 'Implement a settings module specifically for production with all security settings properly configured.',
        },
        {
            'priority': 'Medium',
            'description': 'Use environment variables for all sensitive configuration values.',
        },
        {
            'priority': 'Low',
            'description': 'Regularly review and update security settings as Django evolves.',
        },
    ])
    
    return recommendations


def main():
    """Check Django security settings and generate a report."""
    print(f"Checking Django security settings for {report['project']}...")
    
    # Find all settings files
    settings_dir = project_root / 'config' / 'settings'
    settings_files = list(settings_dir.glob('*.py'))
    
    if not settings_files:
        print("No settings files found.")
        return
    
    all_issues = []
    
    # Check each settings file
    for settings_path in settings_files:
        print(f"Checking {settings_path.name}...")
        
        # Skip __init__.py
        if settings_path.name == '__init__.py':
            continue
        
        # Load the settings module
        settings_module = load_settings_module(settings_path)
        if settings_module:
            # Check security settings
            issues = check_security_settings(settings_module, settings_path)
            all_issues.extend(issues)
    
    # Add issues to the report
    report['issues'] = all_issues
    
    # Generate recommendations
    report['recommendations'] = generate_recommendations(all_issues)
    
    # Save the report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\nDjango Security Check Summary:")
    print(f"Total Issues: {len(all_issues)}")
    print(f"High Severity: {len([issue for issue in all_issues if issue['severity'] == 'high'])}")
    print(f"Medium Severity: {len([issue for issue in all_issues if issue['severity'] == 'medium'])}")
    print(f"Low Severity: {len([issue for issue in all_issues if issue['severity'] == 'low'])}")
    print(f"\nFull report saved to {output_path}")


if __name__ == '__main__':
    main()