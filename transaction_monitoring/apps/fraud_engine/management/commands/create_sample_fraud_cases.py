"""
Management command to create sample fraud cases for testing.
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.fraud_engine.models import FraudCase, FraudDetectionResult, BlockList
from apps.transactions.models import Transaction


class Command(BaseCommand):
    help = 'Create sample fraud cases for testing'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, nargs='?', default=20,
                            help='Number of fraud cases to create (default: 20)')

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(f"Creating {count} sample fraud cases...")
        
        # Get transactions to associate with fraud cases
        transactions = Transaction.objects.all()
        if not transactions.exists():
            self.stdout.write(self.style.WARNING("No transactions found. Please create transactions first."))
            return
        
        # Create fraud cases
        self.create_fraud_cases(count, transactions)
        
        # Create some block list entries
        self.create_block_list_entries(count // 4)
        
        self.stdout.write(self.style.SUCCESS(f"Successfully created {count} sample fraud cases!"))

    def create_fraud_cases(self, count, transactions):
        """Create sample fraud cases."""
        statuses = [choice[0] for choice in FraudCase.CASE_STATUS_CHOICES]
        priorities = [choice[0] for choice in FraudCase.CASE_PRIORITY_CHOICES]
        
        for i in range(count):
            # Get a random user_id from transactions
            if transactions.exists():
                transaction = transactions.order_by('?').first()
                user_id = transaction.user_id
            else:
                user_id = f"user_{random.randint(1, 10)}"
            
            status = random.choice(statuses)
            priority = random.choice(priorities)
            
            # Create related transactions list
            related_transactions = []
            for transaction in transactions.filter(user_id=user_id)[:random.randint(1, 5)]:
                related_transactions.append(transaction.transaction_id)
            
            # Create the fraud case
            case = FraudCase(
                case_id=f"CASE{random.randint(10000, 99999)}",
                user_id=user_id,
                title=f"Potential fraud for {user_id}",
                description=f"Suspicious activity detected for user {user_id}",
                status=status,
                priority=priority,
                assigned_to=f"analyst_{random.randint(1, 5)}" if random.random() > 0.3 else None,
                related_transactions=related_transactions,
                resolution_notes="Case resolved due to..." if status in ['resolved', 'closed'] else None,
                resolved_at=timezone.now() - timedelta(days=random.randint(0, 10)) if status in ['resolved', 'closed'] else None,
                resolved_by=f"analyst_{random.randint(1, 5)}" if status in ['resolved', 'closed'] else None,
                created_at=timezone.now() - timedelta(days=random.randint(0, 30))
            )
            case.save()
            self.stdout.write(f"Created fraud case: {case.case_id}")
            
            # Create fraud detection results for this case
            self.create_fraud_detection_results(case, related_transactions)

    def create_fraud_detection_results(self, case, transaction_ids):
        """Create sample fraud detection results for a case."""
        decisions = ['approve', 'reject', 'review']
        
        # Get existing transaction_ids to avoid duplicates
        existing_transaction_ids = set(FraudDetectionResult.objects.values_list('transaction_id', flat=True))
        
        for transaction_id in transaction_ids:
            # Skip if this transaction_id already has a detection result
            if transaction_id in existing_transaction_ids:
                self.stdout.write(self.style.WARNING(f"  Skipping existing detection result for transaction: {transaction_id}"))
                continue
                
            # Create the fraud detection result
            try:
                result = FraudDetectionResult(
                    transaction_id=transaction_id,
                    risk_score=Decimal(str(round(random.uniform(50, 95), 2))),
                    is_fraudulent=random.random() > 0.5,
                    decision=random.choice(decisions),
                    processing_time=random.uniform(100, 500),
                    block_check_result={'blocked': False, 'reason': None},
                    rule_engine_result={
                        'rules_triggered': random.randint(1, 5),
                        'highest_score_rule': f"rule_{random.randint(1, 20)}"
                    },
                    velocity_engine_result={
                        'velocity_score': round(random.uniform(0, 100), 2),
                        'thresholds_exceeded': random.randint(0, 3)
                    },
                    ml_engine_result={
                        'model_version': '1.0',
                        'prediction': random.random() > 0.5,
                        'confidence': round(random.uniform(0.7, 0.99), 2)
                    },
                    aml_engine_result={
                        'aml_score': round(random.uniform(0, 100), 2),
                        'suspicious_patterns': random.randint(0, 2)
                    },
                    triggered_rules=[f"rule_{random.randint(1, 50)}" for _ in range(random.randint(0, 5))]
                )
                result.save()
                existing_transaction_ids.add(transaction_id)
                self.stdout.write(f"  Created fraud detection result for transaction: {transaction_id}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Could not create detection result for transaction {transaction_id}: {e}"))

    def create_block_list_entries(self, count):
        """Create sample block list entries."""
        entity_types = [choice[0] for choice in BlockList.ENTITY_TYPE_CHOICES]
        
        for i in range(count):
            entity_type = random.choice(entity_types)
            
            # Generate entity value based on type
            if entity_type == 'user_id':
                entity_value = f"user_{random.randint(1, 100)}"
            elif entity_type == 'card_number':
                entity_value = f"4111111111111{random.randint(100, 999)}"
            elif entity_type == 'device_id':
                entity_value = f"device_{random.randint(1000, 9999)}"
            elif entity_type == 'ip_address':
                entity_value = f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}"
            elif entity_type == 'merchant_id':
                entity_value = f"merchant_{random.randint(100, 999)}"
            else:  # email
                entity_value = f"user{random.randint(1, 100)}@example.com"
            
            # Create the block list entry
            try:
                block = BlockList(
                    entity_type=entity_type,
                    entity_value=entity_value,
                    reason=f"Blocked due to suspicious activity",
                    is_active=random.random() > 0.2,
                    expires_at=timezone.now() + timedelta(days=random.randint(30, 365)) if random.random() > 0.5 else None,
                    added_by=f"analyst_{random.randint(1, 5)}"
                )
                block.save()
                self.stdout.write(f"Created block list entry: {block.entity_type} - {block.entity_value}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not create block list entry: {e}"))