"""
Models for the AML app.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel


class AMLRiskProfile(TimeStampedModel):
    """
    Model for AML risk profiles.
    """
    RISK_LEVEL_CHOICES = (
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    )
    
    user_id = models.CharField(_('User ID'), max_length=100, unique=True)
    risk_level = models.CharField(_('Risk Level'), max_length=20, choices=RISK_LEVEL_CHOICES, default='low')
    risk_score = models.DecimalField(_('Risk Score'), max_digits=5, decimal_places=2, default=0.0)
    last_assessment = models.DateTimeField(_('Last Assessment'), auto_now=True)
    
    # Risk factors
    transaction_volume = models.DecimalField(_('Transaction Volume'), max_digits=15, decimal_places=2, default=0.0)
    transaction_count = models.IntegerField(_('Transaction Count'), default=0)
    high_risk_transactions = models.IntegerField(_('High Risk Transactions'), default=0)
    suspicious_patterns = models.IntegerField(_('Suspicious Patterns'), default=0)
    
    # Additional data
    notes = models.TextField(_('Notes'), blank=True)
    risk_factors = models.JSONField(_('Risk Factors'), default=list)
    
    class Meta:
        verbose_name = _('AML Risk Profile')
        verbose_name_plural = _('AML Risk Profiles')
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['last_assessment']),
        ]
    
    def __str__(self):
        return f"{self.user_id} - {self.get_risk_level_display()}"


class AMLAlert(TimeStampedModel):
    """
    Model for AML alerts.
    """
    ALERT_TYPE_CHOICES = (
        ('structuring', _('Structuring')),
        ('rapid_movement', _('Rapid Movement')),
        ('high_risk_jurisdiction', _('High Risk Jurisdiction')),
        ('round_amount', _('Round Amount')),
        ('multiple_transfers', _('Multiple Transfers')),
        ('circular_flow', _('Circular Flow')),
        ('party_connection', _('Party Connection')),
        ('round_amount_transactions', _('High Cumulative Round-Amount Transactions')),
        ('round_number_transfers', _('High Cumulative Round-Number Transfers')),
        ('identical_amount_transfers', _('Multiple Accounts Sending Identical Amounts')),
        ('multiple_transactions_between_accounts', _('Multiple Transactions Between Two Accounts')),
        ('other', _('Other')),
    )
    
    STATUS_CHOICES = (
        ('open', _('Open')),
        ('investigating', _('Investigating')),
        ('closed_false_positive', _('Closed - False Positive')),
        ('closed_sar_filed', _('Closed - SAR Filed')),
        ('closed_other', _('Closed - Other')),
    )
    
    alert_id = models.CharField(_('Alert ID'), max_length=50, unique=True)
    user_id = models.CharField(_('User ID'), max_length=100)
    alert_type = models.CharField(_('Alert Type'), max_length=50, choices=ALERT_TYPE_CHOICES)
    description = models.TextField(_('Description'))
    status = models.CharField(_('Status'), max_length=30, choices=STATUS_CHOICES, default='open')
    risk_score = models.DecimalField(_('Risk Score'), max_digits=5, decimal_places=2)
    
    # Related data
    related_transactions = models.JSONField(_('Related Transactions'), default=list)
    related_entities = models.JSONField(_('Related Entities'), default=list)
    detection_data = models.JSONField(_('Detection Data'), default=dict)
    
    # Case management
    assigned_to = models.CharField(_('Assigned To'), max_length=100, null=True, blank=True)
    investigation_notes = models.TextField(_('Investigation Notes'), blank=True)
    resolution_notes = models.TextField(_('Resolution Notes'), blank=True)
    closed_at = models.DateTimeField(_('Closed At'), null=True, blank=True)
    closed_by = models.CharField(_('Closed By'), max_length=100, null=True, blank=True)
    
    class Meta:
        verbose_name = _('AML Alert')
        verbose_name_plural = _('AML Alerts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_id']),
            models.Index(fields=['user_id']),
            models.Index(fields=['alert_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.alert_id} - {self.get_alert_type_display()} ({self.get_status_display()})"


class SuspiciousActivityReport(TimeStampedModel):
    """
    Model for Suspicious Activity Reports (SARs).
    """
    STATUS_CHOICES = (
        ('draft', _('Draft')),
        ('pending_approval', _('Pending Approval')),
        ('approved', _('Approved')),
        ('filed', _('Filed')),
        ('rejected', _('Rejected')),
    )
    
    sar_id = models.CharField(_('SAR ID'), max_length=50, unique=True)
    user_id = models.CharField(_('User ID'), max_length=100)
    title = models.CharField(_('Title'), max_length=255)
    description = models.TextField(_('Description'))
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Related data
    related_alerts = models.JSONField(_('Related Alerts'), default=list)
    related_transactions = models.JSONField(_('Related Transactions'), default=list)
    supporting_evidence = models.JSONField(_('Supporting Evidence'), default=list)
    
    # Filing information
    prepared_by = models.CharField(_('Prepared By'), max_length=100)
    approved_by = models.CharField(_('Approved By'), max_length=100, null=True, blank=True)
    filed_by = models.CharField(_('Filed By'), max_length=100, null=True, blank=True)
    filed_at = models.DateTimeField(_('Filed At'), null=True, blank=True)
    filing_reference = models.CharField(_('Filing Reference'), max_length=100, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Suspicious Activity Report')
        verbose_name_plural = _('Suspicious Activity Reports')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sar_id']),
            models.Index(fields=['user_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.sar_id} - {self.title} ({self.get_status_display()})"


class TransactionPattern(TimeStampedModel):
    """
    Model for tracking transaction patterns for AML monitoring.
    """
    PATTERN_TYPE_CHOICES = (
        ('structuring', _('Structuring')),
        ('round_amount', _('Round Amount')),
        ('rapid_movement', _('Rapid Movement')),
        ('circular_flow', _('Circular Flow')),
        ('cross_border', _('Cross Border')),
        ('high_risk_mcc', _('High Risk MCC')),
        ('round_amount_transactions', _('High Cumulative Round-Amount Transactions')),
        ('round_number_transfers', _('High Cumulative Round-Number Transfers')),
        ('identical_amount_transfers', _('Multiple Accounts Sending Identical Amounts')),
        ('multiple_transactions_between_accounts', _('Multiple Transactions Between Two Accounts')),
        ('other', _('Other')),
    )
    
    user_id = models.CharField(_('User ID'), max_length=100, null=True, blank=True)
    merchant_id = models.CharField(_('Merchant ID'), max_length=100, null=True, blank=True)
    related_user_id = models.CharField(_('Related User ID'), max_length=100, null=True, blank=True)
    pattern_type = models.CharField(_('Pattern Type'), max_length=50, choices=PATTERN_TYPE_CHOICES)
    pattern_data = models.JSONField(_('Pattern Data'), default=dict)
    first_detected = models.DateTimeField(_('First Detected'), auto_now_add=True)
    last_detected = models.DateTimeField(_('Last Detected'), auto_now=True)
    occurrence_count = models.IntegerField(_('Occurrence Count'), default=1)
    risk_score = models.DecimalField(_('Risk Score'), max_digits=5, decimal_places=2)
    is_suspicious = models.BooleanField(_('Is Suspicious'), default=False)
    
    # Additional fields for advanced patterns
    transaction_count = models.IntegerField(_('Transaction Count'), default=0)
    total_amount = models.DecimalField(_('Total Amount'), max_digits=15, decimal_places=2, default=0)
    time_window = models.CharField(_('Time Window'), max_length=50, null=True, blank=True)
    amount = models.DecimalField(_('Amount'), max_digits=15, decimal_places=2, null=True, blank=True)
    description = models.TextField(_('Description'), blank=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    metadata = models.JSONField(_('Metadata'), default=dict)
    
    class Meta:
        verbose_name = _('Transaction Pattern')
        verbose_name_plural = _('Transaction Patterns')
        ordering = ['-last_detected']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['merchant_id']),
            models.Index(fields=['pattern_type']),
            models.Index(fields=['is_suspicious']),
            models.Index(fields=['last_detected']),
        ]
    
    def __str__(self):
        entity_id = self.user_id or self.merchant_id or "Unknown"
        return f"{entity_id} - {self.get_pattern_type_display()} ({self.occurrence_count} occurrences)"