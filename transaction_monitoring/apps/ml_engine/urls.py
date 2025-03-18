"""
URL patterns for the ML Engine app.
"""

from django.urls import path
from . import views
from .views.response_code_views import response_code_dashboard

app_name = 'ml_engine'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Models
    path('models/', views.model_list, name='model_list'),
    path('models/create/', views.model_create, name='model_create'),
    path('models/<int:model_id>/', views.model_detail, name='model_detail'),
    path('models/<int:model_id>/activate/', views.model_activate, name='model_activate'),
    path('models/<int:model_id>/deactivate/', views.model_deactivate, name='model_deactivate'),
    path('models/<int:model_id>/delete/', views.model_delete, name='model_delete'),
    
    # Predictions
    path('predictions/', views.prediction_list, name='prediction_list'),
    path('predictions/<int:prediction_id>/', views.prediction_detail, name='prediction_detail'),
    
    # Features
    path('features/', views.feature_list, name='feature_list'),
    path('features/create/', views.feature_create, name='feature_create'),
    path('features/<int:feature_id>/', views.feature_detail, name='feature_detail'),
    path('features/<int:feature_id>/edit/', views.feature_edit, name='feature_edit'),
    path('features/<int:feature_id>/delete/', views.feature_delete, name='feature_delete'),
    
    # Analytics
    path('analytics/', views.analytics, name='analytics'),
    path('analytics/performance/', views.model_performance, name='model_performance'),
    path('analytics/feature-importance/', views.feature_importance, name='feature_importance'),
    
    # Monitoring
    path('monitoring/', views.monitoring_dashboard, name='monitoring_dashboard'),
    path('monitoring/drift/', views.model_drift, name='model_drift'),
    path('monitoring/features/', views.feature_distribution, name='feature_distribution'),
    
    # Explainability
    path('explainability/<int:prediction_id>/', views.prediction_explainability, name='prediction_explainability'),
    
    # A/B Testing
    path('abtests/', views.abtest_list, name='abtest_list'),
    path('abtests/create/', views.abtest_create, name='abtest_create'),
    path('abtests/<str:test_id>/', views.abtest_detail, name='abtest_detail'),
    path('abtests/<str:test_id>/end/', views.abtest_end, name='abtest_end'),
    
    # Training
    path('training/', views.training_dashboard, name='training_dashboard'),
    path('training/new/', views.training_new, name='training_new'),
    path('training/<int:training_id>/', views.training_detail, name='training_detail'),
    
    # API endpoints
    path('api/predict/', views.api_predict, name='api_predict'),
    path('api/models/', views.api_models, name='api_models'),
    path('api/features/', views.api_features, name='api_features'),
    
    # Response Code Analytics
    path('analytics/response-codes/', response_code_dashboard, name='response_code_dashboard'),
]