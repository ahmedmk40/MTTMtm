"""
Models for the Rule Engine app.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel


class Rule(TimeStampedModel):
    """
    Model for fraud detection rules.
    """
    RULE_TYPE_CHOICES = (
        ('velocity', _('Velocity')),
        ('amount', _('Amount')),
        ('location', _('Location')),
        ('card', _('Card')),
        ('device', _('Device')),
        ('behavioral', _('Behavioral')),
        ('aml', _('AML')),
        ('custom', _('Custom')),
    )
    
    ACTION_CHOICES = (
        ('approve', _('Approve')),
        ('reject', _('Reject')),
        ('review', _('Flag for Review')),
        ('notify', _('Notify Only')),
    )
    
    name = models.CharField(_('Rule Name'), max_length=100)
    description = models.TextField(_('Description'))
    rule_type = models.CharField(_('Rule Type'), max_length=20, choices=RULE_TYPE_CHOICES)
    condition = models.TextField(_('Condition'))
    action = models.CharField(_('Action'), max_length=20, choices=ACTION_CHOICES)
    risk_score = models.DecimalField(_('Risk Score'), max_digits=5, decimal_places=2)
    is_active = models.BooleanField(_('Is Active'), default=True)
    priority = models.IntegerField(_('Priority'), default=0)
    version = models.IntegerField(_('Version'), default=1)
    created_by = models.CharField(_('Created By'), max_length=100)
    last_modified_by = models.CharField(_('Last Modified By'), max_length=100, null=True, blank=True)
    
    # Channels this rule applies to
    applies_to_pos = models.BooleanField(_('Applies to POS'), default=True)
    applies_to_ecommerce = models.BooleanField(_('Applies to E-commerce'), default=True)
    applies_to_wallet = models.BooleanField(_('Applies to Wallet'), default=True)
    
    # Merchant-specific application
    merchant_specific = models.BooleanField(_('Merchant Specific'), default=False, 
                                           help_text=_('If enabled, this rule will only apply to the specified merchants'))
    included_merchants = models.JSONField(_('Included Merchants'), default=list, blank=True,
                                         help_text=_('List of merchant IDs this rule applies to (if merchant_specific is True)'))
    excluded_merchants = models.JSONField(_('Excluded Merchants'), default=list, blank=True,
                                         help_text=_('List of merchant IDs this rule does NOT apply to'))
    
    # Performance metrics
    hit_count = models.IntegerField(_('Hit Count'), default=0)
    false_positive_count = models.IntegerField(_('False Positive Count'), default=0)
    last_triggered = models.DateTimeField(_('Last Triggered'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Rule')
        verbose_name_plural = _('Rules')
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['rule_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} (v{self.version})"


class RuleSet(TimeStampedModel):
    """
    Model for grouping rules into sets.
    """
    name = models.CharField(_('Rule Set Name'), max_length=100)
    description = models.TextField(_('Description'))
    rules = models.ManyToManyField(Rule, related_name='rule_sets')
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_by = models.CharField(_('Created By'), max_length=100)
    last_modified_by = models.CharField(_('Last Modified By'), max_length=100, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Rule Set')
        verbose_name_plural = _('Rule Sets')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class RuleExecution(TimeStampedModel):
    """
    Model for tracking rule executions.
    """
    transaction_id = models.CharField(_('Transaction ID'), max_length=100)
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name='executions')
    triggered = models.BooleanField(_('Triggered'), default=False)
    execution_time = models.FloatField(_('Execution Time (ms)'))
    condition_values = models.JSONField(_('Condition Values'), default=dict)
    
    class Meta:
        verbose_name = _('Rule Execution')
        verbose_name_plural = _('Rule Executions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['triggered']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.rule.name} - {self.transaction_id} - {'Triggered' if self.triggered else 'Not Triggered'}"