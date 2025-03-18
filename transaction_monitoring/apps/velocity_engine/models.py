"""
Models for the Velocity Engine app.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
from apps.core.constants import (
    TIME_WINDOW_5_MIN,
    TIME_WINDOW_15_MIN,
    TIME_WINDOW_1_HOUR,
    TIME_WINDOW_6_HOURS,
    TIME_WINDOW_24_HOURS,
    TIME_WINDOW_7_DAYS,
    TIME_WINDOW_30_DAYS,
)


class VelocityRule(TimeStampedModel):
    """
    Model for velocity rules.
    """
    TIME_WINDOW_CHOICES = (
        (TIME_WINDOW_5_MIN, _('5 Minutes')),
        (TIME_WINDOW_15_MIN, _('15 Minutes')),
        (TIME_WINDOW_1_HOUR, _('1 Hour')),
        (TIME_WINDOW_6_HOURS, _('6 Hours')),
        (TIME_WINDOW_24_HOURS, _('24 Hours')),
        (TIME_WINDOW_7_DAYS, _('7 Days')),
        (TIME_WINDOW_30_DAYS, _('30 Days')),
    )
    
    ENTITY_TYPE_CHOICES = (
        ('user_id', _('User ID')),
        ('card_number', _('Card Number')),
        ('device_id', _('Device ID')),
        ('ip_address', _('IP Address')),
        ('merchant_id', _('Merchant ID')),
        ('email', _('Email')),
    )
    
    ACTION_CHOICES = (
        ('approve', _('Approve')),
        ('reject', _('Reject')),
        ('review', _('Flag for Review')),
        ('notify', _('Notify Only')),
    )
    
    name = models.CharField(_('Rule Name'), max_length=100)
    description = models.TextField(_('Description'))
    entity_type = models.CharField(_('Entity Type'), max_length=20, choices=ENTITY_TYPE_CHOICES)
    time_window = models.IntegerField(_('Time Window (seconds)'), choices=TIME_WINDOW_CHOICES)
    threshold = models.IntegerField(_('Threshold'))
    action = models.CharField(_('Action'), max_length=20, choices=ACTION_CHOICES)
    risk_score = models.DecimalField(_('Risk Score'), max_digits=5, decimal_places=2)
    is_active = models.BooleanField(_('Is Active'), default=True)
    
    # Channels this rule applies to
    applies_to_pos = models.BooleanField(_('Applies to POS'), default=True)
    applies_to_ecommerce = models.BooleanField(_('Applies to E-commerce'), default=True)
    applies_to_wallet = models.BooleanField(_('Applies to Wallet'), default=True)
    
    # Amount filters (optional)
    min_amount = models.DecimalField(_('Min Amount'), max_digits=15, decimal_places=2, null=True, blank=True)
    max_amount = models.DecimalField(_('Max Amount'), max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Performance metrics
    hit_count = models.IntegerField(_('Hit Count'), default=0)
    false_positive_count = models.IntegerField(_('False Positive Count'), default=0)
    last_triggered = models.DateTimeField(_('Last Triggered'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Velocity Rule')
        verbose_name_plural = _('Velocity Rules')
        ordering = ['entity_type', 'time_window']
        indexes = [
            models.Index(fields=['entity_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_entity_type_display()} - {self.get_time_window_display()})"


class VelocityCounter(TimeStampedModel):
    """
    Model for tracking transaction velocity.
    """
    entity_type = models.CharField(_('Entity Type'), max_length=20)
    entity_value = models.CharField(_('Entity Value'), max_length=255)
    count_5m = models.IntegerField(_('Count (5 min)'), default=0)
    count_15m = models.IntegerField(_('Count (15 min)'), default=0)
    count_1h = models.IntegerField(_('Count (1 hour)'), default=0)
    count_6h = models.IntegerField(_('Count (6 hours)'), default=0)
    count_24h = models.IntegerField(_('Count (24 hours)'), default=0)
    count_7d = models.IntegerField(_('Count (7 days)'), default=0)
    count_30d = models.IntegerField(_('Count (30 days)'), default=0)
    last_updated = models.DateTimeField(_('Last Updated'), auto_now=True)
    
    class Meta:
        verbose_name = _('Velocity Counter')
        verbose_name_plural = _('Velocity Counters')
        unique_together = ('entity_type', 'entity_value')
        indexes = [
            models.Index(fields=['entity_type', 'entity_value']),
            models.Index(fields=['last_updated']),
        ]
    
    def __str__(self):
        return f"{self.entity_type}: {self.entity_value}"


class VelocityAlert(TimeStampedModel):
    """
    Model for velocity rule alerts.
    """
    transaction_id = models.CharField(_('Transaction ID'), max_length=100)
    rule = models.ForeignKey(VelocityRule, on_delete=models.CASCADE, related_name='alerts')
    entity_type = models.CharField(_('Entity Type'), max_length=20)
    entity_value = models.CharField(_('Entity Value'), max_length=255)
    count = models.IntegerField(_('Count'))
    threshold = models.IntegerField(_('Threshold'))
    time_window = models.IntegerField(_('Time Window (seconds)'))
    
    class Meta:
        verbose_name = _('Velocity Alert')
        verbose_name_plural = _('Velocity Alerts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['entity_type', 'entity_value']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.rule.name} - {self.transaction_id} - {self.count}/{self.threshold}"