"""
Views for the ML Engine app.
"""

import json
import logging
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Avg, Max, Min, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import MLModel, MLPrediction, FeatureDefinition
from .services.model_service import train_model, save_model, activate_model
from .services.feature_service import extract_features, transform_features
from .services.prediction_service import get_fraud_prediction
from .services.monitoring_service import get_model_performance_metrics, get_model_drift_metrics, get_feature_distribution
from .services.explainability_service import generate_prediction_explanation, generate_feature_importance_plot
from .services.versioning_service import setup_ab_test, get_ab_test_results, end_ab_test

# Import monitoring views
from .views_monitoring import (
    monitoring_dashboard,
    model_drift,
    feature_distribution,
    prediction_explainability,
    abtest_list,
    abtest_create,
    abtest_detail,
    abtest_end
)

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    """
    ML Engine dashboard.
    """
    # Get model statistics
    model_stats = {
        'total': MLModel.objects.count(),
        'active': MLModel.objects.filter(is_active=True).count(),
        'by_type': MLModel.objects.values('model_type').annotate(count=Count('id')),
    }
    
    # Get prediction statistics
    prediction_stats = {
        'total': MLPrediction.objects.count(),
        'avg_risk_score': MLPrediction.objects.aggregate(avg=Avg('prediction'))['avg'] or 0,
        'high_risk': MLPrediction.objects.filter(prediction__gte=80).count(),
        'medium_risk': MLPrediction.objects.filter(prediction__gte=50, prediction__lt=80).count(),
        'low_risk': MLPrediction.objects.filter(prediction__lt=50).count(),
    }
    
    # Get recent predictions
    recent_predictions = MLPrediction.objects.select_related('model').order_by('-created_at')[:10]
    
    # Get active models
    active_models = MLModel.objects.filter(is_active=True)
    
    # Get prediction trend data
    prediction_trend = MLPrediction.objects.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id'),
        avg_risk=Avg('prediction')
    ).order_by('-date')[:30]
    
    # Reverse for chronological order
    prediction_trend = list(prediction_trend)
    prediction_trend.reverse()
    
    context = {
        'model_stats': model_stats,
        'prediction_stats': prediction_stats,
        'recent_predictions': recent_predictions,
        'active_models': active_models,
        'prediction_trend': prediction_trend,
    }
    
    return render(request, 'ml_engine/dashboard.html', context)


@login_required
def model_list(request):
    """
    List all ML models.
    """
    # Get filter parameters
    model_type = request.GET.get('model_type', '')
    is_active = request.GET.get('is_active', '')
    
    # Start with all models
    models = MLModel.objects.all()
    
    # Apply filters
    if model_type:
        models = models.filter(model_type=model_type)
    
    if is_active:
        is_active_bool = is_active.lower() == 'true'
        models = models.filter(is_active=is_active_bool)
    
    # Order by most recent first
    models = models.order_by('-created_at')
    
    # Paginate the results
    paginator = Paginator(models, 10)  # 10 models per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'model_types': MLModel.MODEL_TYPE_CHOICES,
        'filter_model_type': model_type,
        'filter_is_active': is_active,
    }
    
    return render(request, 'ml_engine/model_list.html', context)


@login_required
@permission_required('ml_engine.add_mlmodel')
def model_create(request):
    """
    Create a new ML model.
    """
    if request.method == 'POST':
        # Extract form data
        name = request.POST.get('name')
        description = request.POST.get('description')
        model_type = request.POST.get('model_type')
        version = request.POST.get('version')
        
        # Get training parameters
        training_params = {}
        for key, value in request.POST.items():
            if key.startswith('param_'):
                param_name = key.replace('param_', '')
                training_params[param_name] = value
        
        # Get training data file
        training_data_file = request.FILES.get('training_data')
        
        if not training_data_file:
            messages.error(request, "Training data file is required.")
            return redirect('ml_engine:model_create')
        
        try:
            # Read training data
            if training_data_file.name.endswith('.csv'):
                training_data = pd.read_csv(training_data_file)
            elif training_data_file.name.endswith(('.xls', '.xlsx')):
                training_data = pd.read_excel(training_data_file)
            else:
                messages.error(request, "Unsupported file format. Please upload a CSV or Excel file.")
                return redirect('ml_engine:model_create')
            
            # Get target column
            target_column = request.POST.get('target_column')
            if target_column not in training_data.columns:
                messages.error(request, f"Target column '{target_column}' not found in training data.")
                return redirect('ml_engine:model_create')
            
            # Train model
            model, metrics = train_model(model_type, training_data, target_column, training_params)
            
            # Save model
            ml_model = save_model(model, model_type, name, version, description, metrics, training_params)
            
            messages.success(request, f"Model '{name}' v{version} created successfully.")
            return redirect('ml_engine:model_detail', model_id=ml_model.id)
        
        except Exception as e:
            logger.error(f"Error creating model: {str(e)}", exc_info=True)
            messages.error(request, f"Error creating model: {str(e)}")
            return redirect('ml_engine:model_create')
    
    context = {
        'model_types': MLModel.MODEL_TYPE_CHOICES,
    }
    
    return render(request, 'ml_engine/model_create.html', context)


@login_required
def model_detail(request, model_id):
    """
    Display details of a specific ML model.
    """
    model = get_object_or_404(MLModel, id=model_id)
    
    # Get predictions using this model
    predictions = MLPrediction.objects.filter(model=model).order_by('-created_at')[:100]
    
    # Get prediction statistics
    prediction_stats = {
        'total': MLPrediction.objects.filter(model=model).count(),
        'avg_risk_score': MLPrediction.objects.filter(model=model).aggregate(avg=Avg('prediction'))['avg'] or 0,
        'high_risk': MLPrediction.objects.filter(model=model, prediction__gte=80).count(),
        'medium_risk': MLPrediction.objects.filter(model=model, prediction__gte=50, prediction__lt=80).count(),
        'low_risk': MLPrediction.objects.filter(model=model, prediction__lt=50).count(),
    }
    
    # Get feature importance
    feature_importance = model.feature_importance
    
    # Sort feature importance by value (descending)
    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    
    context = {
        'model': model,
        'predictions': predictions,
        'prediction_stats': prediction_stats,
        'feature_importance': sorted_features,
    }
    
    return render(request, 'ml_engine/model_detail.html', context)


@login_required
@permission_required('ml_engine.change_mlmodel')
def model_activate(request, model_id):
    """
    Activate an ML model.
    """
    model = get_object_or_404(MLModel, id=model_id)
    
    try:
        activate_model(model_id)
        messages.success(request, f"Model '{model.name}' v{model.version} activated successfully.")
    except Exception as e:
        logger.error(f"Error activating model: {str(e)}", exc_info=True)
        messages.error(request, f"Error activating model: {str(e)}")
    
    return redirect('ml_engine:model_detail', model_id=model_id)


@login_required
@permission_required('ml_engine.change_mlmodel')
def model_deactivate(request, model_id):
    """
    Deactivate an ML model.
    """
    model = get_object_or_404(MLModel, id=model_id)
    
    if not model.is_active:
        messages.warning(request, f"Model '{model.name}' v{model.version} is already inactive.")
        return redirect('ml_engine:model_detail', model_id=model_id)
    
    model.is_active = False
    model.save()
    
    messages.success(request, f"Model '{model.name}' v{model.version} deactivated successfully.")
    return redirect('ml_engine:model_detail', model_id=model_id)


@login_required
@permission_required('ml_engine.delete_mlmodel')
def model_delete(request, model_id):
    """
    Delete an ML model.
    """
    model = get_object_or_404(MLModel, id=model_id)
    
    if request.method == 'POST':
        model_name = model.name
        model_version = model.version
        
        model.delete()
        
        messages.success(request, f"Model '{model_name}' v{model_version} deleted successfully.")
        return redirect('ml_engine:model_list')
    
    context = {
        'model': model,
    }
    
    return render(request, 'ml_engine/model_delete.html', context)


@login_required
def prediction_list(request):
    """
    List all ML predictions.
    """
    # Get filter parameters
    model_id = request.GET.get('model_id', '')
    min_score = request.GET.get('min_score', '')
    max_score = request.GET.get('max_score', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Start with all predictions
    predictions = MLPrediction.objects.select_related('model')
    
    # Apply filters
    if model_id:
        predictions = predictions.filter(model_id=model_id)
    
    if min_score:
        predictions = predictions.filter(prediction__gte=float(min_score))
    
    if max_score:
        predictions = predictions.filter(prediction__lte=float(max_score))
    
    if start_date:
        predictions = predictions.filter(created_at__gte=start_date)
    
    if end_date:
        predictions = predictions.filter(created_at__lte=end_date)
    
    # Order by most recent first
    predictions = predictions.order_by('-created_at')
    
    # Paginate the results
    paginator = Paginator(predictions, 20)  # 20 predictions per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all models for the filter dropdown
    models = MLModel.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'models': models,
        'filter_model_id': model_id,
        'filter_min_score': min_score,
        'filter_max_score': max_score,
        'filter_start_date': start_date,
        'filter_end_date': end_date,
    }
    
    return render(request, 'ml_engine/prediction_list.html', context)


@login_required
def prediction_detail(request, prediction_id):
    """
    Display details of a specific ML prediction.
    """
    prediction = get_object_or_404(MLPrediction, id=prediction_id)
    
    context = {
        'prediction': prediction,
    }
    
    return render(request, 'ml_engine/prediction_detail.html', context)


@login_required
def feature_list(request):
    """
    List all feature definitions.
    """
    # Get filter parameters
    is_active = request.GET.get('is_active', '')
    
    # Start with all features
    features = FeatureDefinition.objects.all()
    
    # Apply filters
    if is_active:
        is_active_bool = is_active.lower() == 'true'
        features = features.filter(is_active=is_active_bool)
    
    # Order by name
    features = features.order_by('name')
    
    context = {
        'features': features,
        'filter_is_active': is_active,
    }
    
    return render(request, 'ml_engine/feature_list.html', context)


@login_required
@permission_required('ml_engine.add_featuredefinition')
def feature_create(request):
    """
    Create a new feature definition.
    """
    if request.method == 'POST':
        # Extract form data
        name = request.POST.get('name')
        description = request.POST.get('description')
        data_type = request.POST.get('data_type')
        source = request.POST.get('source')
        transformation = request.POST.get('transformation')
        is_active = request.POST.get('is_active') == 'on'
        
        # Create feature
        feature = FeatureDefinition.objects.create(
            name=name,
            description=description,
            data_type=data_type,
            source=source,
            transformation=transformation,
            is_active=is_active
        )
        
        messages.success(request, f"Feature '{name}' created successfully.")
        return redirect('ml_engine:feature_detail', feature_id=feature.id)
    
    context = {}
    
    return render(request, 'ml_engine/feature_create.html', context)


@login_required
def feature_detail(request, feature_id):
    """
    Display details of a specific feature definition.
    """
    feature = get_object_or_404(FeatureDefinition, id=feature_id)
    
    context = {
        'feature': feature,
    }
    
    return render(request, 'ml_engine/feature_detail.html', context)


@login_required
@permission_required('ml_engine.change_featuredefinition')
def feature_edit(request, feature_id):
    """
    Edit a feature definition.
    """
    feature = get_object_or_404(FeatureDefinition, id=feature_id)
    
    if request.method == 'POST':
        # Extract form data
        feature.name = request.POST.get('name')
        feature.description = request.POST.get('description')
        feature.data_type = request.POST.get('data_type')
        feature.source = request.POST.get('source')
        feature.transformation = request.POST.get('transformation')
        feature.is_active = request.POST.get('is_active') == 'on'
        
        # Save feature
        feature.save()
        
        messages.success(request, f"Feature '{feature.name}' updated successfully.")
        return redirect('ml_engine:feature_detail', feature_id=feature.id)
    
    context = {
        'feature': feature,
    }
    
    return render(request, 'ml_engine/feature_edit.html', context)


@login_required
@permission_required('ml_engine.delete_featuredefinition')
def feature_delete(request, feature_id):
    """
    Delete a feature definition.
    """
    feature = get_object_or_404(FeatureDefinition, id=feature_id)
    
    if request.method == 'POST':
        feature_name = feature.name
        
        feature.delete()
        
        messages.success(request, f"Feature '{feature_name}' deleted successfully.")
        return redirect('ml_engine:feature_list')
    
    context = {
        'feature': feature,
    }
    
    return render(request, 'ml_engine/feature_delete.html', context)


@login_required
def analytics(request):
    """
    ML analytics dashboard.
    """
    # Get model statistics
    model_stats = {
        'total': MLModel.objects.count(),
        'active': MLModel.objects.filter(is_active=True).count(),
        'by_type': MLModel.objects.values('model_type').annotate(count=Count('id')),
    }
    
    # Get prediction statistics
    prediction_stats = {
        'total': MLPrediction.objects.count(),
        'avg_risk_score': MLPrediction.objects.aggregate(avg=Avg('prediction'))['avg'] or 0,
        'high_risk': MLPrediction.objects.filter(prediction__gte=80).count(),
        'medium_risk': MLPrediction.objects.filter(prediction__gte=50, prediction__lt=80).count(),
        'low_risk': MLPrediction.objects.filter(prediction__lt=50).count(),
    }
    
    # Get prediction trend data
    prediction_trend = MLPrediction.objects.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id'),
        avg_risk=Avg('prediction')
    ).order_by('-date')[:30]
    
    # Reverse for chronological order
    prediction_trend = list(prediction_trend)
    prediction_trend.reverse()
    
    # Get model performance comparison
    model_performance = MLModel.objects.filter(
        accuracy__isnull=False
    ).values(
        'id', 'name', 'version', 'model_type', 'accuracy', 'precision', 'recall', 'f1_score', 'auc_roc'
    ).order_by('-created_at')
    
    context = {
        'model_stats': model_stats,
        'prediction_stats': prediction_stats,
        'prediction_trend': prediction_trend,
        'model_performance': model_performance,
    }
    
    return render(request, 'ml_engine/analytics.html', context)


@login_required
def model_performance(request):
    """
    Model performance comparison.
    """
    # Get filter parameters
    model_type = request.GET.get('model_type', '')
    
    # Get models with performance metrics
    models = MLModel.objects.filter(
        accuracy__isnull=False
    )
    
    # Apply filters
    if model_type:
        models = models.filter(model_type=model_type)
    
    # Order by created_at
    models = models.order_by('-created_at')
    
    context = {
        'models': models,
        'model_types': MLModel.MODEL_TYPE_CHOICES,
        'filter_model_type': model_type,
    }
    
    return render(request, 'ml_engine/model_performance.html', context)


@login_required
def feature_importance(request):
    """
    Feature importance analysis.
    """
    # Get filter parameters
    model_id = request.GET.get('model_id', '')
    
    # Get active models
    active_models = MLModel.objects.filter(is_active=True)
    
    # Get selected model
    selected_model = None
    if model_id:
        selected_model = get_object_or_404(MLModel, id=model_id)
    elif active_models.exists():
        selected_model = active_models.first()
    
    # Get feature importance
    feature_importance = {}
    if selected_model:
        feature_importance = selected_model.feature_importance
    
    # Sort feature importance by value (descending)
    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    
    context = {
        'active_models': active_models,
        'selected_model': selected_model,
        'feature_importance': sorted_features,
        'filter_model_id': model_id,
    }
    
    return render(request, 'ml_engine/feature_importance.html', context)


@login_required
def training_dashboard(request):
    """
    Training dashboard.
    """
    # Get active models
    active_models = MLModel.objects.filter(is_active=True)
    
    # Get all models
    all_models = MLModel.objects.all().order_by('-created_at')
    
    context = {
        'active_models': active_models,
        'all_models': all_models,
    }
    
    return render(request, 'ml_engine/training_dashboard.html', context)


@login_required
@permission_required('ml_engine.add_mlmodel')
def training_new(request):
    """
    Start a new training job.
    """
    # This is a simplified version - in a real system, you'd have a more complex
    # training workflow with job scheduling, progress tracking, etc.
    
    context = {
        'model_types': MLModel.MODEL_TYPE_CHOICES,
    }
    
    return render(request, 'ml_engine/training_new.html', context)


@login_required
def training_detail(request, training_id):
    """
    Display details of a specific training job.
    """
    # This is a placeholder - in a real system, you'd have a Training model
    # to track training jobs
    
    context = {}
    
    return render(request, 'ml_engine/training_detail.html', context)


@csrf_exempt
@require_POST
def api_predict(request):
    """
    API endpoint for making predictions.
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        transaction_data = data.get('transaction')
        
        if not transaction_data:
            return JsonResponse({'error': 'No transaction data provided'}, status=400)
        
        # Create a simple transaction object for prediction
        class SimpleTransaction:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        transaction = SimpleTransaction(**transaction_data)
        
        # Get prediction
        prediction = get_fraud_prediction(transaction)
        
        return JsonResponse(prediction)
    
    except Exception as e:
        logger.error(f"Error in API prediction: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


def api_models(request):
    """
    API endpoint for getting model information.
    """
    models = MLModel.objects.filter(is_active=True).values(
        'id', 'name', 'version', 'model_type', 'accuracy', 'precision', 'recall', 'f1_score'
    )
    
    return JsonResponse({'models': list(models)})


def api_features(request):
    """
    API endpoint for getting feature information.
    """
    features = FeatureDefinition.objects.filter(is_active=True).values(
        'id', 'name', 'description', 'data_type', 'source'
    )
    
    return JsonResponse({'features': list(features)})