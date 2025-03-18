"""
Settings package initialization.
"""

import os

# Set the default Django settings module
environment = os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings.development')