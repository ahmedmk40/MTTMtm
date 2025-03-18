"""
Tests for transaction models.
"""

from django.test import TestCase
from django.utils import timezone
from apps.transactions.models import (
    Transaction,
    POSTransaction,
    EcommerceTransaction,
    WalletTransaction
)


class TransactionModelTests(TestCase):
    """Tests for Transaction model."""
    
    def setUp(self):
        """Set up test data."""
        self.transaction_data = {
            'transaction_id': 'tx_test_123',
            'transaction_type': 'acquiring',
            'channel': 'pos',
            'amount': 100.00,
            'currency': 'USD',
            'user_id': 'user_123',
            'merchant_id': 'merchant_456',
            'timestamp': timezone.now(),
            'status': 'pending',
            'device_id': 'device_789',
            'location_data': {
                'country': 'US',
                'city': 'New York',
                'zip': '10001',
                'ip_address': '192.168.1.1'
            },
            'payment_method_data': {
                'type': 'credit_card',
                'card_details': {
                    'card_number': '4111111111111111',
                    'expiry_month': '12',
                    'expiry_year': '2025',
                    'cardholder_name': 'John Doe',
                    'cvv': '123'
                }
            }
        }
    
    def test_transaction_creation(self):
        """Test Transaction creation."""
        transaction = Transaction.objects.create(**self.transaction_data)
        
        # Check that the transaction was created
        self.assertEqual(Transaction.objects.count(), 1)
        
        # Check that the transaction has the expected attributes
        self.assertEqual(transaction.transaction_id, self.transaction_data['transaction_id'])
        self.assertEqual(transaction.transaction_type, self.transaction_data['transaction_type'])
        self.assertEqual(transaction.channel, self.transaction_data['channel'])
        self.assertEqual(float(transaction.amount), self.transaction_data['amount'])
        self.assertEqual(transaction.currency, self.transaction_data['currency'])
        self.assertEqual(transaction.user_id, self.transaction_data['user_id'])
        self.assertEqual(transaction.merchant_id, self.transaction_data['merchant_id'])
        self.assertEqual(transaction.status, self.transaction_data['status'])
        self.assertEqual(transaction.device_id, self.transaction_data['device_id'])
        
        # Check that the location data was saved
        self.assertEqual(transaction.location_data, self.transaction_data['location_data'])
    
    def test_transaction_sensitive_data_hashing(self):
        """Test that sensitive data is hashed when saving a transaction."""
        transaction = Transaction.objects.create(**self.transaction_data)
        
        # Check that the card number was hashed
        self.assertNotEqual(
            transaction.payment_method_data['card_details']['card_number'],
            self.transaction_data['payment_method_data']['card_details']['card_number']
        )
        
        # Check that the CVV was hashed
        self.assertNotEqual(
            transaction.payment_method_data['card_details']['cvv'],
            self.transaction_data['payment_method_data']['card_details']['cvv']
        )
        
        # Check that a masked card number was added
        self.assertEqual(
            transaction.payment_method_data['card_details']['masked_card_number'],
            '************1111'
        )
    
    def test_transaction_string_representation(self):
        """Test Transaction string representation."""
        transaction = Transaction.objects.create(**self.transaction_data)
        
        # Check that the string representation is as expected
        self.assertEqual(
            str(transaction),
            f"{self.transaction_data['transaction_id']} - {self.transaction_data['amount']} {self.transaction_data['currency']}"
        )


class POSTransactionModelTests(TestCase):
    """Tests for POSTransaction model."""
    
    def setUp(self):
        """Set up test data."""
        self.transaction_data = {
            'transaction_id': 'tx_pos_123',
            'transaction_type': 'acquiring',
            'channel': 'pos',
            'amount': 100.00,
            'currency': 'USD',
            'user_id': 'user_123',
            'merchant_id': 'merchant_456',
            'timestamp': timezone.now(),
            'status': 'pending',
            'device_id': 'device_789',
            'location_data': {
                'country': 'US',
                'city': 'New York',
                'zip': '10001',
                'ip_address': '192.168.1.1'
            },
            'payment_method_data': {
                'type': 'credit_card',
                'card_details': {
                    'card_number': '4111111111111111',
                    'expiry_month': '12',
                    'expiry_year': '2025',
                    'cardholder_name': 'John Doe',
                    'cvv': '123'
                }
            },
            'terminal_id': 'term_123',
            'entry_mode': 'chip',
            'terminal_type': 'standard',
            'attendance': 'attended',
            'condition': 'card_present',
            'authorization_code': 'auth_123',
            'recurring_payment': False,
            'response_details': {
                'response_code': 'approved',
                'processor_response_code': '00',
                'avs_result': 'Y',
                'cvv_result': 'M'
            }
        }
    
    def test_pos_transaction_creation(self):
        """Test POSTransaction creation."""
        transaction = POSTransaction.objects.create(**self.transaction_data)
        
        # Check that the transaction was created
        self.assertEqual(POSTransaction.objects.count(), 1)
        
        # Check that the transaction has the expected attributes
        self.assertEqual(transaction.transaction_id, self.transaction_data['transaction_id'])
        self.assertEqual(transaction.transaction_type, self.transaction_data['transaction_type'])
        self.assertEqual(transaction.channel, self.transaction_data['channel'])
        self.assertEqual(float(transaction.amount), self.transaction_data['amount'])
        self.assertEqual(transaction.currency, self.transaction_data['currency'])
        self.assertEqual(transaction.user_id, self.transaction_data['user_id'])
        self.assertEqual(transaction.merchant_id, self.transaction_data['merchant_id'])
        self.assertEqual(transaction.status, self.transaction_data['status'])
        self.assertEqual(transaction.device_id, self.transaction_data['device_id'])
        
        # Check POS-specific fields
        self.assertEqual(transaction.terminal_id, self.transaction_data['terminal_id'])
        self.assertEqual(transaction.entry_mode, self.transaction_data['entry_mode'])
        self.assertEqual(transaction.terminal_type, self.transaction_data['terminal_type'])
        self.assertEqual(transaction.attendance, self.transaction_data['attendance'])
        self.assertEqual(transaction.condition, self.transaction_data['condition'])
        self.assertEqual(transaction.authorization_code, self.transaction_data['authorization_code'])
        self.assertEqual(transaction.recurring_payment, self.transaction_data['recurring_payment'])
        self.assertEqual(transaction.response_details, self.transaction_data['response_details'])


class EcommerceTransactionModelTests(TestCase):
    """Tests for EcommerceTransaction model."""
    
    def setUp(self):
        """Set up test data."""
        self.transaction_data = {
            'transaction_id': 'tx_ecom_123',
            'transaction_type': 'acquiring',
            'channel': 'ecommerce',
            'amount': 100.00,
            'currency': 'USD',
            'user_id': 'user_123',
            'merchant_id': 'merchant_456',
            'timestamp': timezone.now(),
            'status': 'pending',
            'device_id': 'device_789',
            'location_data': {
                'country': 'US',
                'city': 'New York',
                'zip': '10001',
                'ip_address': '192.168.1.1'
            },
            'payment_method_data': {
                'type': 'credit_card',
                'card_details': {
                    'card_number': '4111111111111111',
                    'expiry_month': '12',
                    'expiry_year': '2025',
                    'cardholder_name': 'John Doe',
                    'cvv': '123'
                }
            },
            'website_url': 'https://example.com/checkout',
            'is_3ds_verified': True,
            'device_fingerprint': 'fp_123456',
            'authorization_code': 'auth_123',
            'recurring_payment': False,
            'shipping_address': {
                'street': '123 Main St',
                'city': 'New York',
                'state': 'NY',
                'postal_code': '10001',
                'country': 'US'
            },
            'billing_address': {
                'street': '123 Main St',
                'city': 'New York',
                'state': 'NY',
                'postal_code': '10001',
                'country': 'US'
            },
            'is_billing_shipping_match': True,
            'response_details': {
                'response_code': 'approved',
                'processor_response_code': '00',
                'avs_result': 'Y',
                'cvv_result': 'M'
            }
        }
    
    def test_ecommerce_transaction_creation(self):
        """Test EcommerceTransaction creation."""
        transaction = EcommerceTransaction.objects.create(**self.transaction_data)
        
        # Check that the transaction was created
        self.assertEqual(EcommerceTransaction.objects.count(), 1)
        
        # Check that the transaction has the expected attributes
        self.assertEqual(transaction.transaction_id, self.transaction_data['transaction_id'])
        self.assertEqual(transaction.transaction_type, self.transaction_data['transaction_type'])
        self.assertEqual(transaction.channel, self.transaction_data['channel'])
        self.assertEqual(float(transaction.amount), self.transaction_data['amount'])
        self.assertEqual(transaction.currency, self.transaction_data['currency'])
        self.assertEqual(transaction.user_id, self.transaction_data['user_id'])
        self.assertEqual(transaction.merchant_id, self.transaction_data['merchant_id'])
        self.assertEqual(transaction.status, self.transaction_data['status'])
        self.assertEqual(transaction.device_id, self.transaction_data['device_id'])
        
        # Check e-commerce-specific fields
        self.assertEqual(transaction.website_url, self.transaction_data['website_url'])
        self.assertEqual(transaction.is_3ds_verified, self.transaction_data['is_3ds_verified'])
        self.assertEqual(transaction.device_fingerprint, self.transaction_data['device_fingerprint'])
        self.assertEqual(transaction.authorization_code, self.transaction_data['authorization_code'])
        self.assertEqual(transaction.recurring_payment, self.transaction_data['recurring_payment'])
        self.assertEqual(transaction.shipping_address, self.transaction_data['shipping_address'])
        self.assertEqual(transaction.billing_address, self.transaction_data['billing_address'])
        self.assertEqual(transaction.is_billing_shipping_match, self.transaction_data['is_billing_shipping_match'])
        self.assertEqual(transaction.response_details, self.transaction_data['response_details'])


class WalletTransactionModelTests(TestCase):
    """Tests for WalletTransaction model."""
    
    def setUp(self):
        """Set up test data."""
        self.transaction_data = {
            'transaction_id': 'tx_wallet_123',
            'transaction_type': 'wallet',
            'channel': 'wallet',
            'amount': 100.00,
            'currency': 'USD',
            'user_id': 'user_123',
            'timestamp': timezone.now(),
            'status': 'pending',
            'device_id': 'device_789',
            'location_data': {
                'country': 'US',
                'city': 'New York',
                'zip': '10001',
                'ip_address': '192.168.1.1'
            },
            'payment_method_data': {
                'type': 'wallet',
                'wallet_details': {
                    'wallet_type': 'digital',
                    'wallet_provider': 'example_wallet'
                }
            },
            'wallet_id': 'wallet_123',
            'transaction_purpose': 'transfer',
            'source_type': 'wallet',
            'source_id': 'wallet_123',
            'destination_type': 'bank_account',
            'destination_id': 'bank_456',
            'is_internal': False
        }
    
    def test_wallet_transaction_creation(self):
        """Test WalletTransaction creation."""
        transaction = WalletTransaction.objects.create(**self.transaction_data)
        
        # Check that the transaction was created
        self.assertEqual(WalletTransaction.objects.count(), 1)
        
        # Check that the transaction has the expected attributes
        self.assertEqual(transaction.transaction_id, self.transaction_data['transaction_id'])
        self.assertEqual(transaction.transaction_type, self.transaction_data['transaction_type'])
        self.assertEqual(transaction.channel, self.transaction_data['channel'])
        self.assertEqual(float(transaction.amount), self.transaction_data['amount'])
        self.assertEqual(transaction.currency, self.transaction_data['currency'])
        self.assertEqual(transaction.user_id, self.transaction_data['user_id'])
        self.assertEqual(transaction.status, self.transaction_data['status'])
        self.assertEqual(transaction.device_id, self.transaction_data['device_id'])
        
        # Check wallet-specific fields
        self.assertEqual(transaction.wallet_id, self.transaction_data['wallet_id'])
        self.assertEqual(transaction.transaction_purpose, self.transaction_data['transaction_purpose'])
        self.assertEqual(transaction.source_type, self.transaction_data['source_type'])
        self.assertEqual(transaction.source_id, self.transaction_data['source_id'])
        self.assertEqual(transaction.destination_type, self.transaction_data['destination_type'])
        self.assertEqual(transaction.destination_id, self.transaction_data['destination_id'])
        self.assertEqual(transaction.is_internal, self.transaction_data['is_internal'])