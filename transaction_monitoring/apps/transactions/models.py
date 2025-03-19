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
    # Enhanced transaction types for both acquiring and wallet transactions
    TRANSACTION_TYPE_CHOICES = (
        # Acquiring Transactions
        ('purchase', _('Purchase')),
        ('authorization', _('Authorization')),
        ('increment_auth', _('Increment Authorization')),
        ('pre_authorization', _('Pre-Authorization')),
        ('capture', _('Capture')),
        ('refund', _('Refund')),
        ('void', _('Void')),
        ('reversal', _('Reversal')),
        ('chargeback', _('Chargeback')),
        
        # Wallet Transactions
        ('deposit', _('Deposit')),
        ('withdrawal', _('Withdrawal')),
        ('wallet_purchase', _('Wallet Purchase')),
        ('transfer', _('Transfer')),
        ('wallet_topup', _('Wallet Top-Up')),
        ('wallet_to_wallet', _('Wallet-to-Wallet Transfer')),
        ('wallet_to_bank', _('Wallet-to-Bank Transfer')),
        ('wallet_to_card', _('Wallet-to-Card Transfer')),
        ('cashout', _('Cash-out')),
        ('bill_payment', _('Bill Payment')),
        ('wallet_refund', _('Wallet Refund')),
    )
    
    CHANNEL_CHOICES = (
        ('pos', _('POS')),
        ('ecommerce', _('E-commerce')),
        ('wallet', _('Wallet')),
        ('mobile_app', _('Mobile App')),
        ('api', _('API')),
        ('web', _('Web')),
        ('atm', _('ATM')),
        ('kiosk', _('Kiosk')),
    )
    
    # Acquiring Response Codes
    ACQUIRING_RESPONSE_CODES = {
        '00': _('Approved'),
        '01': _('Refer to Issuer'),
        '05': _('Do Not Honor'),
        '12': _('Invalid Transaction'),
        '14': _('Invalid Card Number'),
        '30': _('Format Error'),
        '41': _('Lost Card'),
        '43': _('Stolen Card'),
        '51': _('Insufficient Funds'),
        '54': _('Expired Card'),
        '55': _('Incorrect PIN'),
        '57': _('Transaction Not Permitted to Cardholder'),
        '58': _('Transaction Not Permitted to Terminal'),
        '61': _('Exceeds Withdrawal Limit'),
        '91': _('Issuer or Switch Inoperative'),
        '96': _('System Malfunction'),
    }
    
    # Wallet Response Codes
    WALLET_RESPONSE_CODES = {
        '00': _('Success'),
        '01': _('Insufficient Wallet Balance'),
        '03': _('Invalid Wallet Account'),
        '05': _('Unauthorized Transaction'),
        '12': _('Invalid Transaction'),
        '14': _('Invalid Account Number'),
        '30': _('Format Error'),
        '61': _('Exceeds Transaction Limit'),
        '65': _('Daily Limit Exceeded'),
        '91': _('Service Unavailable'),
        '92': _('Wallet Blocked'),
        '93': _('Duplicate Transaction'),
        '94': _('Wallet Account Not Found'),
    }
    
    # Transaction category for analytics and reporting
    TRANSACTION_CATEGORY_CHOICES = (
        ('retail', _('Retail')),
        ('travel', _('Travel')),
        ('entertainment', _('Entertainment')),
        ('dining', _('Dining')),
        ('utilities', _('Utilities')),
        ('healthcare', _('Healthcare')),
        ('education', _('Education')),
        ('financial', _('Financial Services')),
        ('government', _('Government')),
        ('other', _('Other')),
    )
    
    transaction_type = models.CharField(
        _('Transaction Type'), 
        max_length=30, 
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
    
    # New fields for enhanced categorization
    response_code = models.CharField(
        _('Response Code'), 
        max_length=10, 
        null=True, 
        blank=True,
        help_text=_('Transaction response code from the processor or wallet system')
    )
    transaction_category = models.CharField(
        _('Transaction Category'),
        max_length=30,
        choices=TRANSACTION_CATEGORY_CHOICES,
        default='other',
        help_text=_('Category of transaction for analytics purposes')
    )
    is_cross_border = models.BooleanField(
        _('Is Cross Border'),
        default=False,
        help_text=_('Whether the transaction crosses international borders')
    )
    is_high_risk_merchant = models.BooleanField(
        _('Is High Risk Merchant'),
        default=False,
        help_text=_('Whether the merchant is categorized as high risk')
    )
    is_high_risk_country = models.BooleanField(
        _('Is High Risk Country'),
        default=False,
        help_text=_('Whether the transaction involves a high risk country')
    )
    country_code = models.CharField(
        _('Country Code'),
        max_length=2,
        default='US',
        help_text=_('ISO 3166-1 alpha-2 country code')
    )
    
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
    
    def get_response_message(self):
        """Get the human-readable response message based on the transaction type and response code."""
        if not self.response_code:
            return None
            
        if self.transaction_type in ['deposit', 'withdrawal', 'wallet_purchase', 'transfer', 
                                    'wallet_topup', 'wallet_to_wallet', 'wallet_to_bank', 
                                    'wallet_to_card', 'cashout', 'bill_payment', 'wallet_refund']:
            return self.WALLET_RESPONSE_CODES.get(self.response_code, 'Unknown Response Code')
        else:
            return self.ACQUIRING_RESPONSE_CODES.get(self.response_code, 'Unknown Response Code')
    
    def is_wallet_transaction(self):
        """Check if this is a wallet-related transaction."""
        wallet_types = ['deposit', 'withdrawal', 'wallet_purchase', 'transfer', 
                       'wallet_topup', 'wallet_to_wallet', 'wallet_to_bank', 
                       'wallet_to_card', 'cashout', 'bill_payment', 'wallet_refund']
        return self.transaction_type in wallet_types
    
    def is_acquiring_transaction(self):
        """Check if this is an acquiring-related transaction."""
        acquiring_types = ['purchase', 'authorization', 'increment_auth', 'pre_authorization',
                          'capture', 'refund', 'void', 'reversal', 'chargeback']
        return self.transaction_type in acquiring_types
    
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
            models.Index(fields=['response_code']),
            models.Index(fields=['transaction_category']),
            models.Index(fields=['is_cross_border']),
            models.Index(fields=['is_high_risk_merchant']),
            models.Index(fields=['is_high_risk_country']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.get_transaction_type_display()} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        """
        Override save method to process sensitive data before saving and set additional flags.
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
        
        # Set high risk merchant flag based on merchant ID or MCC code
        if self.merchant_id:
            # This is a simplified example - in production, you would check against a database of high-risk merchants
            high_risk_merchant_ids = ['high_risk_merchant', 'merchant_123', 'merchant_456']
            high_risk_mccs = ['7995', '5933', '5944', '5945', '7273', '7994', '7995', '7996', '7997', '7998']
            
            self.is_high_risk_merchant = (
                self.merchant_id in high_risk_merchant_ids or
                (self.payment_method_data.get('mcc') in high_risk_mccs)
            )
        
        # Set cross-border flag based on location data
        if self.location_data and isinstance(self.location_data, dict):
            user_country = self.location_data.get('user_country')
            merchant_country = self.location_data.get('merchant_country')
            
            if user_country and merchant_country and user_country != merchant_country:
                self.is_cross_border = True
            
            # Set high risk country flag
            high_risk_countries = ['AF', 'BY', 'BI', 'CF', 'CD', 'CU', 'IR', 'IQ', 'LY', 'KP', 'SO', 'SS', 'SD', 'SY', 'VE', 'YE', 'ZW']
            self.is_high_risk_country = (
                (user_country in high_risk_countries) or 
                (merchant_country in high_risk_countries)
            )
        
        super().save(*args, **kwargs)
    
    def get_transaction_details(self):
        """
        Return a comprehensive dictionary of transaction details for analytics and reporting.
        """
        return {
            'id': self.transaction_id,
            'type': self.get_transaction_type_display(),
            'category': self.get_transaction_category_display(),
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.get_status_display(),
            'channel': self.get_channel_display(),
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'merchant_id': self.merchant_id,
            'response_code': self.response_code,
            'response_message': self.get_response_message(),
            'risk_score': float(self.risk_score) if self.risk_score else None,
            'is_flagged': self.is_flagged,
            'flag_reason': self.flag_reason,
            'is_cross_border': self.is_cross_border,
            'is_high_risk_merchant': self.is_high_risk_merchant,
            'is_high_risk_country': self.is_high_risk_country,
            'is_wallet_transaction': self.is_wallet_transaction(),
            'is_acquiring_transaction': self.is_acquiring_transaction(),
        }


class POSTransaction(Transaction):
    """
    Model for Point of Sale transactions.
    """
    ENTRY_MODE_CHOICES = (
        ('chip', _('Chip')),
        ('swipe', _('Swipe')),
        ('contactless', _('Contactless')),
        ('manual', _('Manual Entry')),
        ('fallback', _('Fallback')),
        ('keyed', _('Keyed')),
        ('nfc', _('NFC/Mobile Wallet')),
    )
    
    ATTENDANCE_CHOICES = (
        ('attended', _('Attended')),
        ('unattended', _('Unattended')),
        ('semi_attended', _('Semi-Attended')),
    )
    
    CONDITION_CHOICES = (
        ('card_present', _('Card Present')),
        ('card_not_present', _('Card Not Present')),
    )
    
    TERMINAL_TYPE_CHOICES = (
        ('traditional', _('Traditional POS')),
        ('mobile', _('Mobile POS')),
        ('integrated', _('Integrated POS')),
        ('smart', _('Smart Terminal')),
        ('self_service', _('Self-Service Kiosk')),
        ('vending', _('Vending Machine')),
        ('atm', _('ATM')),
    )
    
    terminal_id = models.CharField(_('Terminal ID'), max_length=100)
    entry_mode = models.CharField(
        _('Entry Mode'),
        max_length=20,
        choices=ENTRY_MODE_CHOICES
    )
    terminal_type = models.CharField(
        _('Terminal Type'), 
        max_length=50,
        choices=TERMINAL_TYPE_CHOICES
    )
    attendance = models.CharField(
        _('Attendance'),
        max_length=20,
        choices=ATTENDANCE_CHOICES
    )
    condition = models.CharField(
        _('Condition'),
        max_length=20,
        choices=CONDITION_CHOICES
    )
    mcc = models.CharField(_('MCC'), max_length=10, null=True, blank=True)
    authorization_code = models.CharField(_('Authorization Code'), max_length=50, null=True, blank=True)
    recurring_payment = models.BooleanField(_('Recurring Payment'), default=False)
    processor_response_code = models.CharField(_('Processor Response Code'), max_length=20, null=True, blank=True)
    avs_result = models.CharField(_('AVS Result'), max_length=10, null=True, blank=True)
    cvv_result = models.CharField(_('CVV Result'), max_length=10, null=True, blank=True)
    response_time = models.FloatField(_('Response Time (ms)'), null=True, blank=True)
    
    # New fields for enhanced POS transaction data
    batch_number = models.CharField(_('Batch Number'), max_length=50, null=True, blank=True)
    is_offline = models.BooleanField(_('Is Offline Transaction'), default=False)
    is_fallback = models.BooleanField(_('Is Fallback Transaction'), default=False)
    fallback_reason = models.CharField(_('Fallback Reason'), max_length=100, null=True, blank=True)
    is_partial_approval = models.BooleanField(_('Is Partial Approval'), default=False)
    requested_amount = models.DecimalField(
        _('Requested Amount'), 
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text=_('Original requested amount before partial approval')
    )
    
    class Meta:
        verbose_name = _('POS Transaction')
        verbose_name_plural = _('POS Transactions')
        
    def is_high_risk_entry_mode(self):
        """Check if the entry mode is considered high risk."""
        high_risk_modes = ['manual', 'fallback', 'keyed']
        return self.entry_mode in high_risk_modes


class EcommerceTransaction(Transaction):
    """
    Model for E-commerce transactions.
    """
    AUTHENTICATION_TYPE_CHOICES = (
        ('none', _('None')),
        ('3ds', _('3D Secure')),
        ('3ds2', _('3D Secure 2.0')),
        ('two_factor', _('Two-Factor')),
        ('biometric', _('Biometric')),
        ('other', _('Other')),
    )
    
    CHECKOUT_TYPE_CHOICES = (
        ('guest', _('Guest Checkout')),
        ('registered', _('Registered User')),
        ('one_click', _('One-Click Checkout')),
        ('saved_card', _('Saved Card')),
        ('digital_wallet', _('Digital Wallet')),
    )
    
    website_url = models.URLField(_('Website URL'), null=True, blank=True)
    authentication_type = models.CharField(
        _('Authentication Type'),
        max_length=20,
        choices=AUTHENTICATION_TYPE_CHOICES,
        default='none'
    )
    is_3ds_verified = models.BooleanField(_('3DS Verified'), default=False)
    device_fingerprint = models.CharField(_('Device Fingerprint'), max_length=255, null=True, blank=True)
    shipping_address = models.JSONField(_('Shipping Address'), default=dict)
    billing_address = models.JSONField(_('Billing Address'), default=dict)
    is_billing_shipping_match = models.BooleanField(_('Billing/Shipping Match'), default=True)
    mcc = models.CharField(_('MCC'), max_length=10, null=True, blank=True)
    authorization_code = models.CharField(_('Authorization Code'), max_length=50, null=True, blank=True)
    recurring_payment = models.BooleanField(_('Recurring Payment'), default=False)
    processor_response_code = models.CharField(_('Processor Response Code'), max_length=20, null=True, blank=True)
    avs_result = models.CharField(_('AVS Result'), max_length=10, null=True, blank=True)
    cvv_result = models.CharField(_('CVV Result'), max_length=10, null=True, blank=True)
    response_time = models.FloatField(_('Response Time (ms)'), null=True, blank=True)
    
    # New fields for enhanced e-commerce transaction data
    checkout_type = models.CharField(
        _('Checkout Type'),
        max_length=20,
        choices=CHECKOUT_TYPE_CHOICES,
        default='guest'
    )
    is_mobile_device = models.BooleanField(_('Is Mobile Device'), default=False)
    browser_info = models.JSONField(_('Browser Information'), default=dict)
    ip_address = models.CharField(_('IP Address'), max_length=45, null=True, blank=True)
    is_vpn_detected = models.BooleanField(_('VPN Detected'), default=False)
    is_proxy_detected = models.BooleanField(_('Proxy Detected'), default=False)
    is_new_customer = models.BooleanField(_('New Customer'), default=False)
    days_since_first_purchase = models.IntegerField(_('Days Since First Purchase'), null=True, blank=True)
    shipping_method = models.CharField(_('Shipping Method'), max_length=50, null=True, blank=True)
    delivery_timeframe = models.CharField(_('Delivery Timeframe'), max_length=50, null=True, blank=True)
    
    class Meta:
        verbose_name = _('E-commerce Transaction')
        verbose_name_plural = _('E-commerce Transactions')
        
    def get_risk_factors(self):
        """Return a list of risk factors for this e-commerce transaction."""
        risk_factors = []
        
        if not self.is_3ds_verified:
            risk_factors.append('No 3DS Verification')
            
        if not self.is_billing_shipping_match:
            risk_factors.append('Billing/Shipping Address Mismatch')
            
        if self.is_vpn_detected:
            risk_factors.append('VPN Detected')
            
        if self.is_proxy_detected:
            risk_factors.append('Proxy Detected')
            
        if self.is_new_customer:
            risk_factors.append('New Customer')
            
        if self.is_cross_border:
            risk_factors.append('Cross-Border Transaction')
            
        if self.avs_result and self.avs_result not in ['Y', 'X', 'A', 'W']:
            risk_factors.append('Failed AVS Check')
            
        if self.cvv_result and self.cvv_result != 'M':
            risk_factors.append('Failed CVV Check')
            
        return risk_factors


class WalletTransaction(Transaction):
    """
    Model for Wallet transactions.
    """
    SOURCE_TYPE_CHOICES = (
        ('wallet', _('Wallet')),
        ('bank_account', _('Bank Account')),
        ('card', _('Card')),
        ('cash', _('Cash')),
        ('crypto', _('Cryptocurrency')),
        ('mobile_money', _('Mobile Money')),
        ('payment_gateway', _('Payment Gateway')),
        ('external', _('External')),
    )
    
    DESTINATION_TYPE_CHOICES = (
        ('wallet', _('Wallet')),
        ('bank_account', _('Bank Account')),
        ('card', _('Card')),
        ('cash', _('Cash')),
        ('crypto', _('Cryptocurrency')),
        ('mobile_money', _('Mobile Money')),
        ('payment_gateway', _('Payment Gateway')),
        ('merchant', _('Merchant')),
        ('bill_payment', _('Bill Payment')),
        ('external', _('External')),
    )
    
    TRANSACTION_PURPOSE_CHOICES = (
        ('deposit', _('Deposit')),
        ('withdrawal', _('Withdrawal')),
        ('transfer', _('Transfer')),
        ('payment', _('Payment')),
        ('refund', _('Refund')),
        ('top_up', _('Top-Up')),
        ('bill_payment', _('Bill Payment')),
        ('merchant_payment', _('Merchant Payment')),
        ('p2p_transfer', _('Peer-to-Peer Transfer')),
        ('cash_out', _('Cash Out')),
        ('loan_repayment', _('Loan Repayment')),
        ('investment', _('Investment')),
        ('salary', _('Salary Payment')),
    )
    
    wallet_id = models.CharField(_('Wallet ID'), max_length=100)
    source_type = models.CharField(
        _('Source Type'),
        max_length=20,
        choices=SOURCE_TYPE_CHOICES
    )
    destination_type = models.CharField(
        _('Destination Type'),
        max_length=20,
        choices=DESTINATION_TYPE_CHOICES
    )
    source_id = models.CharField(_('Source ID'), max_length=100)
    destination_id = models.CharField(_('Destination ID'), max_length=100)
    transaction_purpose = models.CharField(
        _('Transaction Purpose'),
        max_length=20,
        choices=TRANSACTION_PURPOSE_CHOICES
    )
    is_internal = models.BooleanField(_('Is Internal'), default=False)
    
    # New fields for enhanced wallet transaction data
    wallet_balance_before = models.DecimalField(
        _('Wallet Balance Before'), 
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    wallet_balance_after = models.DecimalField(
        _('Wallet Balance After'), 
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    fee_amount = models.DecimalField(
        _('Fee Amount'), 
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    fee_type = models.CharField(
        _('Fee Type'),
        max_length=20,
        choices=(
            ('fixed', _('Fixed')),
            ('percentage', _('Percentage')),
            ('tiered', _('Tiered')),
            ('none', _('None')),
        ),
        default='none'
    )
    exchange_rate = models.DecimalField(
        _('Exchange Rate'), 
        max_digits=15, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text=_('Exchange rate for cross-currency transactions')
    )
    source_currency = models.CharField(_('Source Currency'), max_length=3, null=True, blank=True)
    destination_currency = models.CharField(_('Destination Currency'), max_length=3, null=True, blank=True)
    reference_id = models.CharField(_('Reference ID'), max_length=100, null=True, blank=True)
    is_scheduled = models.BooleanField(_('Is Scheduled Transaction'), default=False)
    scheduled_date = models.DateTimeField(_('Scheduled Date'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Wallet Transaction')
        verbose_name_plural = _('Wallet Transactions')
        
    def calculate_fee_percentage(self):
        """Calculate fee as a percentage of the transaction amount."""
        if self.fee_amount and self.amount and self.amount > 0:
            return (self.fee_amount / self.amount) * 100
        return None
        
    def is_cross_currency(self):
        """Check if this is a cross-currency transaction."""
        return (
            self.source_currency and 
            self.destination_currency and 
            self.source_currency != self.destination_currency
        )
        
    def get_transaction_velocity(self, hours=24):
        """
        Get the number of similar transactions in the last X hours.
        This is a placeholder - in a real implementation, this would query the database.
        """
        # This would be implemented with a database query in production
        return 0