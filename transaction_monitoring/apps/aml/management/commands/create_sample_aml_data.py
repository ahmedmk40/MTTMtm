"""
Management command to create sample AML data for testing.
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.aml.models import AMLAlert, AMLRiskProfile, SuspiciousActivityReport, TransactionPattern


class Command(BaseCommand):
    help = 'Create sample AML data for testing'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, nargs='?', default=20,
                            help='Number of records to create (default: 20)')

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(f"Creating {count} sample AML records...")
        
        # Create AML alerts
        self.create_aml_alerts(count)
        
        # Create AML risk profiles
        self.create_aml_risk_profiles(count // 2)
        
        # Create SARs
        self.create_sars(count // 4)
        
        # Create transaction patterns
        self.create_transaction_patterns(count)
        
        self.stdout.write(self.style.SUCCESS(f"Successfully created sample AML data!"))

    def create_aml_alerts(self, count):
        """Create sample AML alerts."""
        alert_types = [choice[0] for choice in AMLAlert.ALERT_TYPE_CHOICES]
        statuses = [choice[0] for choice in AMLAlert.STATUS_CHOICES]
        
        for i in range(count):
            user_id = f"user_{random.randint(1, 10)}"
            alert_type = random.choice(alert_types)
            status = random.choice(statuses)
            
            # Generate a random date within the last 30 days
            created_date = timezone.now() - timedelta(days=random.randint(0, 30))
            
            # Create related transactions
            related_transactions = []
            for j in range(random.randint(1, 5)):
                related_transactions.append({
                    'transaction_id': f"tx_{random.randint(10000, 99999)}",
                    'amount': float(round(random.uniform(100, 10000), 2)),
                    'currency': random.choice(['USD', 'EUR', 'GBP']),
                    'timestamp': (created_date - timedelta(hours=random.randint(1, 48))).isoformat()
                })
            
            # Create detection data
            detection_data = {
                'detection_method': random.choice(['rule_based', 'ml_model', 'pattern_matching']),
                'confidence': random.uniform(0.7, 0.99),
                'trigger_rules': [f"rule_{random.randint(1, 20)}" for _ in range(random.randint(1, 3))]
            }
            
            # Create the alert
            alert = AMLAlert(
                alert_id=f"AML{random.randint(10000, 99999)}",
                user_id=user_id,
                alert_type=alert_type,
                description=f"Suspicious {alert_type} activity detected for user {user_id}",
                status=status,
                risk_score=Decimal(str(round(random.uniform(50, 95), 2))),
                related_transactions=related_transactions,
                related_entities=[{'entity_type': 'user', 'entity_id': user_id}],
                detection_data=detection_data,
                assigned_to=f"analyst_{random.randint(1, 5)}" if random.random() > 0.3 else None,
                investigation_notes="Investigation in progress..." if status == 'investigating' else "",
                resolution_notes="Case closed due to..." if 'closed' in status else "",
                closed_at=timezone.now() if 'closed' in status else None,
                closed_by=f"analyst_{random.randint(1, 5)}" if 'closed' in status else None,
                created_at=created_date,
                updated_at=created_date + timedelta(days=random.randint(0, 5))
            )
            alert.save()
            self.stdout.write(f"Created AML alert: {alert.alert_id}")

    def create_aml_risk_profiles(self, count):
        """Create sample AML risk profiles."""
        risk_levels = [choice[0] for choice in AMLRiskProfile.RISK_LEVEL_CHOICES]
        
        # Get existing user_ids to avoid duplicates
        existing_user_ids = set(AMLRiskProfile.objects.values_list('user_id', flat=True))
        
        created = 0
        attempts = 0
        
        while created < count and attempts < count * 3:
            attempts += 1
            user_id = f"user_{random.randint(1, 100)}"
            
            # Skip if this user_id already exists
            if user_id in existing_user_ids:
                continue
                
            existing_user_ids.add(user_id)
            risk_level = random.choice(risk_levels)
            
            # Risk score based on risk level
            if risk_level == 'low':
                risk_score = round(random.uniform(0, 25), 2)
            elif risk_level == 'medium':
                risk_score = round(random.uniform(25, 50), 2)
            elif risk_level == 'high':
                risk_score = round(random.uniform(50, 75), 2)
            else:  # critical
                risk_score = round(random.uniform(75, 100), 2)
            
            # Create risk factors
            risk_factors = []
            for j in range(random.randint(1, 5)):
                risk_factors.append({
                    'factor': random.choice([
                        'high_volume_transactions', 
                        'cross_border_activity',
                        'high_risk_jurisdiction',
                        'unusual_transaction_patterns',
                        'rapid_movement_of_funds',
                        'round_dollar_amounts',
                        'multiple_accounts'
                    ]),
                    'weight': round(random.uniform(0.1, 1.0), 2),
                    'description': f"Risk factor {j+1} description"
                })
            
            # Create the risk profile
            profile = AMLRiskProfile(
                user_id=user_id,
                risk_level=risk_level,
                risk_score=Decimal(str(risk_score)),
                transaction_volume=Decimal(str(round(random.uniform(1000, 100000), 2))),
                transaction_count=random.randint(10, 500),
                high_risk_transactions=random.randint(0, 50),
                suspicious_patterns=random.randint(0, 10),
                notes=f"Risk profile notes for user {user_id}",
                risk_factors=risk_factors,
                last_assessment=timezone.now() - timedelta(days=random.randint(0, 30))
            )
            profile.save()
            created += 1
            self.stdout.write(f"Created AML risk profile for: {profile.user_id}")

    def create_sars(self, count):
        """Create sample Suspicious Activity Reports."""
        statuses = [choice[0] for choice in SuspiciousActivityReport.STATUS_CHOICES]
        
        for i in range(count):
            user_id = f"user_{random.randint(1, 10)}"
            status = random.choice(statuses)
            
            # Generate a random date within the last 60 days
            created_date = timezone.now() - timedelta(days=random.randint(0, 60))
            
            # Create related alerts
            related_alerts = [f"AML{random.randint(10000, 99999)}" for _ in range(random.randint(1, 3))]
            
            # Create related transactions
            related_transactions = []
            for j in range(random.randint(3, 10)):
                related_transactions.append({
                    'transaction_id': f"tx_{random.randint(10000, 99999)}",
                    'amount': float(round(random.uniform(1000, 50000), 2)),
                    'currency': random.choice(['USD', 'EUR', 'GBP']),
                    'timestamp': (created_date - timedelta(days=random.randint(1, 30))).isoformat()
                })
            
            # Create supporting evidence
            supporting_evidence = []
            for j in range(random.randint(1, 5)):
                supporting_evidence.append({
                    'type': random.choice(['transaction_pattern', 'user_behavior', 'external_information']),
                    'description': f"Evidence {j+1} description",
                    'confidence': round(random.uniform(0.7, 0.99), 2)
                })
            
            # Create the SAR
            sar = SuspiciousActivityReport(
                sar_id=f"SAR{random.randint(10000, 99999)}",
                user_id=user_id,
                title=f"Suspicious activity report for {user_id}",
                description=f"Detailed description of suspicious activity for {user_id}",
                status=status,
                related_alerts=related_alerts,
                related_transactions=related_transactions,
                supporting_evidence=supporting_evidence,
                prepared_by=f"analyst_{random.randint(1, 5)}",
                approved_by=f"manager_{random.randint(1, 3)}" if status in ['approved', 'filed'] else None,
                filed_by=f"compliance_{random.randint(1, 3)}" if status == 'filed' else None,
                filed_at=timezone.now() - timedelta(days=random.randint(0, 10)) if status == 'filed' else None,
                filing_reference=f"REF{random.randint(100000, 999999)}" if status == 'filed' else None,
                created_at=created_date,
                updated_at=created_date + timedelta(days=random.randint(0, 15))
            )
            sar.save()
            self.stdout.write(f"Created SAR: {sar.sar_id}")

    def create_transaction_patterns(self, count):
        """Create sample transaction patterns."""
        pattern_types = [choice[0] for choice in TransactionPattern.PATTERN_TYPE_CHOICES]
        
        for i in range(count):
            user_id = f"user_{random.randint(1, 20)}"
            pattern_type = random.choice(pattern_types)
            is_suspicious = random.random() > 0.7
            
            # Generate a random date within the last 90 days
            first_detected = timezone.now() - timedelta(days=random.randint(0, 90))
            last_detected = first_detected + timedelta(days=random.randint(0, 30))
            
            # Create pattern data based on pattern type
            pattern_data = {}
            if pattern_type == 'structuring':
                transactions = [
                    {'amount': round(random.uniform(8000, 9999), 2), 'date': (first_detected + timedelta(hours=random.randint(1, 24))).isoformat()}
                    for _ in range(random.randint(2, 5))
                ]
                pattern_data = {
                    'threshold': 10000,
                    'transactions': transactions,
                    'total_amount': round(sum(t['amount'] for t in transactions), 2)
                }
            elif pattern_type == 'round_amount':
                pattern_data = {
                    'amounts': [round(random.randint(1, 10) * 1000, 2) for _ in range(random.randint(2, 5))],
                    'frequency': random.randint(1, 10)
                }
            elif pattern_type == 'rapid_movement':
                pattern_data = {
                    'time_window': random.randint(1, 24),
                    'transaction_count': random.randint(3, 10),
                    'total_amount': round(random.uniform(10000, 100000), 2)
                }
            else:
                pattern_data = {
                    'description': f"Pattern data for {pattern_type}",
                    'metrics': {
                        'frequency': random.randint(1, 10),
                        'average_amount': round(random.uniform(1000, 10000), 2),
                        'total_amount': round(random.uniform(10000, 100000), 2)
                    }
                }
            
            # Create the transaction pattern
            pattern = TransactionPattern(
                user_id=user_id,
                pattern_type=pattern_type,
                pattern_data=pattern_data,
                first_detected=first_detected,
                last_detected=last_detected,
                occurrence_count=random.randint(1, 20),
                risk_score=Decimal(str(round(random.uniform(30, 95), 2))),
                is_suspicious=is_suspicious
            )
            pattern.save()
            self.stdout.write(f"Created transaction pattern: {pattern.id} - {pattern.pattern_type}")