"""
Versioning service for ML models.

This service provides methods for model versioning and A/B testing.
"""

import logging
import os
import shutil
import pickle
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.db.models import Avg, Count, F, Q
from ..models import MLModel, MLPrediction

logger = logging.getLogger(__name__)


def create_model_version(model_name: str, 
                        model_type: str,
                        model_file_path: str,
                        description: str,
                        training_parameters: Dict[str, Any],
                        feature_importance: Dict[str, float],
                        performance_metrics: Dict[str, float],
                        is_active: bool = False) -> Tuple[MLModel, bool]:
    """
    Create a new version of a model.
    
    Args:
        model_name: Name of the model
        model_type: Type of the model
        model_file_path: Path to the model file
        description: Description of the model
        training_parameters: Dictionary of training parameters
        feature_importance: Dictionary of feature importance
        performance_metrics: Dictionary of performance metrics
        is_active: Whether the model should be active
        
    Returns:
        Tuple of (model, created)
    """
    try:
        # Get the latest version of the model
        latest_model = MLModel.objects.filter(name=model_name).order_by('-version').first()
        
        # Determine the new version
        if latest_model:
            # Parse the version string (assuming format like "1.0")
            try:
                major, minor = map(int, latest_model.version.split('.'))
                new_version = f"{major}.{minor + 1}"
            except ValueError:
                # If version parsing fails, just increment
                new_version = f"{latest_model.version}.1"
        else:
            new_version = "1.0"
        
        # If this is going to be active, deactivate other versions
        if is_active:
            with transaction.atomic():
                MLModel.objects.filter(name=model_name).update(is_active=False)
                
                # Create the new model version
                model = MLModel.objects.create(
                    name=model_name,
                    version=new_version,
                    model_type=model_type,
                    description=description,
                    file_path=model_file_path,
                    is_active=True,
                    training_parameters=training_parameters,
                    feature_importance=feature_importance,
                    accuracy=performance_metrics.get('accuracy'),
                    precision=performance_metrics.get('precision'),
                    recall=performance_metrics.get('recall'),
                    f1_score=performance_metrics.get('f1_score'),
                    auc_roc=performance_metrics.get('auc_roc'),
                    training_date=timezone.now(),
                    training_data_size=performance_metrics.get('training_data_size'),
                    deployed_at=timezone.now() if is_active else None,
                    deployed_by='system'
                )
        else:
            # Create the new model version without deactivating others
            model = MLModel.objects.create(
                name=model_name,
                version=new_version,
                model_type=model_type,
                description=description,
                file_path=model_file_path,
                is_active=is_active,
                training_parameters=training_parameters,
                feature_importance=feature_importance,
                accuracy=performance_metrics.get('accuracy'),
                precision=performance_metrics.get('precision'),
                recall=performance_metrics.get('recall'),
                f1_score=performance_metrics.get('f1_score'),
                auc_roc=performance_metrics.get('auc_roc'),
                training_date=timezone.now(),
                training_data_size=performance_metrics.get('training_data_size')
            )
        
        return model, True
    
    except Exception as e:
        logger.error(f"Error creating model version: {str(e)}", exc_info=True)
        return None, False


def activate_model_version(model_id: int) -> bool:
    """
    Activate a specific model version and deactivate others of the same name.
    
    Args:
        model_id: ID of the model to activate
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the model
        model = MLModel.objects.get(id=model_id)
        
        # Deactivate other versions of the same model
        with transaction.atomic():
            MLModel.objects.filter(name=model.name).exclude(id=model_id).update(is_active=False)
            
            # Activate this model
            model.is_active = True
            model.deployed_at = timezone.now()
            model.deployed_by = 'system'
            model.save()
        
        return True
    
    except MLModel.DoesNotExist:
        logger.error(f"Model with ID {model_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error activating model version: {str(e)}", exc_info=True)
        return False


def setup_ab_test(model_a_id: int, model_b_id: int, 
                 traffic_split: float = 0.5,
                 test_name: str = None) -> Dict[str, Any]:
    """
    Set up an A/B test between two model versions.
    
    Args:
        model_a_id: ID of model A
        model_b_id: ID of model B
        traffic_split: Fraction of traffic to send to model B (0-1)
        test_name: Optional name for the test
        
    Returns:
        Dictionary with test information
    """
    try:
        # Get the models
        model_a = MLModel.objects.get(id=model_a_id)
        model_b = MLModel.objects.get(id=model_b_id)
        
        # Ensure both models are active
        model_a.is_active = True
        model_b.is_active = True
        
        # Set up A/B test metadata
        test_id = f"ab_test_{int(timezone.now().timestamp())}"
        test_name = test_name or f"A/B Test: {model_a.name} v{model_a.version} vs {model_b.name} v{model_b.version}"
        
        # Store A/B test information in model metadata
        ab_test_info = {
            'test_id': test_id,
            'test_name': test_name,
            'start_date': timezone.now().isoformat(),
            'traffic_split': traffic_split,
            'is_active': True
        }
        
        # Update model A
        model_a.metadata = model_a.metadata or {}
        model_a.metadata['ab_test'] = {
            **ab_test_info,
            'is_control': True,
            'variant': 'A',
            'competing_model_id': model_b.id
        }
        model_a.save()
        
        # Update model B
        model_b.metadata = model_b.metadata or {}
        model_b.metadata['ab_test'] = {
            **ab_test_info,
            'is_control': False,
            'variant': 'B',
            'competing_model_id': model_a.id
        }
        model_b.save()
        
        return {
            'test_id': test_id,
            'test_name': test_name,
            'model_a': {
                'id': model_a.id,
                'name': model_a.name,
                'version': model_a.version
            },
            'model_b': {
                'id': model_b.id,
                'name': model_b.name,
                'version': model_b.version
            },
            'traffic_split': traffic_split,
            'start_date': timezone.now().isoformat(),
            'status': 'active'
        }
    
    except MLModel.DoesNotExist as e:
        logger.error(f"Model not found: {str(e)}")
        return {'error': str(e)}
    except Exception as e:
        logger.error(f"Error setting up A/B test: {str(e)}", exc_info=True)
        return {'error': str(e)}


def get_ab_test_results(test_id: str) -> Dict[str, Any]:
    """
    Get results of an A/B test.
    
    Args:
        test_id: ID of the A/B test
        
    Returns:
        Dictionary with test results
    """
    try:
        # Find models participating in the test
        models = MLModel.objects.filter(metadata__ab_test__test_id=test_id)
        
        if models.count() != 2:
            return {'error': f"A/B test with ID {test_id} not found or invalid"}
        
        # Get control and variant models
        control_model = next((m for m in models if m.metadata.get('ab_test', {}).get('is_control', False)), None)
        variant_model = next((m for m in models if not m.metadata.get('ab_test', {}).get('is_control', True)), None)
        
        if not control_model or not variant_model:
            return {'error': f"Could not determine control and variant models for test {test_id}"}
        
        # Get test metadata
        test_info = control_model.metadata.get('ab_test', {})
        start_date = datetime.fromisoformat(test_info.get('start_date', timezone.now().isoformat()))
        
        # Get predictions for both models
        control_predictions = MLPrediction.objects.filter(
            model=control_model,
            created_at__gte=start_date
        )
        
        variant_predictions = MLPrediction.objects.filter(
            model=variant_model,
            created_at__gte=start_date
        )
        
        # Calculate metrics
        control_metrics = {
            'prediction_count': control_predictions.count(),
            'avg_risk_score': control_predictions.aggregate(avg=Avg('prediction'))['avg'] or 0,
            'avg_execution_time': control_predictions.aggregate(avg=Avg('execution_time'))['avg'] or 0,
            'high_risk_count': control_predictions.filter(prediction__gte=80).count(),
            'medium_risk_count': control_predictions.filter(prediction__gte=50, prediction__lt=80).count(),
            'low_risk_count': control_predictions.filter(prediction__lt=50).count(),
        }
        
        variant_metrics = {
            'prediction_count': variant_predictions.count(),
            'avg_risk_score': variant_predictions.aggregate(avg=Avg('prediction'))['avg'] or 0,
            'avg_execution_time': variant_predictions.aggregate(avg=Avg('execution_time'))['avg'] or 0,
            'high_risk_count': variant_predictions.filter(prediction__gte=80).count(),
            'medium_risk_count': variant_predictions.filter(prediction__gte=50, prediction__lt=80).count(),
            'low_risk_count': variant_predictions.filter(prediction__lt=50).count(),
        }
        
        # Calculate differences
        differences = {
            'avg_risk_score_diff': variant_metrics['avg_risk_score'] - control_metrics['avg_risk_score'],
            'avg_execution_time_diff': variant_metrics['avg_execution_time'] - control_metrics['avg_execution_time'],
            'high_risk_ratio': (variant_metrics['high_risk_count'] / max(1, variant_metrics['prediction_count'])) / 
                              (control_metrics['high_risk_count'] / max(1, control_metrics['prediction_count'])),
        }
        
        # Determine winner (simplified)
        # In a real system, you'd use statistical significance tests
        if differences['avg_execution_time_diff'] < -5:  # Variant is at least 5ms faster
            winner = 'variant'
            winner_reason = 'Faster execution time'
        elif differences['high_risk_ratio'] > 1.1:  # Variant detects 10% more high-risk transactions
            winner = 'variant'
            winner_reason = 'Better at detecting high-risk transactions'
        elif differences['high_risk_ratio'] < 0.9:  # Control detects 10% more high-risk transactions
            winner = 'control'
            winner_reason = 'Better at detecting high-risk transactions'
        else:
            winner = 'tie'
            winner_reason = 'No significant difference'
        
        return {
            'test_id': test_id,
            'test_name': test_info.get('test_name', 'A/B Test'),
            'start_date': start_date.isoformat(),
            'duration_days': (timezone.now() - start_date).days,
            'traffic_split': test_info.get('traffic_split', 0.5),
            'control': {
                'id': control_model.id,
                'name': control_model.name,
                'version': control_model.version,
                'metrics': control_metrics
            },
            'variant': {
                'id': variant_model.id,
                'name': variant_model.name,
                'version': variant_model.version,
                'metrics': variant_metrics
            },
            'differences': differences,
            'winner': winner,
            'winner_reason': winner_reason,
            'status': test_info.get('is_active', False) and 'active' or 'completed'
        }
    
    except Exception as e:
        logger.error(f"Error getting A/B test results: {str(e)}", exc_info=True)
        return {'error': str(e)}


def end_ab_test(test_id: str, winner: str = None) -> Dict[str, Any]:
    """
    End an A/B test and optionally promote the winner.
    
    Args:
        test_id: ID of the A/B test
        winner: Optional winner to promote ('control', 'variant', or None)
        
    Returns:
        Dictionary with result information
    """
    try:
        # Find models participating in the test
        models = MLModel.objects.filter(metadata__ab_test__test_id=test_id)
        
        if models.count() != 2:
            return {'error': f"A/B test with ID {test_id} not found or invalid"}
        
        # Get control and variant models
        control_model = next((m for m in models if m.metadata.get('ab_test', {}).get('is_control', False)), None)
        variant_model = next((m for m in models if not m.metadata.get('ab_test', {}).get('is_control', True)), None)
        
        if not control_model or not variant_model:
            return {'error': f"Could not determine control and variant models for test {test_id}"}
        
        # Mark test as inactive
        for model in models:
            if 'ab_test' in model.metadata:
                model.metadata['ab_test']['is_active'] = False
                model.metadata['ab_test']['end_date'] = timezone.now().isoformat()
                model.save()
        
        # Promote winner if specified
        if winner == 'control':
            # Ensure control model is active, variant is inactive
            control_model.is_active = True
            variant_model.is_active = False
            control_model.save()
            variant_model.save()
            winner_model = control_model
        elif winner == 'variant':
            # Ensure variant model is active, control is inactive
            control_model.is_active = False
            variant_model.is_active = True
            control_model.save()
            variant_model.save()
            winner_model = variant_model
        else:
            # No winner specified, keep both active
            winner_model = None
        
        return {
            'test_id': test_id,
            'status': 'completed',
            'end_date': timezone.now().isoformat(),
            'winner': winner,
            'winner_model': winner_model and {
                'id': winner_model.id,
                'name': winner_model.name,
                'version': winner_model.version
            } or None
        }
    
    except Exception as e:
        logger.error(f"Error ending A/B test: {str(e)}", exc_info=True)
        return {'error': str(e)}