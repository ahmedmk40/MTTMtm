"""
Serializers for the transactions app.
"""

from rest_framework import serializers
from .models import Transaction, POSTransaction, EcommerceTransaction, WalletTransaction


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for the Transaction model."""
    
    class Meta:
        model = Transaction
        fields = [
            'transaction_id',
            'transaction_type',
            'channel',
            'amount',
            'currency',
            'user_id',
            'merchant_id',
            'timestamp',
            'device_id',
            'location_data',
            'payment_method_data',
            'status',
            'risk_score',
            'is_flagged',
            'flag_reason',
            'metadata',
        ]
        read_only_fields = [
            'status',
            'risk_score',
            'is_flagged',
            'flag_reason',
        ]


class POSTransactionSerializer(serializers.ModelSerializer):
    """Serializer for the POSTransaction model."""
    
    class Meta:
        model = POSTransaction
        fields = [
            'transaction_id',
            'transaction_type',
            'channel',
            'amount',
            'currency',
            'user_id',
            'merchant_id',
            'timestamp',
            'device_id',
            'location_data',
            'payment_method_data',
            'terminal_id',
            'entry_mode',
            'terminal_type',
            'attendance',
            'condition',
            'mcc',
            'authorization_code',
            'recurring_payment',
            'status',
            'risk_score',
            'is_flagged',
            'flag_reason',
            'metadata',
        ]
        read_only_fields = [
            'status',
            'risk_score',
            'is_flagged',
            'flag_reason',
        ]


class EcommerceTransactionSerializer(serializers.ModelSerializer):
    """Serializer for the EcommerceTransaction model."""
    
    class Meta:
        model = EcommerceTransaction
        fields = [
            'transaction_id',
            'transaction_type',
            'channel',
            'amount',
            'currency',
            'user_id',
            'merchant_id',
            'timestamp',
            'device_id',
            'location_data',
            'payment_method_data',
            'website_url',
            'is_3ds_verified',
            'device_fingerprint',
            'shipping_address',
            'billing_address',
            'is_billing_shipping_match',
            'mcc',
            'authorization_code',
            'recurring_payment',
            'status',
            'risk_score',
            'is_flagged',
            'flag_reason',
            'metadata',
        ]
        read_only_fields = [
            'status',
            'risk_score',
            'is_flagged',
            'flag_reason',
        ]


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for the WalletTransaction model."""
    
    class Meta:
        model = WalletTransaction
        fields = [
            'transaction_id',
            'transaction_type',
            'channel',
            'amount',
            'currency',
            'user_id',
            'timestamp',
            'device_id',
            'location_data',
            'payment_method_data',
            'wallet_id',
            'source_type',
            'destination_type',
            'source_id',
            'destination_id',
            'transaction_purpose',
            'is_internal',
            'status',
            'risk_score',
            'is_flagged',
            'flag_reason',
            'metadata',
        ]
        read_only_fields = [
            'status',
            'risk_score',
            'is_flagged',
            'flag_reason',
        ]