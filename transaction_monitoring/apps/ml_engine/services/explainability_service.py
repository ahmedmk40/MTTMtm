"""
Explainability service for ML models.

This service provides methods for generating explanations for ML model predictions.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
import matplotlib.pyplot as plt
import io
import base64
import pickle
import os
from django.conf import settings

logger = logging.getLogger(__name__)

# Try to import SHAP, but don't fail if it's not available
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("SHAP library not available. Install with 'pip install shap' for enhanced explainability.")


def generate_feature_importance_plot(feature_importance: Dict[str, float], 
                                     top_n: int = 10) -> Optional[str]:
    """
    Generate a feature importance plot.
    
    Args:
        feature_importance: Dictionary mapping feature names to importance values
        top_n: Number of top features to include in the plot
        
    Returns:
        Base64-encoded PNG image of the plot, or None if generation fails
    """
    try:
        # Sort features by importance
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        
        # Take top N features
        top_features = sorted_features[:top_n]
        
        # Extract feature names and importance values
        feature_names = [f[0] for f in top_features]
        importance_values = [f[1] for f in top_features]
        
        # Create plot
        plt.figure(figsize=(10, 6))
        bars = plt.barh(feature_names, importance_values, color='skyblue')
        
        # Add values to the bars
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 0.01, bar.get_y() + bar.get_height()/2, 
                     f'{width:.3f}', ha='left', va='center')
        
        plt.xlabel('Importance')
        plt.ylabel('Feature')
        plt.title(f'Top {top_n} Feature Importance')
        plt.tight_layout()
        
        # Save plot to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        
        # Encode the image to base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_str
    
    except Exception as e:
        logger.error(f"Error generating feature importance plot: {str(e)}", exc_info=True)
        return None


def generate_prediction_explanation(prediction_result: Dict[str, Any], 
                                    features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a comprehensive explanation for a prediction.
    
    Args:
        prediction_result: Dictionary with prediction results
        features: Dictionary of features used for the prediction
        
    Returns:
        Dictionary with explanation components
    """
    explanation = {
        'summary': '',
        'key_factors': [],
        'risk_factors': [],
        'protective_factors': [],
        'feature_importance_plot': None,
        'model_confidence': 0.0,
    }
    
    try:
        # Extract risk score and model information
        risk_score = prediction_result.get('risk_score', 0)
        model_name = prediction_result.get('model_name', 'Unknown')
        model_scores = prediction_result.get('model_scores', {})
        
        # Generate summary
        if risk_score >= 80:
            risk_level = "HIGH"
        elif risk_score >= 50:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        explanation['summary'] = (
            f"Transaction received a {risk_level} risk score of {risk_score:.2f}. "
            f"This assessment was primarily based on the {model_name} model."
        )
        
        # Add model confidence
        # For simplicity, we'll use a heuristic based on the risk score
        # In a real system, this would come from the model's confidence score
        if risk_score > 90 or risk_score < 10:
            confidence = 0.9  # High confidence for extreme scores
        elif 40 <= risk_score <= 60:
            confidence = 0.6  # Lower confidence for borderline cases
        else:
            confidence = 0.75  # Moderate confidence for other cases
            
        explanation['model_confidence'] = confidence
        
        # Extract top features from the prediction result
        top_features = prediction_result.get('explanation', {}).get('top_features', [])
        
        # Categorize features as risk or protective factors
        for feature in top_features:
            feature_name = feature.get('name', '')
            feature_importance = feature.get('importance', 0)
            feature_value = feature.get('value', features.get(feature_name, 'N/A'))
            
            factor = {
                'name': feature_name,
                'importance': feature_importance,
                'value': feature_value,
                'description': get_feature_description(feature_name, feature_value)
            }
            
            explanation['key_factors'].append(factor)
            
            # Categorize as risk or protective factor
            # This is a simplified approach - in a real system, you'd have more sophisticated logic
            if is_risk_factor(feature_name, feature_value):
                explanation['risk_factors'].append(factor)
            else:
                explanation['protective_factors'].append(factor)
        
        # Generate feature importance plot
        feature_importance = prediction_result.get('explanation', {}).get('feature_importance', {})
        if feature_importance:
            explanation['feature_importance_plot'] = generate_feature_importance_plot(feature_importance)
        
    except Exception as e:
        logger.error(f"Error generating prediction explanation: {str(e)}", exc_info=True)
        explanation['summary'] = "Could not generate explanation due to an error."
    
    return explanation


def get_feature_description(feature_name: str, feature_value: Any) -> str:
    """
    Get a human-readable description of a feature.
    
    Args:
        feature_name: Name of the feature
        feature_value: Value of the feature
        
    Returns:
        Human-readable description
    """
    # This is a simplified implementation
    # In a real system, you'd have a more comprehensive mapping of features to descriptions
    
    descriptions = {
        'amount': f"Transaction amount of {feature_value}",
        'is_new_card': "This is a new card that hasn't been used before" if feature_value else "Card has been used before",
        'is_high_risk_country': "Transaction is from a high-risk country" if feature_value else "Transaction is from a low-risk country",
        'is_night': "Transaction occurred during night hours" if feature_value else "Transaction occurred during day hours",
        'is_suspicious_mcc': "Merchant category is considered high-risk" if feature_value else "Merchant category is not high-risk",
        'user_weighted_degree': f"User has a network connection strength of {feature_value}",
        'merchant_weighted_degree': f"Merchant has a network connection strength of {feature_value}",
        'user_avg_transaction': f"User's average transaction amount is {feature_value}",
        'merchant_avg_transaction': f"Merchant's average transaction amount is {feature_value}",
        'tx_count_1min': f"{feature_value} transactions in the last minute",
        'tx_count_5min': f"{feature_value} transactions in the last 5 minutes",
        'tx_count_15min': f"{feature_value} transactions in the last 15 minutes",
        'tx_count_1hour': f"{feature_value} transactions in the last hour",
        'amount_1min': f"Total amount of {feature_value} in the last minute",
        'amount_5min': f"Total amount of {feature_value} in the last 5 minutes",
        'merchant_count_1hour': f"{feature_value} different merchants in the last hour",
        'location_count_1hour': f"{feature_value} different locations in the last hour",
        
        # Response code related features
        'response_code': get_response_code_description(feature_value),
        'high_risk_response_code_count': f"{feature_value} high-risk response codes in transaction history",
        'medium_risk_response_code_count': f"{feature_value} medium-risk response codes in transaction history",
        'approved_count': f"{feature_value} approved transactions in history",
        'declined_count': f"{feature_value} declined transactions in history",
        'declined_to_approved_ratio': f"Ratio of {feature_value:.2f} declined to approved transactions",
        'channel_switch_count': f"{feature_value} channel switches in transaction history",
        'response_code_risk_score': f"Risk score of {feature_value:.2f} based on response code patterns",
        'current_response_code_velocity_24h': f"{feature_value} occurrences of the current response code in last 24 hours",
    }
    
    # Handle response code features
    if feature_name.startswith('response_code_') and feature_name.endswith('_count'):
        code = feature_name.replace('response_code_', '').replace('_count', '')
        return f"{feature_value} occurrences of response code '{code}' ({get_response_code_description(code)})"
    
    # Handle previous response code features
    if feature_name.startswith('prev_response_code_'):
        position = feature_name.replace('prev_response_code_', '')
        return f"Response code {position} transaction(s) ago was '{feature_value}' ({get_response_code_description(feature_value)})"
    
    # Handle one-hot encoded features
    if feature_name.startswith('response_code_') and not feature_name.endswith('_count'):
        code = feature_name.replace('response_code_', '')
        return f"Response code is '{code}' ({get_response_code_description(code)})"
    
    return descriptions.get(feature_name, f"{feature_name}: {feature_value}")


def get_response_code_description(response_code: str) -> str:
    """
    Get a description for a response code.
    
    Args:
        response_code: The response code
        
    Returns:
        Description of the response code
    """
    from apps.core.constants import RESPONSE_CODE_DESCRIPTIONS
    
    description = RESPONSE_CODE_DESCRIPTIONS.get(response_code, 'Unknown')
    
    # Check if it's a high or medium risk code
    from apps.core.constants import HIGH_RISK_RESPONSE_CODES, MEDIUM_RISK_RESPONSE_CODES
    
    if response_code in HIGH_RISK_RESPONSE_CODES:
        return f"{description} (High Risk)"
    elif response_code in MEDIUM_RISK_RESPONSE_CODES:
        return f"{description} (Medium Risk)"
    elif response_code == '00':
        return f"{description} (Approved)"
    else:
        return description


def is_risk_factor(feature_name: str, feature_value: Any) -> bool:
    """
    Determine if a feature is a risk factor.
    
    Args:
        feature_name: Name of the feature
        feature_value: Value of the feature
        
    Returns:
        True if the feature is a risk factor, False otherwise
    """
    # This is a simplified implementation
    # In a real system, you'd have more sophisticated logic
    
    # Features that are risk factors when True/high
    risk_when_high = [
        'amount', 'is_new_card', 'is_high_risk_country', 'is_night', 'is_suspicious_mcc',
        'tx_count_1min', 'tx_count_5min', 'tx_count_15min', 'tx_count_1hour',
        'amount_1min', 'amount_5min', 'amount_15min', 'amount_1hour',
        'merchant_count_1hour', 'location_count_1hour', 'device_count_1hour',
        'ip_count_1hour', 'failed_tx_count_1hour',
        # Response code related features
        'high_risk_response_code_count', 'medium_risk_response_code_count',
        'declined_count', 'declined_to_approved_ratio', 'channel_switch_count',
        'response_code_risk_score', 'current_response_code_velocity_24h'
    ]
    
    # Features that are protective factors when True/high
    protective_when_high = [
        'user_age', 'account_age', 'transaction_history_length', 'approved_count'
    ]
    
    # Check for response code features
    if feature_name == 'response_code':
        from apps.core.constants import HIGH_RISK_RESPONSE_CODES, MEDIUM_RISK_RESPONSE_CODES
        return feature_value in HIGH_RISK_RESPONSE_CODES or feature_value in MEDIUM_RISK_RESPONSE_CODES
    
    # Check for response code count features
    if feature_name.startswith('response_code_') and feature_name.endswith('_count'):
        code = feature_name.replace('response_code_', '').replace('_count', '')
        from apps.core.constants import HIGH_RISK_RESPONSE_CODES, MEDIUM_RISK_RESPONSE_CODES
        is_risky_code = code in HIGH_RISK_RESPONSE_CODES or code in MEDIUM_RISK_RESPONSE_CODES
        return is_risky_code and feature_value > 0
    
    # Check for previous response code features
    if feature_name.startswith('prev_response_code_'):
        from apps.core.constants import HIGH_RISK_RESPONSE_CODES, MEDIUM_RISK_RESPONSE_CODES
        return feature_value in HIGH_RISK_RESPONSE_CODES or feature_value in MEDIUM_RISK_RESPONSE_CODES
    
    if feature_name in risk_when_high:
        # For boolean features
        if isinstance(feature_value, bool):
            return feature_value
        # For numeric features, consider high values as risk factors
        elif isinstance(feature_value, (int, float)):
            thresholds = {
                'amount': 1000,
                'tx_count_1min': 1,
                'tx_count_5min': 3,
                'tx_count_15min': 5,
                'tx_count_1hour': 10,
                'amount_1min': 200,
                'amount_5min': 500,
                'amount_15min': 1000,
                'amount_1hour': 2000,
                'merchant_count_1hour': 3,
                'location_count_1hour': 2,
                'device_count_1hour': 1,
                'ip_count_1hour': 1,
                'failed_tx_count_1hour': 1,
                # Response code related thresholds
                'high_risk_response_code_count': 1,
                'medium_risk_response_code_count': 2,
                'declined_count': 3,
                'declined_to_approved_ratio': 0.5,
                'channel_switch_count': 2,
                'response_code_risk_score': 50,
                'current_response_code_velocity_24h': 2
            }
            threshold = thresholds.get(feature_name, 0)
            return feature_value > threshold
    
    elif feature_name in protective_when_high:
        # For boolean features
        if isinstance(feature_value, bool):
            return not feature_value
        # For numeric features, consider low values as risk factors
        elif isinstance(feature_value, (int, float)):
            thresholds = {
                'user_age': 30,  # days
                'account_age': 90,  # days
                'transaction_history_length': 10,  # transactions
                'approved_count': 5  # approved transactions
            }
            threshold = thresholds.get(feature_name, 0)
            return feature_value < threshold
    
    # Default to not a risk factor
    return False


def generate_shap_explanation(model, features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate SHAP values to explain model predictions.
    
    Args:
        model: The ML model
        features: Dictionary of features
        
    Returns:
        Dictionary with explanation
    """
    if not SHAP_AVAILABLE:
        return generate_fallback_explanation(model, features)
    
    explanation = {
        'top_features': [],
        'feature_importance': {},
        'shap_values': None
    }
    
    try:
        # Convert features to DataFrame
        features_df = pd.DataFrame([features])
        
        # For pipeline models, we need to get the classifier
        if hasattr(model, 'named_steps') and 'classifier' in model.named_steps:
            classifier = model.named_steps['classifier']
            
            # Apply preprocessing
            if 'preprocessor' in model.named_steps:
                preprocessor = model.named_steps['preprocessor']
                X_processed = preprocessor.transform(features_df)
                
                # For tree-based models
                if hasattr(classifier, 'feature_importances_'):
                    explainer = shap.TreeExplainer(classifier)
                    shap_values = explainer.shap_values(X_processed)
                    
                    # For binary classification, shap_values is a list with two elements
                    if isinstance(shap_values, list) and len(shap_values) == 2:
                        shap_values = shap_values[1]  # Use values for class 1 (fraud)
                    
                    # Get feature names after preprocessing
                    if hasattr(preprocessor, 'get_feature_names_out'):
                        feature_names = preprocessor.get_feature_names_out()
                    else:
                        # Fallback to generic names
                        feature_names = [f'feature_{i}' for i in range(X_processed.shape[1])]
                    
                    # Create feature importance dictionary
                    for i, feature in enumerate(feature_names):
                        explanation['feature_importance'][feature] = float(np.abs(shap_values[0][i]))
                    
                    # Sort by importance and get top features
                    sorted_features = sorted(
                        explanation['feature_importance'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                    
                    # Get top 10 features
                    top_features = sorted_features[:10]
                    
                    # Add to explanation
                    explanation['top_features'] = [
                        {
                            'name': feature,
                            'importance': importance,
                            'value': features.get(feature.split('__')[-1] if '__' in feature else feature, 'N/A')
                        }
                        for feature, importance in top_features
                    ]
                    
                    # Store SHAP values
                    explanation['shap_values'] = shap_values[0].tolist()
        
        # For simple models (not pipelines)
        elif hasattr(model, 'feature_importances_'):
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(features_df)
            
            # For binary classification, shap_values is a list with two elements
            if isinstance(shap_values, list) and len(shap_values) == 2:
                shap_values = shap_values[1]  # Use values for class 1 (fraud)
            
            # Create feature importance dictionary
            for i, feature in enumerate(features_df.columns):
                explanation['feature_importance'][feature] = float(np.abs(shap_values[0][i]))
            
            # Sort by importance and get top features
            sorted_features = sorted(
                explanation['feature_importance'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Get top 10 features
            top_features = sorted_features[:10]
            
            # Add to explanation
            explanation['top_features'] = [
                {
                    'name': feature,
                    'importance': importance,
                    'value': features.get(feature, 'N/A')
                }
                for feature, importance in top_features
            ]
            
            # Store SHAP values
            explanation['shap_values'] = shap_values[0].tolist()
    
    except Exception as e:
        logger.error(f"Error generating SHAP explanation: {str(e)}", exc_info=True)
        explanation = generate_fallback_explanation(model, features)
    
    return explanation


def generate_fallback_explanation(model, features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a fallback explanation when SHAP is not available.
    
    Args:
        model: The ML model
        features: Dictionary of features
        
    Returns:
        Dictionary with explanation
    """
    explanation = {
        'top_features': [],
        'feature_importance': {}
    }
    
    try:
        # For pipeline models, we need to get the classifier
        if hasattr(model, 'named_steps') and 'classifier' in model.named_steps:
            classifier = model.named_steps['classifier']
            
            # For tree-based models
            if hasattr(classifier, 'feature_importances_'):
                # Get feature names
                if hasattr(model, 'feature_names_in_'):
                    feature_names = model.feature_names_in_
                elif hasattr(classifier, 'feature_names_in_'):
                    feature_names = classifier.feature_names_in_
                else:
                    # Convert features to DataFrame and use its columns
                    features_df = pd.DataFrame([features])
                    feature_names = features_df.columns
                
                # Create feature importance dictionary
                for feature, importance in zip(feature_names, classifier.feature_importances_):
                    explanation['feature_importance'][feature] = float(importance)
                
                # Sort by importance and get top features
                sorted_features = sorted(
                    explanation['feature_importance'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                # Get top 10 features
                top_features = sorted_features[:10]
                
                # Add to explanation
                explanation['top_features'] = [
                    {
                        'name': feature,
                        'importance': importance,
                        'value': features.get(feature, 'N/A')
                    }
                    for feature, importance in top_features
                ]
        
        # For simple models (not pipelines)
        elif hasattr(model, 'feature_importances_'):
            # Convert features to DataFrame
            features_df = pd.DataFrame([features])
            
            # Create feature importance dictionary
            for feature, importance in zip(features_df.columns, model.feature_importances_):
                explanation['feature_importance'][feature] = float(importance)
            
            # Sort by importance and get top features
            sorted_features = sorted(
                explanation['feature_importance'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Get top 10 features
            top_features = sorted_features[:10]
            
            # Add to explanation
            explanation['top_features'] = [
                {
                    'name': feature,
                    'importance': importance,
                    'value': features.get(feature, 'N/A')
                }
                for feature, importance in top_features
            ]
    
    except Exception as e:
        logger.error(f"Error generating fallback explanation: {str(e)}", exc_info=True)
        
        # Last resort fallback
        if 'response_code' in features:
            explanation['top_features'] = [
                {
                    'name': 'response_code',
                    'importance': 0.5,
                    'value': features.get('response_code', 'N/A')
                }
            ]
    
    return explanation


def explain_response_code_prediction(transaction, prediction_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate an explanation for a response code model prediction.
    
    Args:
        transaction: The transaction object
        prediction_result: The prediction result from the ML model
        
    Returns:
        Dictionary with explanation
    """
    explanation = {
        'risk_factors': [],
        'response_code_impact': {},
        'explanation_text': ''
    }
    
    try:
        # Get the response code
        response_code = transaction.response_code if hasattr(transaction, 'response_code') else None
        
        if not response_code:
            explanation['explanation_text'] = "No response code available for explanation."
            return explanation
        
        # Get response code description
        from apps.core.constants import RESPONSE_CODE_DESCRIPTIONS
        response_code_description = RESPONSE_CODE_DESCRIPTIONS.get(response_code, 'Unknown')
        
        # Check if response code is high risk
        from apps.core.constants import HIGH_RISK_RESPONSE_CODES, MEDIUM_RISK_RESPONSE_CODES
        is_high_risk = response_code in HIGH_RISK_RESPONSE_CODES
        is_medium_risk = response_code in MEDIUM_RISK_RESPONSE_CODES
        
        # Add response code as a risk factor
        risk_level = 'high' if is_high_risk else ('medium' if is_medium_risk else 'low')
        explanation['risk_factors'].append({
            'factor': 'response_code',
            'value': response_code,
            'description': response_code_description,
            'risk_level': risk_level,
            'impact': 'high' if is_high_risk else ('medium' if is_medium_risk else 'low')
        })
        
        # Add response code impact
        explanation['response_code_impact'] = {
            'code': response_code,
            'description': response_code_description,
            'risk_level': risk_level,
            'contribution_to_score': 'high' if is_high_risk else ('medium' if is_medium_risk else 'low')
        }
        
        # Get model explanation if available
        model_explanation = prediction_result.get('explanation', {})
        top_features = model_explanation.get('top_features', [])
        
        # Add top features as risk factors
        for feature in top_features:
            feature_name = feature.get('name', '')
            
            # Skip if already added
            if feature_name == 'response_code':
                continue
            
            # Determine risk level based on importance
            importance = feature.get('importance', 0)
            feature_risk_level = 'high' if importance > 0.3 else ('medium' if importance > 0.1 else 'low')
            
            # Add to risk factors
            explanation['risk_factors'].append({
                'factor': feature_name,
                'value': feature.get('value', 'N/A'),
                'description': get_feature_description(feature_name, feature.get('value', 'N/A')),
                'risk_level': feature_risk_level,
                'impact': feature_risk_level
            })
        
        # Generate explanation text
        risk_score = prediction_result.get('risk_score', 0)
        is_fraudulent = prediction_result.get('is_fraudulent', False)
        
        if is_fraudulent:
            explanation['explanation_text'] = (
                f"This transaction has been flagged as potentially fraudulent with a risk score of {risk_score:.2f}. "
                f"The primary risk factor is the response code '{response_code}' ({response_code_description}), "
                f"which is considered a {risk_level} risk indicator."
            )
        elif risk_score > 50:
            explanation['explanation_text'] = (
                f"This transaction has a moderate risk score of {risk_score:.2f}. "
                f"The response code '{response_code}' ({response_code_description}) "
                f"contributes to this elevated risk score."
            )
        else:
            explanation['explanation_text'] = (
                f"This transaction has a low risk score of {risk_score:.2f}. "
                f"The response code '{response_code}' ({response_code_description}) "
                f"does not indicate significant fraud risk."
            )
        
        # Add additional context based on other risk factors
        if len(explanation['risk_factors']) > 1:
            additional_factors = [
                f"{factor['factor']} ({factor['description']})"
                for factor in explanation['risk_factors'][1:3]  # Get next 2 factors
            ]
            
            if additional_factors:
                explanation['explanation_text'] += (
                    f" Additional risk factors include: {', '.join(additional_factors)}."
                )
    
    except Exception as e:
        logger.error(f"Error explaining response code prediction: {str(e)}", exc_info=True)
        explanation['explanation_text'] = "Unable to generate explanation due to an error."
    
    return explanation