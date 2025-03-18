"""
Management command to test AML pattern detection.
"""

import random
import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.transactions.models import Transaction, WalletTransaction
from apps.aml.services.pattern_detection_service import (
    detect_round_amount_patterns,
    detect_round_transfers_patterns,
    detect_identical_amount_patterns,
    detect_multiple_transactions_between_accounts,
    check_aml_patterns
)


class Command(BaseCommand):
    """
    Command to test AML pattern detection.
    """
    
    help = 'Test AML pattern detection with sample transactions'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--pattern',
            type=str,
            choices=['round_amount', 'round_transfers', 'identical_amount', 'multiple_transactions', 'all'],
            default='all',
            help='Pattern type to test'
        )
        
        parser.add_argument(
            '--user_id',
            type=str,
            default='test_user',
            help='User ID to use for test transactions'
        )
    
    def handle(self, *args, **options):
        pattern = options['pattern']
        user_id = options['user_id']
        
        self.stdout.write(self.style.NOTICE(f'Testing AML pattern detection for {pattern} patterns...'))
        
        if pattern == 'round_amount' or pattern == 'all':
            self.test_round_amount_pattern(user_id)
        
        if pattern == 'round_transfers' or pattern == 'all':
            self.test_round_transfers_pattern(user_id)
        
        if pattern == 'identical_amount' or pattern == 'all':
            self.test_identical_amount_pattern(user_id)
        
        if pattern == 'multiple_transactions' or pattern == 'all':
            self.test_multiple_transactions_pattern(user_id)
        
        self.stdout.write(self.style.SUCCESS('AML pattern detection tests completed'))
    
    def test_round_amount_pattern(self, user_id):
        """
        Test high cumulative value of round-amount transactions pattern.
        """
        self.stdout.write('Testing high cumulative round-amount transactions pattern...')
        
        # Create 5 round-amount transactions
        amounts = [1000, 2000, 5000, 10000, 3000]
        
        for i, amount in enumerate(amounts):
            # Create transaction
            tx_id = f"test_round_{uuid.uuid4().hex[:8]}"
            timestamp = timezone.now() - timedelta(days=i)
            
            transaction = Transaction.objects.create(
                transaction_id=tx_id,
                user_id=user_id,
                merchant_id=f"merchant_{i}",
                transaction_type='acquiring',
                channel='pos',
                amount=amount,
                currency='USD',
                status='completed',
                timestamp=timestamp
            )
            
            self.stdout.write(f"Created transaction {tx_id} with amount {amount}")
        
        # Test pattern detection
        result = detect_round_amount_patterns(user_id)
        
        if result['is_suspicious']:
            self.stdout.write(self.style.SUCCESS(
                f"Pattern detected: {result['transaction_count']} transactions totaling {result['total_amount']}"
            ))
        else:
            self.stdout.write(self.style.WARNING("Pattern not detected"))
    
    def test_round_transfers_pattern(self, user_id):
        """
        Test high cumulative total of round-number transfers pattern.
        """
        self.stdout.write('Testing high cumulative round-number transfers pattern...')
        
        # Create 5 round-number transfers
        amounts = [500, 1000, 1500, 2000, 2500]
        
        for i, amount in enumerate(amounts):
            # Create transaction
            tx_id = f"test_transfer_{uuid.uuid4().hex[:8]}"
            timestamp = timezone.now() - timedelta(days=i)
            
            transaction = WalletTransaction.objects.create(
                transaction_id=tx_id,
                user_id=user_id,
                transaction_type='wallet',
                channel='wallet',
                amount=amount,
                currency='USD',
                status='completed',
                timestamp=timestamp,
                wallet_id=f"wallet_{user_id}",
                source_type='wallet',
                destination_type='bank_account',
                source_id=f"wallet_{user_id}",
                destination_id=f"bank_{i}",
                transaction_purpose='transfer'
            )
            
            self.stdout.write(f"Created wallet transaction {tx_id} with amount {amount}")
        
        # Test pattern detection
        result = detect_round_transfers_patterns(user_id)
        
        if result['is_suspicious']:
            self.stdout.write(self.style.SUCCESS(
                f"Pattern detected: {result['transfer_count']} transfers totaling {result['total_amount']}"
            ))
        else:
            self.stdout.write(self.style.WARNING("Pattern not detected"))
    
    def test_identical_amount_pattern(self, user_id):
        """
        Test 2+ accounts sending identical amounts pattern.
        """
        self.stdout.write('Testing multiple accounts sending identical amounts pattern...')
        
        # Create 3 transactions with identical amounts to the same merchant
        merchant_id = f"test_merchant_{uuid.uuid4().hex[:8]}"
        amount = 1234.56
        
        for i in range(3):
            # Create transaction
            tx_id = f"test_identical_{uuid.uuid4().hex[:8]}"
            timestamp = timezone.now() - timedelta(hours=i)
            
            transaction = Transaction.objects.create(
                transaction_id=tx_id,
                user_id=f"{user_id}_{i}",
                merchant_id=merchant_id,
                transaction_type='acquiring',
                channel='pos',
                amount=amount,
                currency='USD',
                status='completed',
                timestamp=timestamp
            )
            
            self.stdout.write(f"Created transaction {tx_id} from user {user_id}_{i} to merchant {merchant_id} with amount {amount}")
        
        # Test pattern detection
        result = detect_identical_amount_patterns(merchant_id)
        
        if result['is_suspicious']:
            self.stdout.write(self.style.SUCCESS(
                f"Pattern detected: {result['pattern_count']} patterns found"
            ))
            
            for pattern in result['patterns']:
                self.stdout.write(f"  - {pattern['user_count']} users sent identical amounts of {pattern['amount']}")
        else:
            self.stdout.write(self.style.WARNING("Pattern not detected"))
    
    def test_multiple_transactions_pattern(self, user_id):
        """
        Test 3+ transactions between two accounts pattern.
        """
        self.stdout.write('Testing multiple transactions between two accounts pattern...')
        
        # Create 4 transactions between the same two accounts
        other_user = f"other_user_{uuid.uuid4().hex[:8]}"
        
        # Two transactions from user_id to other_user
        for i in range(2):
            tx_id = f"test_multi_out_{uuid.uuid4().hex[:8]}"
            timestamp = timezone.now() - timedelta(hours=i)
            
            transaction = WalletTransaction.objects.create(
                transaction_id=tx_id,
                user_id=user_id,
                merchant_id=other_user,
                transaction_type='wallet',
                channel='wallet',
                amount=random.uniform(100, 500),
                currency='USD',
                status='completed',
                timestamp=timestamp,
                wallet_id=f"wallet_{user_id}",
                source_type='wallet',
                destination_type='wallet',
                source_id=f"wallet_{user_id}",
                destination_id=f"wallet_{other_user}",
                transaction_purpose='transfer'
            )
            
            self.stdout.write(f"Created outgoing transaction {tx_id} from {user_id} to {other_user}")
        
        # Two transactions from other_user to user_id
        for i in range(2):
            tx_id = f"test_multi_in_{uuid.uuid4().hex[:8]}"
            timestamp = timezone.now() - timedelta(hours=i + 2)
            
            transaction = WalletTransaction.objects.create(
                transaction_id=tx_id,
                user_id=other_user,
                merchant_id=user_id,
                transaction_type='wallet',
                channel='wallet',
                amount=random.uniform(100, 500),
                currency='USD',
                status='completed',
                timestamp=timestamp,
                wallet_id=f"wallet_{other_user}",
                source_type='wallet',
                destination_type='wallet',
                source_id=f"wallet_{other_user}",
                destination_id=f"wallet_{user_id}",
                transaction_purpose='transfer'
            )
            
            self.stdout.write(f"Created incoming transaction {tx_id} from {other_user} to {user_id}")
        
        # Test pattern detection
        result = detect_multiple_transactions_between_accounts(user_id)
        
        if result['is_suspicious']:
            self.stdout.write(self.style.SUCCESS(
                f"Pattern detected: {result['pattern_count']} patterns found"
            ))
            
            for pattern in result['patterns']:
                self.stdout.write(
                    f"  - {pattern['transaction_count']} transactions totaling {pattern['total_amount']} "
                    f"{pattern['direction']} between {user_id} and {pattern['other_id']}"
                )
        else:
            self.stdout.write(self.style.WARNING("Pattern not detected"))