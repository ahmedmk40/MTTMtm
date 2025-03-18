"""
Tests for ML engine services.
"""

from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
from apps.ml_engine.models import MLModel
from apps.ml_engine.services.feature_service import extract_features, transform_features
from apps.ml_engine.services.model_service import train_model, save_model, activate_model, get_active_model


class FeatureServiceTests(TestCase):
    """Tests for feature_service module."""
    
    def setUp(self):
        """Set up test data."""
        # Create a mock transaction
        self.transaction = MagicMock()
        self.transaction.transaction_id = 'tx_test_123'
        self.transaction.amount = 100.0
        self.transaction.transaction_type = 'acquiring'
        self.transaction.channel = 'pos'
        self.transaction.timestamp = timezone.now()
        self.transaction.location_data = {
            'country': 'US',
            'city': 'New York',
            'zip': '10001',
            'ip_address': '192.168.1.1'
        }
        self.transaction.payment_method_data = {
            'type': 'credit_card',
            'card_details': {
                'card_number': '4111111111111111',
                'expiry_month': '12',
                'expiry_year': '2025',
                'cardholder_name': 'John Doe',
                'cvv': '123',
                'is_new': False
            }
        }
        self.transaction.mcc = '5411'
    
    def test_extract_features(self):
        """Test extract_features function."""
        features = extract_features(self.transaction)
        
        # Check that the features dictionary contains the expected keys
        self.assertIn('amount', features)
        self.assertIn('transaction_type', features)
        self.assertIn('channel', features)
        self.assertIn('hour_of_day', features)
        self.assertIn('day_of_week', features)
        self.assertIn('is_weekend', features)
        self.assertIn('is_night', features)
        self.assertIn('country', features)
        self.assertIn('has_ip', features)
        self.assertIn('payment_method_type', features)
        self.assertIn('is_new_card', features)
        self.assertIn('mcc', features)
        
        # Check that the features have the expected values
        self.assertEqual(features['amount'], float(self.transaction.amount))
        self.assertEqual(features['transaction_type'], self.transaction.transaction_type)
        self.assertEqual(features['channel'], self.transaction.channel)
        self.assertEqual(features['country'], self.transaction.location_data['country'])
        self.assertEqual(features['has_ip'], 1)  # IP address is present
        self.assertEqual(features['payment_method_type'], self.transaction.payment_method_data['type'])
        self.assertEqual(features['is_new_card'], 0)  # is_new is False
        self.assertEqual(features['mcc'], self.transaction.mcc)
    
    def test_transform_features(self):
        """Test transform_features function."""
        # Extract raw features
        raw_features = extract_features(self.transaction)
        
        # Transform features
        transformed_features = transform_features(raw_features)
        
        # Check that the transformed features dictionary contains the expected keys
        self.assertIn('amount', transformed_features)
        self.assertIn('hour_of_day', transformed_features)
        self.assertIn('day_of_week', transformed_features)
        self.assertIn('is_weekend', transformed_features)
        self.assertIn('is_night', transformed_features)
        self.assertIn('has_ip', transformed_features)
        self.assertIn('is_new_card', transformed_features)
        
        # Check one-hot encoded features
        self.assertIn('transaction_type_acquiring', transformed_features)
        self.assertIn('transaction_type_wallet', transformed_features)
        self.assertIn('channel_pos', transformed_features)
        self.assertIn('channel_ecommerce', transformed_features)
        self.assertIn('channel_wallet', transformed_features)
        self.assertIn('payment_method_type_credit_card', transformed_features)
        
        # Check that the transformed features have the expected values
        self.assertEqual(transformed_features['amount'], raw_features['amount'])
        self.assertEqual(transformed_features['transaction_type_acquiring'], 1)
        self.assertEqual(transformed_features['transaction_type_wallet'], 0)
        self.assertEqual(transformed_features['channel_pos'], 1)
        self.assertEqual(transformed_features['channel_ecommerce'], 0)
        self.assertEqual(transformed_features['channel_wallet'], 0)
        self.assertEqual(transformed_features['payment_method_type_credit_card'], 1)


class ModelServiceTests(TestCase):
    """Tests for model_service module."""
    
    def setUp(self):
        """Set up test data."""
        # Create a mock training dataset
        self.training_data = pd.DataFrame({
            'amount': np.random.exponential(scale=500, size=100),
            'is_new_card': np.random.randint(0, 2, size=100),
            'is_high_risk_country': np.random.randint(0, 2, size=100),
            'is_night': np.random.randint(0, 2, size=100),
            'is_suspicious_mcc': np.random.randint(0, 2, size=100),
            'is_fraud': np.random.randint(0, 2, size=100)
        })
        
        # Model parameters
        self.model_params = {
            'n_estimators': 10,
            'max_depth': 3,
            'random_state': 42
        }
    
    @patch('apps.ml_engine.services.model_service.pickle.dump')
    def test_train_classification_model(self, mock_pickle_dump):
        """Test train_model function for classification models."""
        # Train a classification model
        model, metrics = train_model(
            model_type='classification',
            training_data=self.training_data,
            target_column='is_fraud',
            model_params=self.model_params
        )
        
        # Check that the model was trained
        self.assertIsNotNone(model)
        
        # Check that the metrics dictionary contains the expected keys
        self.assertIn('accuracy', metrics)
        self.assertIn('precision', metrics)
        self.assertIn('recall', metrics)
        self.assertIn('f1_score', metrics)
        self.assertIn('auc_roc', metrics)
        self.assertIn('training_data_size', metrics)
        self.assertIn('feature_importance', metrics)
        
        # Check that the metrics have the expected types
        self.assertIsInstance(metrics['accuracy'], float)
        self.assertIsInstance(metrics['precision'], float)
        self.assertIsInstance(metrics['recall'], float)
        self.assertIsInstance(metrics['f1_score'], float)
        self.assertIsInstance(metrics['auc_roc'], float)
        self.assertEqual(metrics['training_data_size'], len(self.training_data))
        self.assertIsInstance(metrics['feature_importance'], dict)
    
    @patch('apps.ml_engine.services.model_service.pickle.dump')
    def test_save_model(self, mock_pickle_dump):
        """Test save_model function."""
        # Train a model
        model, metrics = train_model(
            model_type='classification',
            training_data=self.training_data,
            target_column='is_fraud',
            model_params=self.model_params
        )
        
        # Save the model
        ml_model = save_model(
            model=model,
            model_type='classification',
            name='Test Model',
            version='1.0',
            description='A test model for unit testing',
            metrics=metrics,
            training_params=self.model_params
        )
        
        # Check that the model was saved to the database
        self.assertEqual(MLModel.objects.count(), 1)
        
        # Check that the model has the expected attributes
        self.assertEqual(ml_model.name, 'Test Model')
        self.assertEqual(ml_model.description, 'A test model for unit testing')
        self.assertEqual(ml_model.model_type, 'classification')
        self.assertEqual(ml_model.version, '1.0')
        self.assertFalse(ml_model.is_active)  # Not active by default
        self.assertEqual(ml_model.accuracy, metrics['accuracy'])
        self.assertEqual(ml_model.precision, metrics['precision'])
        self.assertEqual(ml_model.recall, metrics['recall'])
        self.assertEqual(ml_model.f1_score, metrics['f1_score'])
        self.assertEqual(ml_model.auc_roc, metrics['auc_roc'])
        self.assertEqual(ml_model.training_data_size, metrics['training_data_size'])
        self.assertEqual(ml_model.training_parameters, self.model_params)
        self.assertEqual(ml_model.feature_importance, metrics['feature_importance'])
        
        # Check that pickle.dump was called to save the model file
        mock_pickle_dump.assert_called_once()
    
    def test_activate_model(self):
        """Test activate_model function."""
        # Create two models of the same type
        model1 = MLModel.objects.create(
            name='Test Model 1',
            description='A test model for unit testing',
            model_type='classification',
            version='1.0',
            file_path='ml_models/test_model_v1.pkl',
            is_active=False
        )
        
        model2 = MLModel.objects.create(
            name='Test Model 2',
            description='Another test model for unit testing',
            model_type='classification',
            version='2.0',
            file_path='ml_models/test_model_v2.pkl',
            is_active=False
        )
        
        # Activate the first model
        activated_model = activate_model(model1.id)
        
        # Check that the first model is active
        model1.refresh_from_db()
        self.assertTrue(model1.is_active)
        self.assertEqual(activated_model, model1)
        
        # Check that the second model is not active
        model2.refresh_from_db()
        self.assertFalse(model2.is_active)
        
        # Activate the second model
        activated_model = activate_model(model2.id)
        
        # Check that the second model is now active
        model2.refresh_from_db()
        self.assertTrue(model2.is_active)
        
        # Check that the first model is no longer active
        model1.refresh_from_db()
        self.assertFalse(model1.is_active)
    
    def test_get_active_model(self):
        """Test get_active_model function."""
        # Create a model
        model = MLModel.objects.create(
            name='Test Model',
            description='A test model for unit testing',
            model_type='classification',
            version='1.0',
            file_path='ml_models/test_model_v1.pkl',
            is_active=True
        )
        
        # Get the active model
        active_model = get_active_model('classification')
        
        # Check that the active model is the one we created
        self.assertEqual(active_model, model)
        
        # Try to get an active model of a different type
        active_model = get_active_model('anomaly')
        
        # Check that no active model was found
        self.assertIsNone(active_model)