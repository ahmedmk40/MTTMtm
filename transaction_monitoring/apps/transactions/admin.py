"""
Admin configuration for the transactions app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Transaction, POSTransaction, EcommerceTransaction, WalletTransaction


class TransactionAdmin(admin.ModelAdmin):
    """Admin interface for the Transaction model."""
    
    list_display = (
        'transaction_id', 
        'transaction_type', 
        'channel', 
        'amount_with_currency', 
        'user_id', 
        'status', 
        'is_flagged', 
        'timestamp',
        'view_details'
    )
    list_filter = (
        'transaction_type', 
        'channel', 
        'status', 
        'is_flagged', 
        'currency',
        'review_status'
    )
    search_fields = (
        'transaction_id', 
        'user_id', 
        'merchant_id'
    )
    readonly_fields = (
        'transaction_id', 
        'created_at', 
        'updated_at'
    )
    fieldsets = (
        ('Transaction Information', {
            'fields': (
                'transaction_id', 
                'transaction_type', 
                'channel', 
                'amount', 
                'currency', 
                'status', 
                'timestamp'
            )
        }),
        ('User and Merchant', {
            'fields': (
                'user_id', 
                'merchant_id', 
                'device_id'
            )
        }),
        ('Location', {
            'fields': (
                'location_data',
            )
        }),
        ('Payment Method', {
            'fields': (
                'payment_method_data',
            )
        }),
        ('Fraud Detection', {
            'fields': (
                'is_flagged', 
                'flag_reason', 
                'risk_score', 
                'review_status', 
                'reviewed_by', 
                'reviewed_at'
            )
        }),
        ('Additional Information', {
            'fields': (
                'metadata', 
                'created_at', 
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def amount_with_currency(self, obj):
        """Display amount with currency."""
        return f"{obj.amount} {obj.currency}"
    amount_with_currency.short_description = 'Amount'
    
    def view_details(self, obj):
        """Link to view transaction details."""
        url = reverse('admin:transactions_transaction_change', args=[obj.pk])
        return format_html('<a href="{}">View Details</a>', url)
    view_details.short_description = 'Details'


class POSTransactionAdmin(TransactionAdmin):
    """Admin interface for the POSTransaction model."""
    
    fieldsets = TransactionAdmin.fieldsets + (
        ('POS Details', {
            'fields': (
                'terminal_id', 
                'entry_mode', 
                'terminal_type', 
                'attendance', 
                'condition', 
                'mcc', 
                'authorization_code', 
                'recurring_payment'
            )
        }),
        ('Response Details', {
            'fields': (
                'response_code', 
                'processor_response_code', 
                'avs_result', 
                'cvv_result', 
                'response_time'
            )
        }),
    )


class EcommerceTransactionAdmin(TransactionAdmin):
    """Admin interface for the EcommerceTransaction model."""
    
    fieldsets = TransactionAdmin.fieldsets + (
        ('E-commerce Details', {
            'fields': (
                'website_url', 
                'is_3ds_verified', 
                'device_fingerprint', 
                'shipping_address', 
                'billing_address', 
                'is_billing_shipping_match', 
                'mcc', 
                'authorization_code', 
                'recurring_payment'
            )
        }),
        ('Response Details', {
            'fields': (
                'response_code', 
                'processor_response_code', 
                'avs_result', 
                'cvv_result', 
                'response_time'
            )
        }),
    )


class WalletTransactionAdmin(TransactionAdmin):
    """Admin interface for the WalletTransaction model."""
    
    fieldsets = TransactionAdmin.fieldsets + (
        ('Wallet Details', {
            'fields': (
                'wallet_id', 
                'source_type', 
                'destination_type', 
                'source_id', 
                'destination_id', 
                'transaction_purpose', 
                'is_internal'
            )
        }),
    )


# Register models with admin site
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(POSTransaction, POSTransactionAdmin)
admin.site.register(EcommerceTransaction, EcommerceTransactionAdmin)
admin.site.register(WalletTransaction, WalletTransactionAdmin)