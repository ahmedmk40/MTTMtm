"""
Model management service for the ML Engine.

This service is responsible for managing ML models, including training,
evaluation, and deployment.
"""

import os
import logging
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from django.conf import settings
from django.utils import timezone
from ..models import MLModel

logger = logging.getLogger(__name__)


def train_model(model_type: str, training_data: pd.DataFrame, target_column: str,
                model_params: Dict[str, Any] = None) -> Tuple[Any, Dict[str, Any]]:
    """
    Train a new ML model.
    
    Args:
        model_type: Type of model to train (anomaly, classification, etc.)
        training_data: DataFrame with training data
        target_column: Name of the target column
        model_params: Dictionary of model parameters
        
    Returns:
        Tuple of (trained_model, metrics)
    """
    if model_params is None:
        model_params = {}
    
    # Split features and target
    X = training_data.drop(columns=[target_column])
    y = training_data[target_column]
    
    # Initialize metrics
    metrics = {
        'accuracy': None,
        'precision': None,
        'recall': None,
        'f1_score': None,
        'auc_roc': None,
        'training_data_size': len(training_data),
        'feature_importance': {},
    }
    
    # Train model based on type
    if model_type == 'anomaly':
        from sklearn.ensemble import IsolationForest
        
        # Set default parameters if not provided
        if 'n_estimators' not in model_params:
            model_params['n_estimators'] = 100
        if 'contamination' not in model_params:
            model_params['contamination'] = 'auto'
        
        # Train model
        model = IsolationForest(**model_params)
        model.fit(X)
        
        # No standard metrics for anomaly detection
    
    elif model_type == 'classification':
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
        
        # Set default parameters if not provided
        if 'n_estimators' not in model_params:
            model_params['n_estimators'] = 100
        if 'max_depth' not in model_params:
            model_params['max_depth'] = 10
        
        # Split data into train and test sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model
        model = RandomForestClassifier(**model_params)
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        metrics['accuracy'] = float(accuracy_score(y_test, y_pred))
        metrics['precision'] = float(precision_score(y_test, y_pred))
        metrics['recall'] = float(recall_score(y_test, y_pred))
        metrics['f1_score'] = float(f1_score(y_test, y_pred))
        metrics['auc_roc'] = float(roc_auc_score(y_test, y_prob))
        
        # Get feature importance
        feature_importance = {
            feature: float(importance)
            for feature, importance in zip(X.columns, model.feature_importances_)
        }
        metrics['feature_importance'] = feature_importance
    
    elif model_type == 'behavioral':
        # For simplicity, we'll use a RandomForestClassifier for behavioral analysis too
        # In a real system, you'd use more specialized models like LSTM or RNN
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
        
        # Set default parameters if not provided
        if 'n_estimators' not in model_params:
            model_params['n_estimators'] = 100
        if 'max_depth' not in model_params:
            model_params['max_depth'] = 10
        
        # Split data into train and test sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model
        model = RandomForestClassifier(**model_params)
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        metrics['accuracy'] = float(accuracy_score(y_test, y_pred))
        metrics['precision'] = float(precision_score(y_test, y_pred))
        metrics['recall'] = float(recall_score(y_test, y_pred))
        metrics['f1_score'] = float(f1_score(y_test, y_pred))
        metrics['auc_roc'] = float(roc_auc_score(y_test, y_prob))
        
        # Get feature importance
        feature_importance = {
            feature: float(importance)
            for feature, importance in zip(X.columns, model.feature_importances_)
        }
        metrics['feature_importance'] = feature_importance
    
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    
    return model, metrics


def save_model(model, model_type: str, name: str, version: str, description: str,
               metrics: Dict[str, Any], training_params: Dict[str, Any]) -> MLModel:
    """
    Save a trained ML model.
    
    Args:
        model: The trained model
        model_type: Type of model (anomaly, classification, etc.)
        name: Name of the model
        version: Version of the model
        description: Description of the model
        metrics: Dictionary of model metrics
        training_params: Dictionary of training parameters
        
    Returns:
        The created MLModel instance
    """
    # Create directory for models if it doesn't exist
    models_dir = os.path.join(settings.BASE_DIR, 'ml_models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Create file path
    file_name = f"{name.lower().replace(' ', '_')}_{version}.pkl"
    file_path = os.path.join('ml_models', file_name)
    full_path = os.path.join(settings.BASE_DIR, file_path)
    
    # Save model to file
    with open(full_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Create MLModel instance
    ml_model = MLModel.objects.create(
        name=name,
        description=description,
        model_type=model_type,
        version=version,
        file_path=file_path,
        is_active=False,  # Not active by default
        accuracy=metrics.get('accuracy'),
        precision=metrics.get('precision'),
        recall=metrics.get('recall'),
        f1_score=metrics.get('f1_score'),
        auc_roc=metrics.get('auc_roc'),
        training_date=timezone.now(),
        training_data_size=metrics.get('training_data_size'),
        training_parameters=training_params,
        feature_importance=metrics.get('feature_importance', {})
    )
    
    logger.info(f"Saved model {name} v{version} to {file_path}")
    
    return ml_model


def activate_model(model_id: int) -> MLModel:
    """
    Activate an ML model and deactivate others of the same type.
    
    Args:
        model_id: ID of the model to activate
        
    Returns:
        The activated MLModel instance
    """
    # Get the model to activate
    model = MLModel.objects.get(id=model_id)
    
    # Deactivate all models of the same type
    MLModel.objects.filter(model_type=model.model_type).update(is_active=False)
    
    # Activate the selected model
    model.is_active = True
    model.deployed_at = timezone.now()
    model.deployed_by = 'system'  # In a real system, this would be the current user
    model.save()
    
    logger.info(f"Activated model {model.name} v{model.version}")
    
    return model


def get_active_model(model_type: str) -> MLModel:
    """
    Get the active model of a specific type.
    
    Args:
        model_type: Type of model (anomaly, classification, etc.)
        
    Returns:
        The active MLModel instance or None if not found
    """
    try:
        return MLModel.objects.get(model_type=model_type, is_active=True)
    except MLModel.DoesNotExist:
        return None