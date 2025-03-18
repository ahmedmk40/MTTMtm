"""
Transaction models for the Transaction Monitoring and Fraud Detection System.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseTransaction
from apps.core.utils import hash_sensitive_data, mask_card_number


class Transaction(BaseTransaction):
    """
    Base model for all transaction types with common fields.
    """
    TRANSACTION_TYPE_CHOICES = (
        ('acquiring', _('Acquiring')),
        ('wallet', _('Wallet')),
    )
    
    CHANNEL_CHOICES = (
        ('pos', _('POS')),
        ('ecommerce', _('E-commerce')),
        ('wallet', _('Wallet')),
    )
    
    transaction_type = models.CharField(
        _('Transaction Type'), 
        max_length=20, 
        choices=TRANSACTION_TYPE_CHOICES
    )
    channel = models.CharField(
        _('Channel'), 
        max_length=20, 
        choices=CHANNEL_CHOICES
    )
    device_id = models.CharField(_('Device ID'), max_length=100, null=True, blank=True)
    merchant_id = models.CharField(_('Merchant ID'), max_length=100, null=True, blank=True)
    location_data = models.JSONField(_('Location Data'), default=dict)
    payment_method_data = models.JSONField(_('Payment Method Data'), default=dict)
    metadata = models.JSONField(_('Metadata'), default=dict)
    
    # Fraud detection fields
    is_flagged = models.BooleanField(_('Is Flagged'), default=False)
    flag_reason = models.CharField(_('Flag Reason'), max_length=255, null=True, blank=True)
    review_status = models.CharField(
        _('Review Status'),
        max_length=20,
        choices=(
            ('pending', _('Pending Review')),
            ('reviewed', _('Reviewed')),
            ('cleared', _('Cleared')),
            ('confirmed_fraud', _('Confirmed Fraud')),
        ),
        null=True,
        blank=True
    )
    reviewed_by = models.CharField(_('Reviewed By'), max_length=100, null=True, blank=True)
    reviewed_at = models.DateTimeField(_('Reviewed At'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['user_id']),
            models.Index(fields=['merchant_id']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['channel']),
            models.Index(fields=['status']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['is_flagged']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.amount} {self.currency} ({self.get_channel_display()})"
    
    def save(self, *args, **kwargs):
        """
        Override save method to process sensitive data before saving.
        """
        # Process payment method data to hash sensitive information
        if self.payment_method_data and isinstance(self.payment_method_data, dict):
            payment_method = self.payment_method_data.get('type')
            
            # Process card details
            if payment_method == 'credit_card' or payment_method == 'debit_card':
                card_details = self.payment_method_data.get('card_details', {})
                if card_details and isinstance(card_details, dict):
                    # Hash card number if present
                    if 'card_number' in card_details:
                        # Store masked version for display
                        card_details['masked_card_number'] = mask_card_number(card_details['card_number'])
                        # Hash the actual card number
                        card_details['card_number'] = hash_sensitive_data(card_details['card_number'])
                    
                    # Hash CVV if present
                    if 'cvv' in card_details:
                        card_details['cvv'] = hash_sensitive_data(card_details['cvv'])
                    
                    self.payment_method_data['card_details'] = card_details
        
        super().save(*args, **kwargs)


class POSTransaction(Transaction):
    """
    Model for Point of Sale transactions.
    """
    terminal_id = models.CharField(_('Terminal ID'), max_length=100)
    entry_mode = models.CharField(
        _('Entry Mode'),
        max_length=20,
        choices=(
            ('chip', _('Chip')),
            ('swipe', _('Swipe')),
            ('contactless', _('Contactless')),
            ('manual', _('Manual Entry')),
        )
    )
    terminal_type = models.CharField(_('Terminal Type'), max_length=50)
    attendance = models.CharField(
        _('Attendance'),
        max_length=20,
        choices=(
            ('attended', _('Attended')),
            ('unattended', _('Unattended')),
        )
    )
    condition = models.CharField(
        _('Condition'),
        max_length=20,
        choices=(
            ('card_present', _('Card Present')),
            ('card_not_present', _('Card Not Present')),
        )
    )
    mcc = models.CharField(_('MCC'), max_length=10, null=True, blank=True)
    authorization_code = models.CharField(_('Authorization Code'), max_length=50, null=True, blank=True)
    recurring_payment = models.BooleanField(_('Recurring Payment'), default=False)
    response_code = models.CharField(_('Response Code'), max_length=20, null=True, blank=True)
    processor_response_code = models.CharField(_('Processor Response Code'), max_length=20, null=True, blank=True)
    avs_result = models.CharField(_('AVS Result'), max_length=10, null=True, blank=True)
    cvv_result = models.CharField(_('CVV Result'), max_length=10, null=True, blank=True)
    response_time = models.FloatField(_('Response Time (ms)'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('POS Transaction')
        verbose_name_plural = _('POS Transactions')


class EcommerceTransaction(Transaction):
    """
    Model for E-commerce transactions.
    """
    website_url = models.URLField(_('Website URL'), null=True, blank=True)
    is_3ds_verified = models.BooleanField(_('3DS Verified'), default=False)
    device_fingerprint = models.CharField(_('Device Fingerprint'), max_length=255, null=True, blank=True)
    shipping_address = models.JSONField(_('Shipping Address'), default=dict)
    billing_address = models.JSONField(_('Billing Address'), default=dict)
    is_billing_shipping_match = models.BooleanField(_('Billing/Shipping Match'), default=True)
    mcc = models.CharField(_('MCC'), max_length=10, null=True, blank=True)
    authorization_code = models.CharField(_('Authorization Code'), max_length=50, null=True, blank=True)
    recurring_payment = models.BooleanField(_('Recurring Payment'), default=False)
    response_code = models.CharField(_('Response Code'), max_length=20, null=True, blank=True)
    processor_response_code = models.CharField(_('Processor Response Code'), max_length=20, null=True, blank=True)
    avs_result = models.CharField(_('AVS Result'), max_length=10, null=True, blank=True)
    cvv_result = models.CharField(_('CVV Result'), max_length=10, null=True, blank=True)
    response_time = models.FloatField(_('Response Time (ms)'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('E-commerce Transaction')
        verbose_name_plural = _('E-commerce Transactions')


class WalletTransaction(Transaction):
    """
    Model for Wallet transactions.
    """
    wallet_id = models.CharField(_('Wallet ID'), max_length=100)
    source_type = models.CharField(
        _('Source Type'),
        max_length=20,
        choices=(
            ('wallet', _('Wallet')),
            ('bank_account', _('Bank Account')),
            ('card', _('Card')),
            ('external', _('External')),
        )
    )
    destination_type = models.CharField(
        _('Destination Type'),
        max_length=20,
        choices=(
            ('wallet', _('Wallet')),
            ('bank_account', _('Bank Account')),
            ('card', _('Card')),
            ('external', _('External')),
        )
    )
    source_id = models.CharField(_('Source ID'), max_length=100)
    destination_id = models.CharField(_('Destination ID'), max_length=100)
    transaction_purpose = models.CharField(
        _('Transaction Purpose'),
        max_length=20,
        choices=(
            ('deposit', _('Deposit')),
            ('withdrawal', _('Withdrawal')),
            ('transfer', _('Transfer')),
            ('payment', _('Payment')),
            ('refund', _('Refund')),
        )
    )
    is_internal = models.BooleanField(_('Is Internal'), default=False)
    
    class Meta:
        verbose_name = _('Wallet Transaction')
        verbose_name_plural = _('Wallet Transactions')