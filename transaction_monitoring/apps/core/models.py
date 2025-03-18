"""
Core models for Transaction Monitoring and Fraud Detection System.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides created and modified timestamps.
    """
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    class Meta:
        abstract = True


class BaseTransaction(TimeStampedModel):
    """
    Abstract base model for all transaction types.
    """
    TRANSACTION_STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('flagged', _('Flagged for Review')),
    )
    
    transaction_id = models.CharField(_('Transaction ID'), max_length=100, unique=True)
    amount = models.DecimalField(_('Amount'), max_digits=15, decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3)
    user_id = models.CharField(_('User ID'), max_length=100)
    timestamp = models.DateTimeField(_('Transaction Timestamp'))
    status = models.CharField(
        _('Status'), 
        max_length=20, 
        choices=TRANSACTION_STATUS_CHOICES,
        default='pending'
    )
    risk_score = models.DecimalField(
        _('Risk Score'), 
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    class Meta:
        abstract = True
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.transaction_id} - {self.amount} {self.currency}"