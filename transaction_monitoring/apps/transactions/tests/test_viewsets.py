"""
Tests for transaction viewsets.
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


class TransactionViewSetTests(APITestCase):
    """Tests for the TransactionViewSet."""
    
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
        
        # Create some test transactions
        self.transaction1 = POSTransaction.objects.create(
            transaction_id='tx_pos_1',
            transaction_type='acquiring',
            channel='pos',
            amount=100.00,
            currency='USD',
            user_id='user_123',
            merchant_id='merchant_456',
            timestamp=timezone.now(),
            terminal_id='term_123',
            entry_mode='chip'
        )
        
        self.transaction2 = EcommerceTransaction.objects.create(
            transaction_id='tx_ecom_1',
            transaction_type='acquiring',
            channel='ecommerce',
            amount=200.00,
            currency='USD',
            user_id='user_123',
            merchant_id='merchant_456',
            timestamp=timezone.now(),
            website_url='https://example.com',
            is_3ds_verified=True
        )
        
        self.transaction3 = WalletTransaction.objects.create(
            transaction_id='tx_wallet_1',
            transaction_type='wallet',
            channel='wallet',
            amount=300.00,
            currency='USD',
            user_id='user_123',
            timestamp=timezone.now(),
            wallet_id='wallet_123',
            source_type='wallet',
            source_id='wallet_123',
            destination_type='bank_account',
            destination_id='bank_456',
            transaction_purpose='withdrawal',
            is_internal=False
        )
    
    def test_list_transactions_authenticated(self):
        """Test listing transactions when authenticated."""
        # URL for the transactions list endpoint
        url = reverse('api:transaction-list')
        
        # Make the request
        response = self.client.get(url)
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains the expected data
        self.assertEqual(len(response.data), 3)  # All 3 transactions
    
    def test_list_transactions_unauthenticated(self):
        """Test listing transactions when unauthenticated."""
        # Remove authentication credentials
        self.client.credentials()
        
        # URL for the transactions list endpoint
        url = reverse('api:transaction-list')
        
        # Make the request
        response = self.client.get(url)
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_retrieve_transaction(self):
        """Test retrieving a single transaction."""
        # URL for the transaction detail endpoint
        url = reverse('api:transaction-detail', args=[self.transaction1.transaction_id])
        
        # Make the request
        response = self.client.get(url)
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains the expected data
        self.assertEqual(response.data['transaction_id'], self.transaction1.transaction_id)
        self.assertEqual(response.data['transaction_type'], self.transaction1.transaction_type)
        self.assertEqual(response.data['channel'], self.transaction1.channel)
        self.assertEqual(float(response.data['amount']), float(self.transaction1.amount))
        self.assertEqual(response.data['currency'], self.transaction1.currency)
        self.assertEqual(response.data['user_id'], self.transaction1.user_id)
        self.assertEqual(response.data['merchant_id'], self.transaction1.merchant_id)
    
    def test_filter_transactions_by_user_id(self):
        """Test filtering transactions by user_id."""
        # Create a transaction with a different user_id
        POSTransaction.objects.create(
            transaction_id='tx_pos_2',
            transaction_type='acquiring',
            channel='pos',
            amount=150.00,
            currency='USD',
            user_id='user_456',  # Different user_id
            merchant_id='merchant_456',
            timestamp=timezone.now(),
            terminal_id='term_123',
            entry_mode='chip'
        )
        
        # URL for the transactions list endpoint with filter
        url = reverse('api:transaction-list') + '?user_id=user_123'
        
        # Make the request
        response = self.client.get(url)
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains only transactions for user_123
        self.assertEqual(len(response.data), 3)
        for transaction in response.data:
            self.assertEqual(transaction['user_id'], 'user_123')
    
    def test_filter_transactions_by_channel(self):
        """Test filtering transactions by channel."""
        # URL for the transactions list endpoint with filter
        url = reverse('api:transaction-list') + '?channel=pos'
        
        # Make the request
        response = self.client.get(url)
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains only POS transactions
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['channel'], 'pos')
    
    def test_filter_transactions_by_status(self):
        """Test filtering transactions by status."""
        # Update a transaction's status
        self.transaction1.status = 'approved'
        self.transaction1.save()
        
        # URL for the transactions list endpoint with filter
        url = reverse('api:transaction-list') + '?status=approved'
        
        # Make the request
        response = self.client.get(url)
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains only approved transactions
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'approved')
    
    def test_filter_transactions_by_is_flagged(self):
        """Test filtering transactions by is_flagged."""
        # Update a transaction's is_flagged status
        self.transaction1.is_flagged = True
        self.transaction1.save()
        
        # URL for the transactions list endpoint with filter
        url = reverse('api:transaction-list') + '?is_flagged=true'
        
        # Make the request
        response = self.client.get(url)
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains only flagged transactions
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['is_flagged'], True)
    
    def test_filter_transactions_by_date_range(self):
        """Test filtering transactions by date range."""
        # Create a transaction with an older timestamp
        old_timestamp = timezone.now() - timezone.timedelta(days=10)
        POSTransaction.objects.create(
            transaction_id='tx_pos_old',
            transaction_type='acquiring',
            channel='pos',
            amount=100.00,
            currency='USD',
            user_id='user_123',
            merchant_id='merchant_456',
            timestamp=old_timestamp,
            terminal_id='term_123',
            entry_mode='chip'
        )
        
        # URL for the transactions list endpoint with filter
        today = timezone.now().date().isoformat()
        yesterday = (timezone.now() - timezone.timedelta(days=1)).date().isoformat()
        url = reverse('api:transaction-list') + f'?start_date={yesterday}&end_date={today}'
        
        # Make the request
        response = self.client.get(url)
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains only recent transactions
        self.assertEqual(len(response.data), 3)  # The 3 original transactions, not the old one


class POSTransactionViewSetTests(APITestCase):
    """Tests for the POSTransactionViewSet."""
    
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
        
        # Create some test POS transactions
        self.pos_transaction1 = POSTransaction.objects.create(
            transaction_id='tx_pos_1',
            transaction_type='acquiring',
            channel='pos',
            amount=100.00,
            currency='USD',
            user_id='user_123',
            merchant_id='merchant_456',
            timestamp=timezone.now(),
            terminal_id='term_123',
            entry_mode='chip'
        )
        
        self.pos_transaction2 = POSTransaction.objects.create(
            transaction_id='tx_pos_2',
            transaction_type='acquiring',
            channel='pos',
            amount=200.00,
            currency='USD',
            user_id='user_456',
            merchant_id='merchant_456',
            timestamp=timezone.now(),
            terminal_id='term_456',
            entry_mode='swipe'
        )
    
    def test_list_pos_transactions(self):
        """Test listing POS transactions."""
        # URL for the POS transactions list endpoint
        url = reverse('api:postransaction-list')
        
        # Make the request
        response = self.client.get(url)
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains the expected data
        self.assertEqual(len(response.data), 2)  # Both POS transactions
    
    def test_retrieve_pos_transaction(self):
        """Test retrieving a single POS transaction."""
        # URL for the POS transaction detail endpoint
        url = reverse('api:postransaction-detail', args=[self.pos_transaction1.transaction_id])
        
        # Make the request
        response = self.client.get(url)
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains the expected data
        self.assertEqual(response.data['transaction_id'], self.pos_transaction1.transaction_id)
        self.assertEqual(response.data['transaction_type'], self.pos_transaction1.transaction_type)
        self.assertEqual(response.data['channel'], self.pos_transaction1.channel)
        self.assertEqual(float(response.data['amount']), float(self.pos_transaction1.amount))
        self.assertEqual(response.data['terminal_id'], self.pos_transaction1.terminal_id)
        self.assertEqual(response.data['entry_mode'], self.pos_transaction1.entry_mode)
    
    def test_filter_pos_transactions_by_entry_mode(self):
        """Test filtering POS transactions by entry_mode."""
        # URL for the POS transactions list endpoint with filter
        url = reverse('api:postransaction-list') + '?entry_mode=chip'
        
        # Make the request
        response = self.client.get(url)
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains only chip transactions
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['entry_mode'], 'chip')
    
    def test_filter_pos_transactions_by_terminal_id(self):
        """Test filtering POS transactions by terminal_id."""
        # URL for the POS transactions list endpoint with filter
        url = reverse('api:postransaction-list') + '?terminal_id=term_123'
        
        # Make the request
        response = self.client.get(url)
        
        # Check that the response has the expected status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the response contains only transactions for term_123
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['terminal_id'], 'term_123')