"""
Test settings for Transaction Monitoring and Fraud Detection System.
"""

from .base import *  # noqa

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Password hashers (faster for testing)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable migrations for tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Celery settings for testing
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable throttling for tests
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []  # noqa