"""
Tests for AML models.
"""

from django.test import TestCase
from django.utils import timezone
from apps.aml.models import AMLRiskProfile, AMLAlert, SuspiciousActivityReport, TransactionPattern


class AMLRiskProfileTests(TestCase):
    """Tests for AMLRiskProfile model."""
    
    def setUp(self):
        """Set up test data."""
        self.risk_profile_data = {
            'user_id': 'user_123',
            'risk_level': 'medium',
            'risk_score': 45.5,
            'transaction_volume': 5000.0,
            'transaction_count': 25,
            'high_risk_transactions': 3,
            'suspicious_patterns': 2,
            'notes': 'Test risk profile',
            'risk_factors': ['structuring', 'high_risk_jurisdiction']
        }
    
    def test_risk_profile_creation(self):
        """Test AMLRiskProfile creation."""
        risk_profile = AMLRiskProfile.objects.create(**self.risk_profile_data)
        
        # Check that the risk profile was created
        self.assertEqual(AMLRiskProfile.objects.count(), 1)
        
        # Check that the risk profile has the expected attributes
        self.assertEqual(risk_profile.user_id, self.risk_profile_data['user_id'])
        self.assertEqual(risk_profile.risk_level, self.risk_profile_data['risk_level'])
        self.assertEqual(float(risk_profile.risk_score), self.risk_profile_data['risk_score'])
        self.assertEqual(float(risk_profile.transaction_volume), self.risk_profile_data['transaction_volume'])
        self.assertEqual(risk_profile.transaction_count, self.risk_profile_data['transaction_count'])
        self.assertEqual(risk_profile.high_risk_transactions, self.risk_profile_data['high_risk_transactions'])
        self.assertEqual(risk_profile.suspicious_patterns, self.risk_profile_data['suspicious_patterns'])
        self.assertEqual(risk_profile.notes, self.risk_profile_data['notes'])
        self.assertEqual(risk_profile.risk_factors, self.risk_profile_data['risk_factors'])
    
    def test_risk_profile_string_representation(self):
        """Test AMLRiskProfile string representation."""
        risk_profile = AMLRiskProfile.objects.create(**self.risk_profile_data)
        
        # Check that the string representation is as expected
        self.assertEqual(str(risk_profile), f"{self.risk_profile_data['user_id']} - Medium")


class AMLAlertTests(TestCase):
    """Tests for AMLAlert model."""
    
    def setUp(self):
        """Set up test data."""
        self.alert_data = {
            'alert_id': 'AML-12345678',
            'user_id': 'user_123',
            'alert_type': 'structuring',
            'description': 'Suspicious structuring pattern detected',
            'status': 'open',
            'risk_score': 75.0,
            'related_transactions': ['tx_123', 'tx_456', 'tx_789'],
            'related_entities': ['user_456', 'merchant_789'],
            'detection_data': {
                'pattern': 'multiple_small_transactions',
                'threshold': 10000.0,
                'total_amount': 9500.0,
                'transaction_count': 5
            }
        }
    
    def test_alert_creation(self):
        """Test AMLAlert creation."""
        alert = AMLAlert.objects.create(**self.alert_data)
        
        # Check that the alert was created
        self.assertEqual(AMLAlert.objects.count(), 1)
        
        # Check that the alert has the expected attributes
        self.assertEqual(alert.alert_id, self.alert_data['alert_id'])
        self.assertEqual(alert.user_id, self.alert_data['user_id'])
        self.assertEqual(alert.alert_type, self.alert_data['alert_type'])
        self.assertEqual(alert.description, self.alert_data['description'])
        self.assertEqual(alert.status, self.alert_data['status'])
        self.assertEqual(float(alert.risk_score), self.alert_data['risk_score'])
        self.assertEqual(alert.related_transactions, self.alert_data['related_transactions'])
        self.assertEqual(alert.related_entities, self.alert_data['related_entities'])
        self.assertEqual(alert.detection_data, self.alert_data['detection_data'])
    
    def test_alert_string_representation(self):
        """Test AMLAlert string representation."""
        alert = AMLAlert.objects.create(**self.alert_data)
        
        # Check that the string representation is as expected
        self.assertEqual(str(alert), f"{self.alert_data['alert_id']} - Structuring (Open)")


class SuspiciousActivityReportTests(TestCase):
    """Tests for SuspiciousActivityReport model."""
    
    def setUp(self):
        """Set up test data."""
        self.sar_data = {
            'sar_id': 'SAR-12345678',
            'user_id': 'user_123',
            'title': 'Suspicious activity report for user_123',
            'description': 'Multiple suspicious patterns detected',
            'status': 'draft',
            'related_alerts': ['AML-12345678', 'AML-87654321'],
            'related_transactions': ['tx_123', 'tx_456', 'tx_789'],
            'supporting_evidence': [
                {'type': 'transaction_pattern', 'id': 'pattern_123'},
                {'type': 'risk_profile', 'id': 'profile_123'}
            ],
            'prepared_by': 'analyst_123'
        }
    
    def test_sar_creation(self):
        """Test SuspiciousActivityReport creation."""
        sar = SuspiciousActivityReport.objects.create(**self.sar_data)
        
        # Check that the SAR was created
        self.assertEqual(SuspiciousActivityReport.objects.count(), 1)
        
        # Check that the SAR has the expected attributes
        self.assertEqual(sar.sar_id, self.sar_data['sar_id'])
        self.assertEqual(sar.user_id, self.sar_data['user_id'])
        self.assertEqual(sar.title, self.sar_data['title'])
        self.assertEqual(sar.description, self.sar_data['description'])
        self.assertEqual(sar.status, self.sar_data['status'])
        self.assertEqual(sar.related_alerts, self.sar_data['related_alerts'])
        self.assertEqual(sar.related_transactions, self.sar_data['related_transactions'])
        self.assertEqual(sar.supporting_evidence, self.sar_data['supporting_evidence'])
        self.assertEqual(sar.prepared_by, self.sar_data['prepared_by'])
    
    def test_sar_string_representation(self):
        """Test SuspiciousActivityReport string representation."""
        sar = SuspiciousActivityReport.objects.create(**self.sar_data)
        
        # Check that the string representation is as expected
        self.assertEqual(str(sar), f"{self.sar_data['sar_id']} - {self.sar_data['title']} (Draft)")


class TransactionPatternTests(TestCase):
    """Tests for TransactionPattern model."""
    
    def setUp(self):
        """Set up test data."""
        self.pattern_data = {
            'user_id': 'user_123',
            'pattern_type': 'structuring',
            'pattern_data': {
                'transactions': [
                    {
                        'transaction_id': 'tx_123',
                        'amount': 2500.0,
                        'currency': 'USD',
                        'timestamp': timezone.now().isoformat()
                    },
                    {
                        'transaction_id': 'tx_456',
                        'amount': 2500.0,
                        'currency': 'USD',
                        'timestamp': timezone.now().isoformat()
                    },
                    {
                        'transaction_id': 'tx_789',
                        'amount': 2500.0,
                        'currency': 'USD',
                        'timestamp': timezone.now().isoformat()
                    }
                ],
                'threshold': 10000.0,
                'total_amount': 7500.0
            },
            'occurrence_count': 3,
            'risk_score': 75.0,
            'is_suspicious': True
        }
    
    def test_pattern_creation(self):
        """Test TransactionPattern creation."""
        pattern = TransactionPattern.objects.create(**self.pattern_data)
        
        # Check that the pattern was created
        self.assertEqual(TransactionPattern.objects.count(), 1)
        
        # Check that the pattern has the expected attributes
        self.assertEqual(pattern.user_id, self.pattern_data['user_id'])
        self.assertEqual(pattern.pattern_type, self.pattern_data['pattern_type'])
        self.assertEqual(pattern.pattern_data, self.pattern_data['pattern_data'])
        self.assertEqual(pattern.occurrence_count, self.pattern_data['occurrence_count'])
        self.assertEqual(float(pattern.risk_score), self.pattern_data['risk_score'])
        self.assertEqual(pattern.is_suspicious, self.pattern_data['is_suspicious'])
    
    def test_pattern_string_representation(self):
        """Test TransactionPattern string representation."""
        pattern = TransactionPattern.objects.create(**self.pattern_data)
        
        # Check that the string representation is as expected
        self.assertEqual(str(pattern), f"{self.pattern_data['user_id']} - Structuring (3 occurrences)")