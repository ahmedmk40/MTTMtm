"""
Views for ML Engine monitoring.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count, Max, Min, F, Q
from datetime import datetime, timedelta
import json

from .models import MLModel, MLPrediction
from .services.monitoring_service import (
    get_model_performance_metrics,
    get_model_drift_metrics,
    get_feature_distribution
)
from .services.explainability_service import (
    generate_prediction_explanation,
    generate_feature_importance_plot
)
from .services.versioning_service import (
    setup_ab_test,
    get_ab_test_results,
    end_ab_test
)


@login_required
def monitoring_dashboard(request):
    """
    View for the ML monitoring dashboard.
    """
    # Get performance metrics for all models
    metrics = get_model_performance_metrics(days=30)
    
    # Get active models
    active_models = MLModel.objects.filter(is_active=True)
    
    # Check for model drift
    drift_alerts = []
    for model in active_models:
        drift_metrics = get_model_drift_metrics(model.id, days=30)
        if drift_metrics.get('drift_detected', False):
            drift_alerts.append({
                'model_id': model.id,
                'model_name': model.name,
                'model_version': model.version,
                'drift_metrics': drift_metrics.get('drift_metrics', {})
            })
    
    # Get A/B tests
    ab_tests = []
    for model in active_models:
        if model.metadata and 'ab_test' in model.metadata and model.metadata['ab_test'].get('is_active', False):
            test_id = model.metadata['ab_test'].get('test_id')
            if test_id and test_id not in [t.get('test_id') for t in ab_tests]:
                test_results = get_ab_test_results(test_id)
                if 'error' not in test_results:
                    ab_tests.append(test_results)
    
    context = {
        'title': 'ML Monitoring Dashboard',
        'metrics': metrics,
        'active_models': active_models,
        'drift_alerts': drift_alerts,
        'ab_tests': ab_tests
    }
    
    return render(request, 'ml_engine/monitoring_dashboard.html', context)


@login_required
def model_drift(request):
    """
    View for model drift analysis.
    """
    model_id = request.GET.get('model_id')
    days = int(request.GET.get('days', 30))
    
    if not model_id:
        # If no model specified, show drift for all active models
        active_models = MLModel.objects.filter(is_active=True)
        drift_results = []
        
        for model in active_models:
            drift_metrics = get_model_drift_metrics(model.id, days=days)
            drift_results.append({
                'model_id': model.id,
                'model_name': model.name,
                'model_version': model.version,
                'drift_detected': drift_metrics.get('drift_detected', False),
                'drift_metrics': drift_metrics.get('drift_metrics', {})
            })
        
        context = {
            'title': 'Model Drift Analysis',
            'drift_results': drift_results,
            'days': days
        }
    else:
        # Show drift for specific model
        model = get_object_or_404(MLModel, id=model_id)
        drift_metrics = get_model_drift_metrics(model.id, days=days)
        
        context = {
            'title': f'Model Drift Analysis - {model.name} v{model.version}',
            'model': model,
            'drift_metrics': drift_metrics,
            'days': days
        }
    
    return render(request, 'ml_engine/model_drift.html', context)


@login_required
def feature_distribution(request):
    """
    View for feature distribution analysis.
    """
    model_id = request.GET.get('model_id')
    feature_name = request.GET.get('feature')
    days = int(request.GET.get('days', 30))
    
    if not model_id or not feature_name:
        # Show form to select model and feature
        active_models = MLModel.objects.filter(is_active=True)
        
        context = {
            'title': 'Feature Distribution Analysis',
            'active_models': active_models,
            'days': days
        }
    else:
        # Show feature distribution for specific model and feature
        model = get_object_or_404(MLModel, id=model_id)
        distribution = get_feature_distribution(model.id, feature_name, days=days)
        
        context = {
            'title': f'Feature Distribution - {feature_name}',
            'model': model,
            'feature_name': feature_name,
            'distribution': distribution,
            'days': days
        }
    
    return render(request, 'ml_engine/feature_distribution.html', context)


@login_required
def prediction_explainability(request, prediction_id):
    """
    View for prediction explainability.
    """
    prediction = get_object_or_404(MLPrediction, id=prediction_id)
    
    # Generate explanation
    prediction_result = {
        'risk_score': prediction.prediction,
        'model_name': prediction.model.name,
        'model_version': prediction.model.version,
        'explanation': prediction.explanation
    }
    
    explanation = generate_prediction_explanation(prediction_result, prediction.features)
    
    context = {
        'title': f'Prediction Explainability - {prediction.transaction_id}',
        'prediction': prediction,
        'explanation': explanation
    }
    
    return render(request, 'ml_engine/prediction_explainability.html', context)


@login_required
def abtest_list(request):
    """
    View for A/B test list.
    """
    # Find all models participating in A/B tests
    models_in_tests = MLModel.objects.filter(metadata__has_key='ab_test')
    
    # Get unique test IDs
    test_ids = set()
    for model in models_in_tests:
        if model.metadata and 'ab_test' in model.metadata:
            test_id = model.metadata['ab_test'].get('test_id')
            if test_id:
                test_ids.add(test_id)
    
    # Get test results for each test
    ab_tests = []
    for test_id in test_ids:
        test_results = get_ab_test_results(test_id)
        if 'error' not in test_results:
            ab_tests.append(test_results)
    
    # Sort by start date (newest first)
    ab_tests.sort(key=lambda x: x.get('start_date', ''), reverse=True)
    
    context = {
        'title': 'A/B Tests',
        'ab_tests': ab_tests
    }
    
    return render(request, 'ml_engine/abtest_list.html', context)


@login_required
def abtest_create(request):
    """
    View for creating an A/B test.
    """
    if request.method == 'POST':
        model_a_id = request.POST.get('model_a')
        model_b_id = request.POST.get('model_b')
        traffic_split = float(request.POST.get('traffic_split', 0.5))
        test_name = request.POST.get('test_name')
        
        if not model_a_id or not model_b_id:
            messages.error(request, 'Please select both models for the A/B test')
            return redirect('ml_engine:abtest_create')
        
        # Set up A/B test
        result = setup_ab_test(
            model_a_id=int(model_a_id),
            model_b_id=int(model_b_id),
            traffic_split=traffic_split,
            test_name=test_name
        )
        
        if 'error' in result:
            messages.error(request, f"Error setting up A/B test: {result['error']}")
            return redirect('ml_engine:abtest_create')
        
        messages.success(request, f"A/B test '{result['test_name']}' created successfully")
        return redirect('ml_engine:abtest_detail', test_id=result['test_id'])
    
    # GET request - show form
    active_models = MLModel.objects.filter(is_active=True)
    
    context = {
        'title': 'Create A/B Test',
        'active_models': active_models
    }
    
    return render(request, 'ml_engine/abtest_create.html', context)


@login_required
def abtest_detail(request, test_id):
    """
    View for A/B test details.
    """
    # Get test results
    test_results = get_ab_test_results(test_id)
    
    if 'error' in test_results:
        messages.error(request, f"Error getting A/B test results: {test_results['error']}")
        return redirect('ml_engine:abtest_list')
    
    context = {
        'title': f"A/B Test - {test_results['test_name']}",
        'test': test_results
    }
    
    return render(request, 'ml_engine/abtest_detail.html', context)


@login_required
def abtest_end(request, test_id):
    """
    View for ending an A/B test.
    """
    if request.method == 'POST':
        winner = request.POST.get('winner')
        
        # End A/B test
        result = end_ab_test(test_id, winner)
        
        if 'error' in result:
            messages.error(request, f"Error ending A/B test: {result['error']}")
            return redirect('ml_engine:abtest_detail', test_id=test_id)
        
        messages.success(request, f"A/B test ended successfully")
        return redirect('ml_engine:abtest_list')
    
    # GET request - show confirmation form
    test_results = get_ab_test_results(test_id)
    
    if 'error' in test_results:
        messages.error(request, f"Error getting A/B test results: {test_results['error']}")
        return redirect('ml_engine:abtest_list')
    
    context = {
        'title': f"End A/B Test - {test_results['test_name']}",
        'test': test_results
    }
    
    return render(request, 'ml_engine/abtest_end.html', context)