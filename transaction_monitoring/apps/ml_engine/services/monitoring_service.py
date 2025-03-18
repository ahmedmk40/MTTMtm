"""
Monitoring service for ML models.

This service provides methods for monitoring ML model performance.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Max, Min, StdDev, F, Q, FloatField
from django.db.models.functions import TruncDay, TruncHour
from ..models import MLModel, MLPrediction

logger = logging.getLogger(__name__)


def get_model_performance_metrics(model_id: Optional[int] = None, 
                                 days: int = 30) -> Dict[str, Any]:
    """
    Get performance metrics for a model or all models.
    
    Args:
        model_id: Optional model ID. If None, metrics for all active models are returned.
        days: Number of days to include in the metrics
        
    Returns:
        Dictionary with performance metrics
    """
    try:
        # Set time range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Base query
        predictions = MLPrediction.objects.filter(created_at__gte=start_date)
        
        # Filter by model if specified
        if model_id is not None:
            predictions = predictions.filter(model_id=model_id)
        
        # Get basic metrics
        metrics = {
            'total_predictions': predictions.count(),
            'avg_risk_score': predictions.aggregate(avg=Avg('prediction'))['avg'] or 0,
            'avg_execution_time': predictions.aggregate(avg=Avg('execution_time'))['avg'] or 0,
            'high_risk_count': predictions.filter(prediction__gte=80).count(),
            'medium_risk_count': predictions.filter(prediction__gte=50, prediction__lt=80).count(),
            'low_risk_count': predictions.filter(prediction__lt=50).count(),
        }
        
        # Calculate risk score distribution
        risk_bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        risk_distribution = []
        
        for i in range(len(risk_bins) - 1):
            lower = risk_bins[i]
            upper = risk_bins[i + 1]
            count = predictions.filter(prediction__gte=lower, prediction__lt=upper).count()
            risk_distribution.append({
                'range': f"{lower}-{upper}",
                'count': count
            })
        
        # Add the last bin (90-100)
        count = predictions.filter(prediction__gte=risk_bins[-2], prediction__lte=risk_bins[-1]).count()
        risk_distribution.append({
            'range': f"{risk_bins[-2]}-{risk_bins[-1]}",
            'count': count
        })
        
        metrics['risk_distribution'] = risk_distribution
        
        # Get daily prediction counts and average risk scores
        daily_metrics = (
            predictions
            .annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(
                count=Count('id'),
                avg_risk_score=Avg('prediction'),
                avg_execution_time=Avg('execution_time')
            )
            .order_by('day')
        )
        
        metrics['daily_metrics'] = list(daily_metrics)
        
        # Get model-specific metrics if no specific model was requested
        if model_id is None:
            model_metrics = []
            for model in MLModel.objects.filter(is_active=True):
                model_predictions = predictions.filter(model=model)
                if model_predictions.exists():
                    model_metrics.append({
                        'id': model.id,
                        'name': model.name,
                        'version': model.version,
                        'type': model.model_type,
                        'prediction_count': model_predictions.count(),
                        'avg_risk_score': model_predictions.aggregate(avg=Avg('prediction'))['avg'] or 0,
                        'avg_execution_time': model_predictions.aggregate(avg=Avg('execution_time'))['avg'] or 0,
                    })
            
            metrics['model_metrics'] = model_metrics
        
        return metrics
    
    except Exception as e:
        logger.error(f"Error getting model performance metrics: {str(e)}", exc_info=True)
        return {
            'error': str(e),
            'total_predictions': 0,
            'avg_risk_score': 0,
            'avg_execution_time': 0,
            'high_risk_count': 0,
            'medium_risk_count': 0,
            'low_risk_count': 0,
            'risk_distribution': [],
            'daily_metrics': [],
            'model_metrics': []
        }


def get_model_drift_metrics(model_id: int, days: int = 30) -> Dict[str, Any]:
    """
    Get model drift metrics for a specific model.
    
    Args:
        model_id: Model ID
        days: Number of days to include in the metrics
        
    Returns:
        Dictionary with model drift metrics
    """
    try:
        # Set time range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get predictions for the model
        predictions = MLPrediction.objects.filter(
            model_id=model_id,
            created_at__gte=start_date
        )
        
        if not predictions.exists():
            return {
                'error': 'No predictions found for the specified model and time range',
                'drift_detected': False,
                'drift_metrics': {},
                'daily_metrics': []
            }
        
        # Calculate baseline metrics (first week)
        baseline_end = start_date + timedelta(days=7)
        baseline_predictions = predictions.filter(created_at__lt=baseline_end)
        
        if not baseline_predictions.exists():
            # If no baseline predictions, use the first 25% of predictions
            total_count = predictions.count()
            baseline_count = max(1, total_count // 4)
            baseline_predictions = predictions.order_by('created_at')[:baseline_count]
        
        baseline_avg_risk = baseline_predictions.aggregate(avg=Avg('prediction'))['avg'] or 0
        baseline_std_risk = baseline_predictions.aggregate(std=StdDev('prediction'))['std'] or 1
        
        # Calculate current metrics (last week)
        current_start = end_date - timedelta(days=7)
        current_predictions = predictions.filter(created_at__gte=current_start)
        
        if not current_predictions.exists():
            # If no current predictions, use the last 25% of predictions
            total_count = predictions.count()
            current_count = max(1, total_count // 4)
            current_predictions = predictions.order_by('-created_at')[:current_count]
        
        current_avg_risk = current_predictions.aggregate(avg=Avg('prediction'))['avg'] or 0
        current_std_risk = current_predictions.aggregate(std=StdDev('prediction'))['std'] or 1
        
        # Calculate drift metrics
        absolute_drift = abs(current_avg_risk - baseline_avg_risk)
        relative_drift = absolute_drift / max(0.1, baseline_avg_risk)  # Avoid division by zero
        
        # Calculate z-score
        z_score = absolute_drift / max(0.1, baseline_std_risk)  # Avoid division by zero
        
        # Determine if drift is significant
        drift_detected = z_score > 2.0 or relative_drift > 0.2
        
        # Get daily metrics for trend analysis
        daily_metrics = (
            predictions
            .annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(
                count=Count('id'),
                avg_risk_score=Avg('prediction'),
                std_risk_score=StdDev('prediction')
            )
            .order_by('day')
        )
        
        return {
            'drift_detected': drift_detected,
            'drift_metrics': {
                'baseline_avg_risk': baseline_avg_risk,
                'baseline_std_risk': baseline_std_risk,
                'current_avg_risk': current_avg_risk,
                'current_std_risk': current_std_risk,
                'absolute_drift': absolute_drift,
                'relative_drift': relative_drift,
                'z_score': z_score
            },
            'daily_metrics': list(daily_metrics)
        }
    
    except Exception as e:
        logger.error(f"Error getting model drift metrics: {str(e)}", exc_info=True)
        return {
            'error': str(e),
            'drift_detected': False,
            'drift_metrics': {},
            'daily_metrics': []
        }


def get_feature_distribution(model_id: int, feature_name: str, days: int = 30) -> Dict[str, Any]:
    """
    Get distribution of a feature for a specific model.
    
    Args:
        model_id: Model ID
        feature_name: Name of the feature
        days: Number of days to include in the metrics
        
    Returns:
        Dictionary with feature distribution
    """
    try:
        # Set time range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get predictions for the model
        predictions = MLPrediction.objects.filter(
            model_id=model_id,
            created_at__gte=start_date
        )
        
        if not predictions.exists():
            return {
                'error': 'No predictions found for the specified model and time range',
                'feature_name': feature_name,
                'distribution': []
            }
        
        # Extract feature values from the features JSON field
        feature_values = []
        for prediction in predictions:
            features = prediction.features
            if feature_name in features:
                value = features[feature_name]
                if isinstance(value, (int, float)):
                    feature_values.append(value)
        
        if not feature_values:
            return {
                'error': f'Feature {feature_name} not found in predictions',
                'feature_name': feature_name,
                'distribution': []
            }
        
        # Calculate distribution
        feature_values = np.array(feature_values)
        
        # For numeric features, calculate histogram
        hist, bin_edges = np.histogram(feature_values, bins=10)
        
        distribution = []
        for i in range(len(hist)):
            distribution.append({
                'range': f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}",
                'count': int(hist[i])
            })
        
        return {
            'feature_name': feature_name,
            'distribution': distribution,
            'statistics': {
                'min': float(np.min(feature_values)),
                'max': float(np.max(feature_values)),
                'mean': float(np.mean(feature_values)),
                'median': float(np.median(feature_values)),
                'std': float(np.std(feature_values))
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting feature distribution: {str(e)}", exc_info=True)
        return {
            'error': str(e),
            'feature_name': feature_name,
            'distribution': []
        }