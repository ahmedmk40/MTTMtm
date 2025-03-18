"""
Models for the ML Engine app.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel


class MLModel(TimeStampedModel):
    """
    Model for ML models.
    """
    MODEL_TYPE_CHOICES = (
        ('anomaly', _('Anomaly Detection')),
        ('classification', _('Classification')),
        ('behavioral', _('Behavioral Analysis')),
        ('network', _('Network Analysis')),
        ('adaptive', _('Adaptive Threshold')),
    )
    
    name = models.CharField(_('Model Name'), max_length=100)
    description = models.TextField(_('Description'))
    model_type = models.CharField(_('Model Type'), max_length=20, choices=MODEL_TYPE_CHOICES)
    version = models.CharField(_('Version'), max_length=20)
    file_path = models.CharField(_('File Path'), max_length=255)
    is_active = models.BooleanField(_('Is Active'), default=False)
    
    # Performance metrics
    accuracy = models.FloatField(_('Accuracy'), null=True, blank=True)
    precision = models.FloatField(_('Precision'), null=True, blank=True)
    recall = models.FloatField(_('Recall'), null=True, blank=True)
    f1_score = models.FloatField(_('F1 Score'), null=True, blank=True)
    auc_roc = models.FloatField(_('AUC-ROC'), null=True, blank=True)
    
    # Training information
    training_date = models.DateTimeField(_('Training Date'), null=True, blank=True)
    training_data_size = models.IntegerField(_('Training Data Size'), null=True, blank=True)
    training_parameters = models.JSONField(_('Training Parameters'), default=dict)
    feature_importance = models.JSONField(_('Feature Importance'), default=dict)
    
    # Deployment information
    deployed_at = models.DateTimeField(_('Deployed At'), null=True, blank=True)
    deployed_by = models.CharField(_('Deployed By'), max_length=100, null=True, blank=True)
    
    # Additional metadata (for A/B testing, versioning, etc.)
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('ML Model')
        verbose_name_plural = _('ML Models')
        ordering = ['-version']
        unique_together = ('name', 'version')
        indexes = [
            models.Index(fields=['model_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} v{self.version}"


class MLPrediction(TimeStampedModel):
    """
    Model for ML predictions.
    """
    transaction_id = models.CharField(_('Transaction ID'), max_length=100)
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE, related_name='predictions')
    prediction = models.FloatField(_('Prediction'))
    prediction_probability = models.FloatField(_('Prediction Probability'), null=True, blank=True)
    features = models.JSONField(_('Features'), default=dict)
    explanation = models.JSONField(_('Explanation'), default=dict)
    execution_time = models.FloatField(_('Execution Time (ms)'))
    
    class Meta:
        verbose_name = _('ML Prediction')
        verbose_name_plural = _('ML Predictions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.model.name} - {self.transaction_id} - {self.prediction}"


class FeatureDefinition(TimeStampedModel):
    """
    Model for feature definitions.
    """
    name = models.CharField(_('Feature Name'), max_length=100)
    description = models.TextField(_('Description'))
    data_type = models.CharField(_('Data Type'), max_length=20)
    source = models.CharField(_('Source'), max_length=100)
    transformation = models.TextField(_('Transformation'), null=True, blank=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    
    class Meta:
        verbose_name = _('Feature Definition')
        verbose_name_plural = _('Feature Definitions')
        ordering = ['name']
    
    def __str__(self):
        return self.name