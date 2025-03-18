"""
URL patterns for the Rule Engine app.
"""

from django.urls import path
from . import views

app_name = 'rule_engine'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Rules
    path('rules/', views.rule_list, name='list'),
    path('rules/create/', views.rule_create, name='create'),
    path('rules/<int:rule_id>/', views.rule_detail, name='detail'),
    path('rules/<int:rule_id>/edit/', views.rule_edit, name='edit'),
    path('rules/<int:rule_id>/toggle/', views.rule_toggle_active, name='toggle'),
    path('rules/test/', views.rule_test, name='test'),
    path('rules/<int:rule_id>/test/', views.rule_test, name='test_rule'),
    
    # Rule Sets
    path('rulesets/', views.ruleset_list, name='ruleset_list'),
    path('rulesets/create/', views.ruleset_create, name='ruleset_create'),
    path('rulesets/<int:ruleset_id>/', views.ruleset_detail, name='ruleset_detail'),
    path('rulesets/<int:ruleset_id>/edit/', views.ruleset_edit, name='ruleset_edit'),
    path('rulesets/<int:ruleset_id>/toggle/', views.ruleset_toggle_active, name='ruleset_toggle'),
    
    # Executions
    path('executions/', views.execution_list, name='execution_list'),
    path('executions/<int:execution_id>/', views.execution_detail, name='execution_detail'),
]