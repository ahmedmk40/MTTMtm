"""
Development settings for Transaction Monitoring and Fraud Detection System.
"""

from .base import *  # noqa

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Additional installed apps for development
INSTALLED_APPS += [
    'django_extensions',
]

# Celery settings
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Debug toolbar settings
try:
    import debug_toolbar  # noqa
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
        'apps.core.middleware.PerformanceMonitoringMiddleware',
        'apps.core.middleware.SecurityHeadersMiddleware',
    ]
    INTERNAL_IPS = ['127.0.0.1']
    
    # Debug Toolbar Configuration
    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
        'debug_toolbar.panels.profiling.ProfilingPanel',
    ]
    
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
        'SHOW_COLLAPSED': True,
        'SHOW_TEMPLATE_CONTEXT': True,
        'ENABLE_STACKTRACES': True,
        'IS_RUNNING_TESTS': False,
    }
except ImportError:
    pass