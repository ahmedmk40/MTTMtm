"""
Forms for the transactions app.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import json
from .models import Transaction, POSTransaction, EcommerceTransaction, WalletTransaction


class TransactionCreateForm(forms.Form):
    """
    Form for creating new transactions.
    """
    # Common fields for all transaction types
    transaction_type = forms.ChoiceField(
        label=_('Transaction Type'),
        choices=Transaction.TRANSACTION_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    channel = forms.ChoiceField(
        label=_('Channel'),
        choices=Transaction.CHANNEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    response_code = forms.ChoiceField(
        label=_('Response Code'),
        choices=[('', '---')] + [(code, f"{code} - {desc}") for code, desc in Transaction.ACQUIRING_RESPONSE_CODES.items()],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_response_code'})
    )
    wallet_response_code = forms.ChoiceField(
        label=_('Wallet Response Code'),
        choices=[('', '---')] + [(code, f"{code} - {desc}") for code, desc in Transaction.WALLET_RESPONSE_CODES.items()],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_wallet_response_code'})
    )
    amount = forms.DecimalField(
        label=_('Amount'),
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    currency = forms.CharField(
        label=_('Currency'),
        max_length=3,
        initial='USD',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    user_id = forms.CharField(
        label=_('User ID'),
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    merchant_id = forms.CharField(
        label=_('Merchant ID'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    device_id = forms.CharField(
        label=_('Device ID'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Location data
    location_latitude = forms.DecimalField(
        label=_('Latitude'),
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'})
    )
    location_longitude = forms.DecimalField(
        label=_('Longitude'),
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'})
    )
    location_city = forms.CharField(
        label=_('City'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    location_country = forms.CharField(
        label=_('Country'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    location_postal_code = forms.CharField(
        label=_('Postal Code'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Payment method data
    payment_method_type = forms.ChoiceField(
        label=_('Payment Method Type'),
        choices=[
            ('credit_card', _('Credit Card')),
            ('debit_card', _('Debit Card')),
            ('wallet', _('Wallet')),
            ('bank_transfer', _('Bank Transfer')),
            ('cash', _('Cash')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    card_number = forms.CharField(
        label=_('Card Number'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    card_expiry = forms.CharField(
        label=_('Card Expiry (MM/YY)'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    card_cvv = forms.CharField(
        label=_('CVV'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    cardholder_name = forms.CharField(
        label=_('Cardholder Name'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # POS Transaction specific fields
    terminal_id = forms.CharField(
        label=_('Terminal ID'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    entry_mode = forms.ChoiceField(
        label=_('Entry Mode'),
        required=False,
        choices=[
            ('', '---'),
            ('chip', _('Chip')),
            ('swipe', _('Swipe')),
            ('contactless', _('Contactless')),
            ('manual', _('Manual Entry')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    terminal_type = forms.CharField(
        label=_('Terminal Type'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    attendance = forms.ChoiceField(
        label=_('Attendance'),
        required=False,
        choices=[
            ('', '---'),
            ('attended', _('Attended')),
            ('unattended', _('Unattended')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    condition = forms.ChoiceField(
        label=_('Condition'),
        required=False,
        choices=[
            ('', '---'),
            ('card_present', _('Card Present')),
            ('card_not_present', _('Card Not Present')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # E-commerce Transaction specific fields
    website_url = forms.URLField(
        label=_('Website URL'),
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )
    ip_address = forms.CharField(
        label=_('IP Address'),
        required=False,
        max_length=45,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    is_3ds_verified = forms.BooleanField(
        label=_('3DS Verified'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    device_fingerprint = forms.CharField(
        label=_('Device Fingerprint'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Shipping and billing address (for e-commerce)
    shipping_street = forms.CharField(
        label=_('Shipping Street'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    shipping_city = forms.CharField(
        label=_('Shipping City'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    shipping_state = forms.CharField(
        label=_('Shipping State'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    shipping_postal_code = forms.CharField(
        label=_('Shipping Postal Code'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    shipping_country = forms.CharField(
        label=_('Shipping Country'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    billing_same_as_shipping = forms.BooleanField(
        label=_('Billing same as shipping'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    billing_street = forms.CharField(
        label=_('Billing Street'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    billing_city = forms.CharField(
        label=_('Billing City'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    billing_state = forms.CharField(
        label=_('Billing State'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    billing_postal_code = forms.CharField(
        label=_('Billing Postal Code'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    billing_country = forms.CharField(
        label=_('Billing Country'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Wallet Transaction specific fields
    wallet_id = forms.CharField(
        label=_('Wallet ID'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    source_type = forms.ChoiceField(
        label=_('Source Type'),
        required=False,
        choices=[
            ('', '---'),
            ('wallet', _('Wallet')),
            ('bank_account', _('Bank Account')),
            ('card', _('Card')),
            ('external', _('External')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    destination_type = forms.ChoiceField(
        label=_('Destination Type'),
        required=False,
        choices=[
            ('', '---'),
            ('wallet', _('Wallet')),
            ('bank_account', _('Bank Account')),
            ('card', _('Card')),
            ('external', _('External')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    source_id = forms.CharField(
        label=_('Source ID'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    destination_id = forms.CharField(
        label=_('Destination ID'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    transaction_purpose = forms.ChoiceField(
        label=_('Transaction Purpose'),
        required=False,
        choices=[
            ('', '---'),
            ('deposit', _('Deposit')),
            ('withdrawal', _('Withdrawal')),
            ('transfer', _('Transfer')),
            ('payment', _('Payment')),
            ('refund', _('Refund')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_internal = forms.BooleanField(
        label=_('Is Internal'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Common fields for all transaction types
    metadata_notes = forms.CharField(
        label=_('Additional Notes (Metadata)'),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        channel = cleaned_data.get('channel')
        
        # Validate required fields based on channel
        if channel == 'pos':
            required_fields = ['terminal_id', 'entry_mode', 'terminal_type', 'attendance', 'condition']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, _('This field is required for POS transactions.'))
        
        elif channel == 'ecommerce':
            required_fields = ['website_url', 'ip_address']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, _('This field is required for E-commerce transactions.'))
            
            # Validate shipping address
            shipping_fields = ['shipping_street', 'shipping_city', 'shipping_country']
            for field in shipping_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, _('Shipping address is required for E-commerce transactions.'))
            
            # Validate billing address if not same as shipping
            if not cleaned_data.get('billing_same_as_shipping'):
                billing_fields = ['billing_street', 'billing_city', 'billing_country']
                for field in billing_fields:
                    if not cleaned_data.get(field):
                        self.add_error(field, _('Billing address is required when different from shipping.'))
        
        elif channel == 'wallet':
            required_fields = ['wallet_id', 'source_type', 'destination_type', 'source_id', 'destination_id', 'transaction_purpose']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, _('This field is required for Wallet transactions.'))
        
        # Validate payment method data
        payment_method_type = cleaned_data.get('payment_method_type')
        if payment_method_type in ['credit_card', 'debit_card']:
            card_fields = ['card_number', 'card_expiry', 'card_cvv', 'cardholder_name']
            for field in card_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, _('This field is required for card payments.'))
        
        return cleaned_data
    
    def get_transaction_data(self):
        """
        Convert form data to the format expected by the API.
        """
        data = self.cleaned_data
        channel = data.get('channel')
        
        # Common transaction data
        transaction_data = {
            'transaction_type': data.get('transaction_type'),
            'channel': channel,
            
            # Set the appropriate response code based on transaction type
            'response_code': data.get('wallet_response_code') if data.get('transaction_type') in [
                'deposit', 'withdrawal', 'wallet_purchase', 'transfer', 
                'wallet_topup', 'wallet_to_wallet', 'wallet_to_bank', 
                'wallet_to_card', 'cashout', 'bill_payment', 'wallet_refund'
            ] else data.get('response_code'),
            'amount': float(data.get('amount')),
            'currency': data.get('currency'),
            'user_id': data.get('user_id'),
            'timestamp': timezone.now().isoformat(),
            'merchant_id': data.get('merchant_id'),
            'device_id': data.get('device_id'),
        }
        
        # Location data
        location_data = {}
        if data.get('location_latitude') and data.get('location_longitude'):
            location_data['latitude'] = float(data.get('location_latitude'))
            location_data['longitude'] = float(data.get('location_longitude'))
        if data.get('location_city'):
            location_data['city'] = data.get('location_city')
        if data.get('location_country'):
            location_data['country'] = data.get('location_country')
        if data.get('location_postal_code'):
            location_data['postal_code'] = data.get('location_postal_code')
        
        transaction_data['location_data'] = location_data
        
        # Payment method data
        payment_method_data = {
            'type': data.get('payment_method_type')
        }
        
        if data.get('payment_method_type') in ['credit_card', 'debit_card']:
            payment_method_data['card_details'] = {
                'card_number': data.get('card_number'),
                'expiry_date': data.get('card_expiry'),
                'cvv': data.get('card_cvv'),
                'cardholder_name': data.get('cardholder_name')
            }
        
        transaction_data['payment_method_data'] = payment_method_data
        
        # Metadata
        metadata = {}
        if data.get('metadata_notes'):
            metadata['notes'] = data.get('metadata_notes')
        
        transaction_data['metadata'] = metadata
        
        # Channel-specific data
        if channel == 'pos':
            transaction_data.update({
                'terminal_id': data.get('terminal_id'),
                'entry_mode': data.get('entry_mode'),
                'terminal_type': data.get('terminal_type'),
                'attendance': data.get('attendance'),
                'condition': data.get('condition')
            })
        
        elif channel == 'ecommerce':
            transaction_data.update({
                'website_url': data.get('website_url'),
                'ip_address': data.get('ip_address'),
                'is_3ds_verified': data.get('is_3ds_verified', False),
                'device_fingerprint': data.get('device_fingerprint')
            })
            
            # Shipping address
            shipping_address = {
                'street': data.get('shipping_street'),
                'city': data.get('shipping_city'),
                'state': data.get('shipping_state'),
                'postal_code': data.get('shipping_postal_code'),
                'country': data.get('shipping_country')
            }
            transaction_data['shipping_address'] = shipping_address
            
            # Billing address
            if data.get('billing_same_as_shipping'):
                billing_address = shipping_address.copy()
            else:
                billing_address = {
                    'street': data.get('billing_street'),
                    'city': data.get('billing_city'),
                    'state': data.get('billing_state'),
                    'postal_code': data.get('billing_postal_code'),
                    'country': data.get('billing_country')
                }
            transaction_data['billing_address'] = billing_address
            transaction_data['is_billing_shipping_match'] = data.get('billing_same_as_shipping', True)
        
        elif channel == 'wallet':
            transaction_data.update({
                'wallet_id': data.get('wallet_id'),
                'source_type': data.get('source_type'),
                'destination_type': data.get('destination_type'),
                'source_id': data.get('source_id'),
                'destination_id': data.get('destination_id'),
                'transaction_purpose': data.get('transaction_purpose'),
                'is_internal': data.get('is_internal', False)
            })
        
        return transaction_data


class TransactionSearchForm(forms.Form):
    """
    Form for searching and filtering transactions.
    """
    transaction_id = forms.CharField(
        label=_('Transaction ID'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    user_id = forms.CharField(
        label=_('User ID'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    merchant_id = forms.CharField(
        label=_('Merchant ID'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    transaction_type = forms.ChoiceField(
        label=_('Transaction Type'),
        choices=[('', '---')] + list(Transaction.TRANSACTION_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    channel = forms.ChoiceField(
        label=_('Channel'),
        choices=[('', '---')] + list(Transaction.CHANNEL_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        label=_('Status'),
        choices=[('', '---')] + list(Transaction.TRANSACTION_STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_flagged = forms.NullBooleanField(
        label=_('Flagged'),
        required=False,
        widget=forms.Select(
            attrs={'class': 'form-select'},
            choices=[
                ('', '---'),
                ('true', _('Yes')),
                ('false', _('No')),
            ]
        )
    )
    min_amount = forms.DecimalField(
        label=_('Min Amount'),
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    max_amount = forms.DecimalField(
        label=_('Max Amount'),
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    start_date = forms.DateTimeField(
        label=_('Start Date'),
        required=False,
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'}
        )
    )
    end_date = forms.DateTimeField(
        label=_('End Date'),
        required=False,
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'}
        )
    )


class TransactionReviewForm(forms.Form):
    """
    Form for reviewing flagged transactions.
    """
    REVIEW_STATUS_CHOICES = (
        ('pending', _('Pending Review')),
        ('reviewed', _('Reviewed')),
        ('cleared', _('Cleared')),
        ('confirmed_fraud', _('Confirmed Fraud')),
    )
    
    review_status = forms.ChoiceField(
        label=_('Review Status'),
        choices=REVIEW_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        label=_('Review Notes'),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )