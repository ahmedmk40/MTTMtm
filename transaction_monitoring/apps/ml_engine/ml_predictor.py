"""
ML Predictor module for the ML Engine.

This module provides a high-level interface for making predictions using ML models.
"""

import logging
from typing import Dict, Any, Optional
from .services.prediction_service import get_fraud_prediction
from .models import MLModel

logger = logging.getLogger(__name__)


class MLPredictor:
    """
    ML Predictor class for making predictions using ML models.
    """
    
    def __init__(self):
        """Initialize the ML Predictor."""
        self.active_models = None
    
    def _load_active_models(self):
        """Load active ML models."""
        self.active_models = MLModel.objects.filter(is_active=True)
        return self.active_models.exists()
    
    def predict(self, transaction) -> Optional[Dict[str, Any]]:
        """
        Make a prediction for a transaction.
        
        Args:
            transaction: The transaction object
            
        Returns:
            Dictionary with prediction results or None if prediction fails
        """
        try:
            # Check if we have active models
            if not self.active_models:
                if not self._load_active_models():
                    logger.warning("No active ML models available for prediction")
                    return None
            
            # Get prediction from the prediction service
            prediction_result = get_fraud_prediction(transaction)
            
            # Return the prediction result
            return prediction_result
            
        except Exception as e:
            logger.error(f"Error in ML prediction for transaction {transaction.transaction_id}: {str(e)}", 
                         exc_info=True)
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about active ML models.
        
        Returns:
            Dictionary with model information
        """
        if not self.active_models:
            self._load_active_models()
        
        models_info = []
        for model in self.active_models:
            models_info.append({
                'id': model.id,
                'name': model.name,
                'version': model.version,
                'type': model.model_type,
                'accuracy': model.accuracy,
                'precision': model.precision,
                'recall': model.recall,
                'f1_score': model.f1_score,
                'auc_roc': model.auc_roc,
            })
        
        return {
            'active_models_count': len(models_info),
            'models': models_info
        }
    
    def get_feature_importance(self, model_id=None) -> Dict[str, Any]:
        """
        Get feature importance for a model.
        
        Args:
            model_id: Optional model ID. If None, uses the first active model.
            
        Returns:
            Dictionary with feature importance information
        """
        if not self.active_models:
            self._load_active_models()
        
        if model_id:
            try:
                model = MLModel.objects.get(id=model_id, is_active=True)
            except MLModel.DoesNotExist:
                logger.warning(f"Model with ID {model_id} not found or not active")
                return {'features': []}
        else:
            if not self.active_models.exists():
                logger.warning("No active ML models available")
                return {'features': []}
            model = self.active_models.first()
        
        # Get feature importance from the model
        feature_importance = model.feature_importance
        
        # Convert to list of dictionaries for easier consumption
        features = [
            {'name': feature, 'importance': importance}
            for feature, importance in feature_importance.items()
        ]
        
        # Sort by importance (descending)
        features.sort(key=lambda x: x['importance'], reverse=True)
        
        return {
            'model_name': model.name,
            'model_version': model.version,
            'features': features
        }