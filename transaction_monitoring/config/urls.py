"""
URL Configuration for Transaction Monitoring and Fraud Detection System.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.api.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('transactions/', include('apps.transactions.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('reports/', include('apps.reporting.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('cases/', include('apps.cases.urls')),
    path('rules/', include('apps.rule_engine.urls')),
    path('ml/', include('apps.ml_engine.urls')),
    path('fraud/', include('apps.fraud_engine.urls')),
    path('network/', include('network_viz.urls')),
    path('', include('apps.core.urls')),
]

# Add debug toolbar URLs in development
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass

    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)