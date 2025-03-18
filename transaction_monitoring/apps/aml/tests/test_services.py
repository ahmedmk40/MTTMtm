"""
Tests for AML services.
"""

from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from apps.aml.models import AMLRiskProfile, AMLAlert, TransactionPattern
from apps.aml.services.monitoring_service import (
    check_aml_risk,
    check_structuring,
    check_round_amount,
    check_high_risk_jurisdiction,
    check_rapid_movement,
    record_pattern,
    create_aml_alert,
    update_risk_profile
)


class MonitoringServiceTests(TestCase):
    """Tests for monitoring_service module."""
    
    def setUp(self):
        """Set up test data."""
        # Create a mock wallet transaction
        self.transaction = MagicMock()
        self.transaction.transaction_id = 'tx_wallet_123'
        self.transaction.channel = 'wallet'
        self.transaction.amount = 9500.0
        self.transaction.currency = 'USD'
        self.transaction.user_id = 'user_123'
        self.transaction.timestamp = timezone.now()
        self.transaction.source_type = 'wallet'
        self.transaction.source_id = 'wallet_123'
        self.transaction.destination_type = 'bank_account'
        self.transaction.destination_id = 'bank_456'
        self.transaction.transaction_purpose = 'withdrawal'
        self.transaction.is_internal = False
        self.transaction.location_data = {
            'country': 'US',
            'city': 'New York',
            'zip': '10001',
            'ip_address': '192.168.1.1'
        }
    
    def test_check_structuring(self):
        """Test check_structuring function."""
        # Test with amount just below threshold
        self.transaction.amount = 9500.0
        self.assertTrue(check_structuring(self.transaction))
        
        # Test with amount above threshold
        self.transaction.amount = 11000.0
        self.assertFalse(check_structuring(self.transaction))
        
        # Test with amount well below threshold
        self.transaction.amount = 5000.0
        self.assertFalse(check_structuring(self.transaction))
    
    def test_check_round_amount(self):
        """Test check_round_amount function."""
        # Test with round amount
        self.transaction.amount = 5000.0
        self.assertTrue(check_round_amount(self.transaction))
        
        # Test with non-round amount
        self.transaction.amount = 5123.45
        self.assertFalse(check_round_amount(self.transaction))
    
    @patch('apps.aml.services.monitoring_service.HIGH_RISK_COUNTRIES', ['IR', 'KP', 'SY'])
    def test_check_high_risk_jurisdiction(self):
        """Test check_high_risk_jurisdiction function."""
        # Test with high-risk country
        self.transaction.location_data = {'country': 'IR'}
        self.assertTrue(check_high_risk_jurisdiction(self.transaction))
        
        # Test with low-risk country
        self.transaction.location_data = {'country': 'US'}
        self.assertFalse(check_high_risk_jurisdiction(self.transaction))
    
    def test_check_rapid_movement(self):
        """Test check_rapid_movement function."""
        # Test with large withdrawal
        self.transaction.transaction_purpose = 'withdrawal'
        self.transaction.amount = 6000.0
        self.assertTrue(check_rapid_movement(self.transaction))
        
        # Test with small withdrawal
        self.transaction.amount = 1000.0
        self.assertFalse(check_rapid_movement(self.transaction))
        
        # Test with large transfer
        self.transaction.transaction_purpose = 'transfer'
        self.transaction.amount = 6000.0
        self.assertTrue(check_rapid_movement(self.transaction))
        
        # Test with deposit (should not trigger)
        self.transaction.transaction_purpose = 'deposit'
        self.transaction.amount = 6000.0
        self.assertFalse(check_rapid_movement(self.transaction))
    
    def test_record_pattern(self):
        """Test record_pattern function."""
        # Test creating a new pattern
        pattern_data = {
            'transaction_id': self.transaction.transaction_id,
            'amount': float(self.transaction.amount),
            'currency': self.transaction.currency,
            'timestamp': self.transaction.timestamp.isoformat()
        }
        
        pattern = record_pattern(
            user_id=self.transaction.user_id,
            pattern_type='structuring',
            pattern_data=pattern_data,
            risk_score=80.0
        )
        
        # Check that the pattern was created
        self.assertEqual(TransactionPattern.objects.count(), 1)
        self.assertEqual(pattern.user_id, self.transaction.user_id)
        self.assertEqual(pattern.pattern_type, 'structuring')
        self.assertEqual(pattern.occurrence_count, 1)
        self.assertEqual(float(pattern.risk_score), 80.0)
        self.assertFalse(pattern.is_suspicious)  # Not suspicious on first occurrence
        
        # Test updating an existing pattern
        pattern_data2 = {
            'transaction_id': 'tx_wallet_456',
            'amount': 9000.0,
            'currency': 'USD',
            'timestamp': timezone.now().isoformat()
        }
        
        updated_pattern = record_pattern(
            user_id=self.transaction.user_id,
            pattern_type='structuring',
            pattern_data=pattern_data2,
            risk_score=85.0
        )
        
        # Check that the pattern was updated, not created
        self.assertEqual(TransactionPattern.objects.count(), 1)
        self.assertEqual(updated_pattern.occurrence_count, 2)
        self.assertEqual(float(updated_pattern.risk_score), 85.0)  # Higher risk score takes precedence
        self.assertFalse(updated_pattern.is_suspicious)  # Still not suspicious
        
        # Test updating again to reach suspicious threshold
        pattern_data3 = {
            'transaction_id': 'tx_wallet_789',
            'amount': 9200.0,
            'currency': 'USD',
            'timestamp': timezone.now().isoformat()
        }
        
        updated_pattern = record_pattern(
            user_id=self.transaction.user_id,
            pattern_type='structuring',
            pattern_data=pattern_data3,
            risk_score=85.0
        )
        
        # Check that the pattern is now marked as suspicious
        self.assertEqual(updated_pattern.occurrence_count, 3)
        self.assertTrue(updated_pattern.is_suspicious)  # Now suspicious (3+ occurrences)
    
    def test_create_aml_alert(self):
        """Test create_aml_alert function."""
        # Create a result dictionary
        result = {
            'risk_score': 80.0,
            'is_suspicious': True,
            'patterns_detected': [
                {
                    'type': 'structuring',
                    'description': 'Transaction amount just below reporting threshold',
                    'risk_score': 80.0
                }
            ],
            'triggered_rules': [
                {
                    'id': 'aml_structuring',
                    'name': 'Structuring Detection',
                    'description': 'Transaction amount just below reporting threshold',
                    'rule_type': 'aml',
                    'action': 'review',
                    'risk_score': 80.0
                }
            ]
        }
        
        # Create an alert
        alert = create_aml_alert(self.transaction, result)
        
        # Check that the alert was created
        self.assertEqual(AMLAlert.objects.count(), 1)
        self.assertEqual(alert.user_id, self.transaction.user_id)
        self.assertEqual(alert.alert_type, 'structuring')
        self.assertEqual(float(alert.risk_score), result['risk_score'])
        self.assertEqual(alert.status, 'open')
        self.assertEqual(alert.related_transactions, [self.transaction.transaction_id])
        self.assertEqual(alert.detection_data['patterns_detected'], result['patterns_detected'])
        self.assertEqual(alert.detection_data['triggered_rules'], result['triggered_rules'])
    
    def test_update_risk_profile(self):
        """Test update_risk_profile function."""
        # Create a risk profile
        risk_profile = AMLRiskProfile.objects.create(
            user_id=self.transaction.user_id,
            risk_level='low',
            risk_score=20.0,
            transaction_volume=10000.0,
            transaction_count=10,
            high_risk_transactions=1,
            suspicious_patterns=1,
            risk_factors=['high_risk_jurisdiction']
        )
        
        # Create a result dictionary
        result = {
            'risk_score': 80.0,
            'is_suspicious': True,
            'patterns_detected': [
                {
                    'type': 'structuring',
                    'description': 'Transaction amount just below reporting threshold',
                    'risk_score': 80.0
                }
            ],
            'triggered_rules': [
                {
                    'id': 'aml_structuring',
                    'name': 'Structuring Detection',
                    'description': 'Transaction amount just below reporting threshold',
                    'rule_type': 'aml',
                    'action': 'review',
                    'risk_score': 80.0
                }
            ]
        }
        
        # Update the risk profile
        updated_profile = update_risk_profile(risk_profile, self.transaction, result)
        
        # Check that the risk profile was updated
        self.assertEqual(updated_profile.transaction_count, 11)  # Incremented
        self.assertEqual(float(updated_profile.transaction_volume), 10000.0 + float(self.transaction.amount))
        self.assertEqual(updated_profile.high_risk_transactions, 2)  # Incremented
        self.assertEqual(updated_profile.suspicious_patterns, 2)  # Incremented
        
        # Check that the risk factors were updated
        self.assertIn('structuring', updated_profile.risk_factors)
        self.assertIn('high_risk_jurisdiction', updated_profile.risk_factors)
        
        # Check that the risk score and level were updated
        self.assertGreater(float(updated_profile.risk_score), 20.0)
        self.assertNotEqual(updated_profile.risk_level, 'low')  # Should be higher now
    
    @patch('apps.aml.services.monitoring_service.check_structuring')
    @patch('apps.aml.services.monitoring_service.check_round_amount')
    @patch('apps.aml.services.monitoring_service.check_high_risk_jurisdiction')
    @patch('apps.aml.services.monitoring_service.check_rapid_movement')
    @patch('apps.aml.services.monitoring_service.record_pattern')
    @patch('apps.aml.services.monitoring_service.create_aml_alert')
    @patch('apps.aml.services.monitoring_service.update_risk_profile')
    def test_check_aml_risk(self, mock_update_risk_profile, mock_create_aml_alert, 
                           mock_record_pattern, mock_check_rapid_movement, 
                           mock_check_high_risk_jurisdiction, mock_check_round_amount, 
                           mock_check_structuring):
        """Test check_aml_risk function."""
        # Set up mocks
        mock_check_structuring.return_value = True
        mock_check_round_amount.return_value = False
        mock_check_high_risk_jurisdiction.return_value = False
        mock_check_rapid_movement.return_value = True
        
        # Create a risk profile
        risk_profile = AMLRiskProfile.objects.create(
            user_id=self.transaction.user_id,
            risk_level='low',
            risk_score=20.0
        )
        
        # Mock record_pattern to return a pattern
        pattern = TransactionPattern(
            user_id=self.transaction.user_id,
            pattern_type='structuring',
            risk_score=80.0
        )
        mock_record_pattern.return_value = pattern
        
        # Check AML risk
        result = check_aml_risk(self.transaction)
        
        # Check that the result has the expected structure
        self.assertIn('risk_score', result)
        self.assertIn('is_suspicious', result)
        self.assertIn('triggered_rules', result)
        self.assertIn('patterns_detected', result)
        self.assertIn('execution_time', result)
        
        # Check that the result indicates suspicious activity
        self.assertTrue(result['is_suspicious'])
        self.assertGreater(result['risk_score'], 0.0)
        
        # Check that the appropriate functions were called
        mock_check_structuring.assert_called_once_with(self.transaction)
        mock_check_round_amount.assert_called_once_with(self.transaction)
        mock_check_high_risk_jurisdiction.assert_called_once_with(self.transaction)
        mock_check_rapid_movement.assert_called_once_with(self.transaction)
        
        # Check that record_pattern was called for the detected patterns
        self.assertEqual(mock_record_pattern.call_count, 2)  # structuring and rapid movement
        
        # Check that create_aml_alert was called
        mock_create_aml_alert.assert_called_once_with(self.transaction, result)
        
        # Check that update_risk_profile was called
        mock_update_risk_profile.assert_called_once()