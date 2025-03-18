"""
Models for the Fraud Engine app.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel


class FraudDetectionResult(TimeStampedModel):
    """
    Model to store fraud detection results for transactions.
    """
    transaction_id = models.CharField(_('Transaction ID'), max_length=100, unique=True)
    risk_score = models.DecimalField(_('Risk Score'), max_digits=5, decimal_places=2)
    is_fraudulent = models.BooleanField(_('Is Fraudulent'), default=False)
    decision = models.CharField(
        _('Decision'),
        max_length=20,
        choices=(
            ('approve', _('Approve')),
            ('reject', _('Reject')),
            ('review', _('Review')),
        )
    )
    processing_time = models.FloatField(_('Processing Time (ms)'))
    
    # Results from different engines
    block_check_result = models.JSONField(_('Block Check Result'), default=dict)
    rule_engine_result = models.JSONField(_('Rule Engine Result'), default=dict)
    velocity_engine_result = models.JSONField(_('Velocity Engine Result'), default=dict)
    ml_engine_result = models.JSONField(_('ML Engine Result'), default=dict)
    aml_engine_result = models.JSONField(_('AML Engine Result'), default=dict)
    
    # Triggered rules
    triggered_rules = models.JSONField(_('Triggered Rules'), default=list)
    
    class Meta:
        verbose_name = _('Fraud Detection Result')
        verbose_name_plural = _('Fraud Detection Results')
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['is_fraudulent']),
            models.Index(fields=['decision']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - Score: {self.risk_score} - Decision: {self.decision}"


class BlockList(TimeStampedModel):
    """
    Model for storing blocked entities (users, cards, devices, etc.).
    """
    ENTITY_TYPE_CHOICES = (
        ('user_id', _('User ID')),
        ('card_number', _('Card Number')),
        ('device_id', _('Device ID')),
        ('ip_address', _('IP Address')),
        ('merchant_id', _('Merchant ID')),
        ('email', _('Email')),
    )
    
    entity_type = models.CharField(_('Entity Type'), max_length=20, choices=ENTITY_TYPE_CHOICES)
    entity_value = models.CharField(_('Entity Value'), max_length=255)
    reason = models.TextField(_('Reason'))
    is_active = models.BooleanField(_('Is Active'), default=True)
    expires_at = models.DateTimeField(_('Expires At'), null=True, blank=True)
    added_by = models.CharField(_('Added By'), max_length=100)
    
    class Meta:
        verbose_name = _('Block List Entry')
        verbose_name_plural = _('Block List Entries')
        unique_together = ('entity_type', 'entity_value')
        indexes = [
            models.Index(fields=['entity_type', 'entity_value']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.get_entity_type_display()}: {self.entity_value}"


class FraudCase(TimeStampedModel):
    """
    Model for tracking fraud cases.
    """
    CASE_STATUS_CHOICES = (
        ('open', _('Open')),
        ('investigating', _('Investigating')),
        ('resolved', _('Resolved')),
        ('closed', _('Closed')),
    )
    
    CASE_PRIORITY_CHOICES = (
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    )
    
    case_id = models.CharField(_('Case ID'), max_length=50, unique=True)
    user_id = models.CharField(_('User ID'), max_length=100)
    title = models.CharField(_('Title'), max_length=255)
    description = models.TextField(_('Description'))
    status = models.CharField(_('Status'), max_length=20, choices=CASE_STATUS_CHOICES, default='open')
    priority = models.CharField(_('Priority'), max_length=20, choices=CASE_PRIORITY_CHOICES, default='medium')
    assigned_to = models.CharField(_('Assigned To'), max_length=100, null=True, blank=True)
    related_transactions = models.JSONField(_('Related Transactions'), default=list)
    resolution_notes = models.TextField(_('Resolution Notes'), null=True, blank=True)
    resolved_at = models.DateTimeField(_('Resolved At'), null=True, blank=True)
    resolved_by = models.CharField(_('Resolved By'), max_length=100, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Fraud Case')
        verbose_name_plural = _('Fraud Cases')
        indexes = [
            models.Index(fields=['case_id']),
            models.Index(fields=['user_id']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['assigned_to']),
        ]
    
    def __str__(self):
        return f"{self.case_id} - {self.title} ({self.get_status_display()})"