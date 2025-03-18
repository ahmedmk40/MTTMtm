"""
Tests for the process_transaction API endpoint.
"""

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from apps.transactions.models import (
    Transaction,
    POSTransaction,
    EcommerceTransaction,
    WalletTransaction
)

User = get_user_model()


class ProcessTransactionAPITests(APITestCase):
    """Tests for the process_transaction API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create a token for the test user
        self.token = Token.objects.create(user=self.user)
        
        # Set up the API client
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # URL for the process_transaction endpoint
        self.url = reverse('api:process_transaction')
        
        # Base transaction data
        self.base_transaction_data = {
            'amount': 100.00,
            'currency': 'USD',
            'user_id': 'user_123',
            'timestamp': timezone.now().isoformat(),
        }
    
    def test_process_transaction_unauthorized(self):
        """Test that unauthorized requests are rejected."""
        # Remove authentication credentials
        self.client.credentials()
        
        # Create transaction data
        data = {
            **self.base_transaction_data,
            'transaction_type': 'acquiring',
            'channel': 'pos',
        }
        
        # Make the request
        response = self.client.post(self.url, data, format='json')
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_process_transaction_missing_fields(self):
        """Test that requests with missing required fields are rejected."""
        # Create transaction data with missing fields
        data = {
            'transaction_type': 'acquiring',
            'channel': 'pos',
            # Missing amount, currency, user_id, timestamp
        }
        
        # Make the request
        response = self.client.post(self.url, data, format='json')
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check that the response contains the expected error message
        self.assertIn('error', response.data)
        self.assertIn('Missing required field', response.data['error'])
    
    def test_process_transaction_invalid_channel(self):
        """Test that requests with an invalid channel are rejected."""
        # Create transaction data with an invalid channel
        data = {
            **self.base_transaction_data,
            'transaction_type': 'acquiring',
            'channel': 'invalid_channel',
        }
        
        # Make the request
        response = self.client.post(self.url, data, format='json')
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check that the response contains the expected error message
        self.assertIn('error', response.data)
        self.assertIn('Invalid channel', response.data['error'])
    
    def test_process_pos_transaction(self):
        """Test processing a POS transaction."""
        # Create POS transaction data
        data = {
            **self.base_transaction_data,
            'transaction_type': 'acquiring',
            'channel': 'pos',
            'merchant_id': 'merchant_456',
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
            'mcc': '5411',
            'authorization_code': 'auth_123',
            'recurring_payment': False
        }
        
        # Make the request
        response = self.client.post(self.url, data, format='json')
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the response contains the expected data
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['message'], 'Transaction processed successfully')
        self.assertIn('transaction_id', response.data)
        self.assertEqual(response.data['transaction_status'], 'pending')
        
        # Check that the transaction was created in the database
        transaction_id = response.data['transaction_id']
        self.assertTrue(POSTransaction.objects.filter(transaction_id=transaction_id).exists())
        
        # Get the transaction from the database
        transaction = POSTransaction.objects.get(transaction_id=transaction_id)
        
        # Check that the transaction has the expected attributes
        self.assertEqual(transaction.transaction_type, data['transaction_type'])
        self.assertEqual(transaction.channel, data['channel'])
        self.assertEqual(float(transaction.amount), data['amount'])
        self.assertEqual(transaction.currency, data['currency'])
        self.assertEqual(transaction.user_id, data['user_id'])
        self.assertEqual(transaction.merchant_id, data['merchant_id'])
        self.assertEqual(transaction.device_id, data['device_id'])
        self.assertEqual(transaction.terminal_id, data['terminal_id'])
        self.assertEqual(transaction.entry_mode, data['entry_mode'])
        self.assertEqual(transaction.terminal_type, data['terminal_type'])
        self.assertEqual(transaction.attendance, data['attendance'])
        self.assertEqual(transaction.condition, data['condition'])
        self.assertEqual(transaction.mcc, data['mcc'])
        self.assertEqual(transaction.authorization_code, data['authorization_code'])
        self.assertEqual(transaction.recurring_payment, data['recurring_payment'])
        
        # Check that sensitive data was hashed
        self.assertNotEqual(
            transaction.payment_method_data['card_details']['card_number'],
            data['payment_method_data']['card_details']['card_number']
        )
        self.assertNotEqual(
            transaction.payment_method_data['card_details']['cvv'],
            data['payment_method_data']['card_details']['cvv']
        )
        
        # Check that a masked card number was added
        self.assertEqual(
            transaction.payment_method_data['card_details']['masked_card_number'],
            '************1111'
        )
    
    def test_process_ecommerce_transaction(self):
        """Test processing an e-commerce transaction."""
        # Create e-commerce transaction data
        data = {
            **self.base_transaction_data,
            'transaction_type': 'acquiring',
            'channel': 'ecommerce',
            'merchant_id': 'merchant_456',
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
            'mcc': '5411',
            'authorization_code': 'auth_123',
            'recurring_payment': False
        }
        
        # Make the request
        response = self.client.post(self.url, data, format='json')
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the response contains the expected data
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['message'], 'Transaction processed successfully')
        self.assertIn('transaction_id', response.data)
        self.assertEqual(response.data['transaction_status'], 'pending')
        
        # Check that the transaction was created in the database
        transaction_id = response.data['transaction_id']
        self.assertTrue(EcommerceTransaction.objects.filter(transaction_id=transaction_id).exists())
        
        # Get the transaction from the database
        transaction = EcommerceTransaction.objects.get(transaction_id=transaction_id)
        
        # Check that the transaction has the expected attributes
        self.assertEqual(transaction.transaction_type, data['transaction_type'])
        self.assertEqual(transaction.channel, data['channel'])
        self.assertEqual(float(transaction.amount), data['amount'])
        self.assertEqual(transaction.currency, data['currency'])
        self.assertEqual(transaction.user_id, data['user_id'])
        self.assertEqual(transaction.merchant_id, data['merchant_id'])
        self.assertEqual(transaction.device_id, data['device_id'])
        self.assertEqual(transaction.website_url, data['website_url'])
        self.assertEqual(transaction.is_3ds_verified, data['is_3ds_verified'])
        self.assertEqual(transaction.device_fingerprint, data['device_fingerprint'])
        self.assertEqual(transaction.shipping_address, data['shipping_address'])
        self.assertEqual(transaction.billing_address, data['billing_address'])
        self.assertEqual(transaction.is_billing_shipping_match, data['is_billing_shipping_match'])
        self.assertEqual(transaction.mcc, data['mcc'])
        self.assertEqual(transaction.authorization_code, data['authorization_code'])
        self.assertEqual(transaction.recurring_payment, data['recurring_payment'])
    
    def test_process_wallet_transaction(self):
        """Test processing a wallet transaction."""
        # Create wallet transaction data
        data = {
            **self.base_transaction_data,
            'transaction_type': 'wallet',
            'channel': 'wallet',
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
            'source_type': 'wallet',
            'source_id': 'wallet_123',
            'destination_type': 'bank_account',
            'destination_id': 'bank_456',
            'transaction_purpose': 'withdrawal',
            'is_internal': False
        }
        
        # Make the request
        response = self.client.post(self.url, data, format='json')
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the response contains the expected data
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['message'], 'Transaction processed successfully')
        self.assertIn('transaction_id', response.data)
        self.assertEqual(response.data['transaction_status'], 'pending')
        
        # Check that the transaction was created in the database
        transaction_id = response.data['transaction_id']
        self.assertTrue(WalletTransaction.objects.filter(transaction_id=transaction_id).exists())
        
        # Get the transaction from the database
        transaction = WalletTransaction.objects.get(transaction_id=transaction_id)
        
        # Check that the transaction has the expected attributes
        self.assertEqual(transaction.transaction_type, data['transaction_type'])
        self.assertEqual(transaction.channel, data['channel'])
        self.assertEqual(float(transaction.amount), data['amount'])
        self.assertEqual(transaction.currency, data['currency'])
        self.assertEqual(transaction.user_id, data['user_id'])
        self.assertEqual(transaction.device_id, data['device_id'])
        self.assertEqual(transaction.wallet_id, data['wallet_id'])
        self.assertEqual(transaction.source_type, data['source_type'])
        self.assertEqual(transaction.source_id, data['source_id'])
        self.assertEqual(transaction.destination_type, data['destination_type'])
        self.assertEqual(transaction.destination_id, data['destination_id'])
        self.assertEqual(transaction.transaction_purpose, data['transaction_purpose'])
        self.assertEqual(transaction.is_internal, data['is_internal'])
    
    def test_process_transaction_with_custom_id(self):
        """Test processing a transaction with a custom transaction ID."""
        # Create transaction data with a custom transaction ID
        custom_id = 'custom_tx_123'
        data = {
            **self.base_transaction_data,
            'transaction_id': custom_id,
            'transaction_type': 'acquiring',
            'channel': 'pos',
            'merchant_id': 'merchant_456',
            'terminal_id': 'term_123',
            'entry_mode': 'chip'
        }
        
        # Make the request
        response = self.client.post(self.url, data, format='json')
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the transaction was created with the custom ID
        self.assertEqual(response.data['transaction_id'], custom_id)
        self.assertTrue(POSTransaction.objects.filter(transaction_id=custom_id).exists())