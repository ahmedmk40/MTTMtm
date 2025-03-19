"""
Prediction service for the ML Engine.

This service is responsible for making fraud predictions using ML models.
"""

import time
import logging
import pickle
import os
import numpy as np
from typing import Dict, Any
from django.conf import settings
from django.utils import timezone
from ..models import MLModel, MLPrediction
from .feature_service import extract_features, transform_features
from .explainability_service import generate_shap_explanation, explain_response_code_prediction

logger = logging.getLogger(__name__)


def get_fraud_prediction(transaction) -> Dict[str, Any]:
    """
    Get fraud prediction for a transaction.
    
    Args:
        transaction: The transaction object
        
    Returns:
        Dictionary with the prediction result
    """
    start_time = time.time()
    
    # Initialize result
    result = {
        'risk_score': 0.0,
        'is_fraudulent': False,
        'execution_time': 0.0,
        'model_name': None,
        'model_version': None,
        'explanation': {},
        'models_used': [],
        'model_scores': {}
    }
    
    try:
        # Extract features
        raw_features = extract_features(transaction)
        
        # Transform features
        transformed_features = transform_features(raw_features)
        
        # Get active models
        active_models = MLModel.objects.filter(is_active=True)
        
        if not active_models.exists():
            logger.warning(f"No active ML models found for transaction {transaction.transaction_id}")
            result['execution_time'] = (time.time() - start_time) * 1000
            return result
        
        # Initialize variables for ensemble prediction
        total_risk_score = 0.0
        model_weights = {
            'classification': 0.5,  # Base fraud classification
            'behavioral': 0.3,      # Behavioral analysis
            'network': 0.2,         # Network analysis
            'anomaly': 0.3,         # Anomaly detection
            'adaptive': 0.2         # Adaptive thresholds
        }
        used_model_types = set()
        model_scores = {}
        
        # Process each active model
        for model in active_models:
            try:
                # Load the model
                model_path = os.path.join(settings.BASE_DIR, model.file_path)
                
                # Check if model file exists
                if not os.path.exists(model_path):
                    logger.error(f"Model file not found: {model_path}")
                    continue
                
                # Load the model from file
                with open(model_path, 'rb') as f:
                    ml_model = pickle.load(f)
                
                # Prepare features for prediction
                feature_vector = []
                for feature in ml_model.feature_names_in_:
                    feature_vector.append(transformed_features.get(feature, 0))
                
                # Make prediction
                prediction_start = time.time()
                
                # Different handling based on model type
                if model.model_type == 'anomaly' or model.model_type == 'behavioral':
                    # For anomaly detection models (like Isolation Forest)
                    # -1 for anomalies, 1 for normal observations
                    anomaly_score = ml_model.decision_function([feature_vector])[0]
                    # Convert to a 0-1 scale where 1 is anomalous
                    normalized_score = 1 - (anomaly_score + 1) / 2
                    risk_score = normalized_score * 100
                else:
                    # For classification models
                    prediction = ml_model.predict_proba([feature_vector])[0]
                    # Get fraud probability (assuming binary classification with fraud as class 1)
                    fraud_probability = prediction[1]
                    risk_score = fraud_probability * 100
                
                prediction_time = (time.time() - prediction_start) * 1000
                
                # Generate explanation using SHAP
                explanation = generate_shap_explanation(ml_model, transformed_features)
                
                # Save prediction to database
                MLPrediction.objects.create(
                    transaction_id=transaction.transaction_id,
                    model=model,
                    prediction=risk_score,
                    prediction_probability=risk_score / 100,  # Normalize back to 0-1
                    features=raw_features,
                    explanation=explanation,
                    execution_time=prediction_time
                )
                
                # Add to ensemble prediction
                model_weight = model_weights.get(model.model_type, 0.2)  # Default weight if type not specified
                total_risk_score += risk_score * model_weight
                used_model_types.add(model.model_type)
                
                # Store individual model scores
                model_scores[model.name] = {
                    'risk_score': risk_score,
                    'model_type': model.model_type,
                    'weight': model_weight
                }
                
                # Add to models used
                result['models_used'].append({
                    'name': model.name,
                    'version': model.version,
                    'type': model.model_type,
                    'risk_score': risk_score
                })
                
            except Exception as e:
                logger.error(f"Error using model {model.name} for transaction {transaction.transaction_id}: {str(e)}", 
                             exc_info=True)
        
        # Calculate final risk score (weighted average)
        if used_model_types:
            # Normalize by the sum of weights of used model types
            total_weight = sum(model_weights.get(model_type, 0.2) for model_type in used_model_types)
            final_risk_score = total_risk_score / total_weight if total_weight > 0 else 0
        else:
            final_risk_score = 0
        
        # Determine if fraudulent based on threshold
        is_fraudulent = final_risk_score >= 80  # Threshold can be adjusted
        
        # Update result
        result['risk_score'] = final_risk_score
        result['is_fraudulent'] = is_fraudulent
        result['model_scores'] = model_scores
        
        # Add response code specific explanation if available
        if hasattr(transaction, 'response_code') and transaction.response_code:
            result['response_code_explanation'] = explain_response_code_prediction(transaction, result)
        
        # Use the explanation from the highest-weighted model type
        if result['models_used']:
            primary_model = max(result['models_used'], key=lambda m: model_weights.get(m['type'], 0))
            result['model_name'] = primary_model['name']
            result['model_version'] = primary_model['version']
            
            # Get the explanation from the database
            try:
                primary_prediction = MLPrediction.objects.filter(
                    transaction_id=transaction.transaction_id,
                    model__name=primary_model['name']
                ).latest('created_at')
                result['explanation'] = primary_prediction.explanation
            except MLPrediction.DoesNotExist:
                pass
    
    except Exception as e:
        logger.error(f"Error making fraud prediction for transaction {transaction.transaction_id}: {str(e)}", exc_info=True)
    
    # Calculate total execution time
    result['execution_time'] = (time.time() - start_time) * 1000
    
    logger.info(
        f"ML prediction for transaction {transaction.transaction_id}: "
        f"risk_score={result['risk_score']:.2f}, "
        f"is_fraudulent={result['is_fraudulent']}, "
        f"models_used={len(result['models_used'])}, "
        f"execution_time={result['execution_time']:.2f}ms"
    )
    
    return result


def generate_explanation(model, features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate an explanation for a model prediction.
    
    Args:
        model: The ML model
        features: Dictionary of features
        
    Returns:
        Dictionary with the explanation
    """
    # This is a simplified explanation approach
    # In a real system, you'd use SHAP or LIME for proper explanations
    explanation = {
        'top_features': [],
        'feature_importance': {}
    }
    
    try:
        # Get feature importance from the model
        if hasattr(model, 'feature_importances_'):
            # For tree-based models
            importances = model.feature_importances_
            feature_names = model.feature_names_in_
            
            # Create a list of (feature, importance) tuples
            feature_importance = [(feature, importance) for feature, importance in zip(feature_names, importances)]
            
            # Sort by importance (descending)
            feature_importance.sort(key=lambda x: x[1], reverse=True)
            
            # Get top 5 features
            top_features = feature_importance[:5]
            
            # Add to explanation
            explanation['top_features'] = [
                {'name': feature, 'importance': float(importance), 'value': features.get(feature, 0)}
                for feature, importance in top_features
            ]
            
            # Add all feature importances
            explanation['feature_importance'] = {
                feature: float(importance)
                for feature, importance in feature_importance
            }
    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}", exc_info=True)
    
    return explanation