"""
Management command to test merchant-specific rules.
"""

import uuid
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.transactions.models import Transaction
from apps.rule_engine.services.evaluator import evaluate_rules


class Command(BaseCommand):
    """
    Command to test merchant-specific rules.
    """
    
    help = 'Test merchant-specific rules'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--rule_id',
            type=int,
            help='ID of the rule to test'
        )
        
        parser.add_argument(
            '--merchant_id',
            type=str,
            default='test_merchant',
            help='Merchant ID to use for testing'
        )
        
        parser.add_argument(
            '--amount',
            type=float,
            default=1000.0,
            help='Transaction amount to use for testing'
        )
    
    def handle(self, *args, **options):
        rule_id = options.get('rule_id')
        merchant_id = options.get('merchant_id')
        amount = options.get('amount')
        
        self.stdout.write(self.style.NOTICE(f"Testing merchant-specific rules for merchant {merchant_id}"))
        
        # Create a test transaction
        transaction_id = f"test_tx_{uuid.uuid4().hex[:8]}"
        
        transaction = Transaction.objects.create(
            transaction_id=transaction_id,
            user_id='test_user',
            merchant_id=merchant_id,
            transaction_type='acquiring',
            channel='pos',
            amount=amount,
            currency='USD',
            status='pending',
            timestamp=timezone.now()
        )
        
        self.stdout.write(f"Created test transaction {transaction_id} with amount {amount}")
        
        # Evaluate rules
        result = evaluate_rules(transaction)
        
        # Display results
        self.stdout.write(f"Evaluated {result['rules_evaluated']} rules in {result['execution_time']:.2f}ms")
        
        if result['rules_triggered']:
            self.stdout.write(self.style.SUCCESS(f"Triggered {result['rules_triggered']} rules:"))
            
            for rule in result['triggered_rules']:
                self.stdout.write(f"  - {rule['name']} (ID: {rule['id']}, Risk Score: {rule['risk_score']})")
                if 'condition_values' in rule:
                    for key, value in rule['condition_values'].items():
                        self.stdout.write(f"    {key}: {value}")
        else:
            self.stdout.write(self.style.WARNING("No rules were triggered"))
        
        # If a specific rule was requested, check if it was triggered
        if rule_id:
            triggered_rule_ids = [rule['id'] for rule in result['triggered_rules']]
            
            if rule_id in triggered_rule_ids:
                self.stdout.write(self.style.SUCCESS(f"Rule {rule_id} was triggered for merchant {merchant_id}"))
            else:
                self.stdout.write(self.style.WARNING(f"Rule {rule_id} was NOT triggered for merchant {merchant_id}"))