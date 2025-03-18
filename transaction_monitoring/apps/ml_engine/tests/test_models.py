"""
Tests for ML engine models.
"""

from django.test import TestCase
from django.utils import timezone
from apps.ml_engine.models import MLModel, MLPrediction, FeatureDefinition


class MLModelTests(TestCase):
    """Tests for MLModel model."""
    
    def setUp(self):
        """Set up test data."""
        self.model_data = {
            'name': 'Test Model',
            'description': 'A test model for unit testing',
            'model_type': 'classification',
            'version': '1.0',
            'file_path': 'ml_models/test_model_v1.pkl',
            'is_active': True,
            'accuracy': 0.95,
            'precision': 0.92,
            'recall': 0.88,
            'f1_score': 0.90,
            'auc_roc': 0.96,
            'training_date': timezone.now(),
            'training_data_size': 10000,
            'training_parameters': {
                'n_estimators': 100,
                'max_depth': 10,
                'random_state': 42
            },
            'feature_importance': {
                'amount': 0.25,
                'is_new_card': 0.15,
                'is_high_risk_country': 0.12,
                'is_night': 0.10,
                'is_suspicious_mcc': 0.08
            }
        }
    
    def test_ml_model_creation(self):
        """Test MLModel creation."""
        model = MLModel.objects.create(**self.model_data)
        
        # Check that the model was created
        self.assertEqual(MLModel.objects.count(), 1)
        
        # Check that the model has the expected attributes
        self.assertEqual(model.name, self.model_data['name'])
        self.assertEqual(model.description, self.model_data['description'])
        self.assertEqual(model.model_type, self.model_data['model_type'])
        self.assertEqual(model.version, self.model_data['version'])
        self.assertEqual(model.file_path, self.model_data['file_path'])
        self.assertEqual(model.is_active, self.model_data['is_active'])
        self.assertEqual(model.accuracy, self.model_data['accuracy'])
        self.assertEqual(model.precision, self.model_data['precision'])
        self.assertEqual(model.recall, self.model_data['recall'])
        self.assertEqual(model.f1_score, self.model_data['f1_score'])
        self.assertEqual(model.auc_roc, self.model_data['auc_roc'])
        self.assertEqual(model.training_data_size, self.model_data['training_data_size'])
        self.assertEqual(model.training_parameters, self.model_data['training_parameters'])
        self.assertEqual(model.feature_importance, self.model_data['feature_importance'])
    
    def test_ml_model_string_representation(self):
        """Test MLModel string representation."""
        model = MLModel.objects.create(**self.model_data)
        
        # Check that the string representation is as expected
        self.assertEqual(str(model), f"{self.model_data['name']} v{self.model_data['version']}")
    
    def test_ml_model_unique_together_constraint(self):
        """Test MLModel unique_together constraint."""
        # Create a model
        MLModel.objects.create(**self.model_data)
        
        # Try to create another model with the same name and version
        with self.assertRaises(Exception):
            MLModel.objects.create(**self.model_data)
        
        # Create a model with the same name but different version
        self.model_data['version'] = '2.0'
        model2 = MLModel.objects.create(**self.model_data)
        
        # Check that the second model was created
        self.assertEqual(MLModel.objects.count(), 2)
        self.assertEqual(model2.version, '2.0')


class MLPredictionTests(TestCase):
    """Tests for MLPrediction model."""
    
    def setUp(self):
        """Set up test data."""
        # Create a model for the prediction
        self.model = MLModel.objects.create(
            name='Test Model',
            description='A test model for unit testing',
            model_type='classification',
            version='1.0',
            file_path='ml_models/test_model_v1.pkl',
            is_active=True
        )
        
        self.prediction_data = {
            'transaction_id': 'tx_test_123',
            'model': self.model,
            'prediction': 0.85,
            'prediction_probability': 0.85,
            'features': {
                'amount': 100.0,
                'is_new_card': 1,
                'is_high_risk_country': 0,
                'is_night': 1,
                'is_suspicious_mcc': 0
            },
            'explanation': {
                'top_features': [
                    {'name': 'amount', 'importance': 0.25, 'value': 100.0},
                    {'name': 'is_new_card', 'importance': 0.15, 'value': 1},
                    {'name': 'is_night', 'importance': 0.10, 'value': 1}
                ],
                'feature_importance': {
                    'amount': 0.25,
                    'is_new_card': 0.15,
                    'is_high_risk_country': 0.12,
                    'is_night': 0.10,
                    'is_suspicious_mcc': 0.08
                }
            },
            'execution_time': 25.5
        }
    
    def test_ml_prediction_creation(self):
        """Test MLPrediction creation."""
        prediction = MLPrediction.objects.create(**self.prediction_data)
        
        # Check that the prediction was created
        self.assertEqual(MLPrediction.objects.count(), 1)
        
        # Check that the prediction has the expected attributes
        self.assertEqual(prediction.transaction_id, self.prediction_data['transaction_id'])
        self.assertEqual(prediction.model, self.model)
        self.assertEqual(prediction.prediction, self.prediction_data['prediction'])
        self.assertEqual(prediction.prediction_probability, self.prediction_data['prediction_probability'])
        self.assertEqual(prediction.features, self.prediction_data['features'])
        self.assertEqual(prediction.explanation, self.prediction_data['explanation'])
        self.assertEqual(prediction.execution_time, self.prediction_data['execution_time'])
    
    def test_ml_prediction_string_representation(self):
        """Test MLPrediction string representation."""
        prediction = MLPrediction.objects.create(**self.prediction_data)
        
        # Check that the string representation is as expected
        self.assertEqual(
            str(prediction),
            f"{self.model.name} - {self.prediction_data['transaction_id']} - {self.prediction_data['prediction']}"
        )


class FeatureDefinitionTests(TestCase):
    """Tests for FeatureDefinition model."""
    
    def setUp(self):
        """Set up test data."""
        self.feature_data = {
            'name': 'amount',
            'description': 'Transaction amount',
            'data_type': 'float',
            'source': 'transaction',
            'transformation': 'log',
            'is_active': True
        }
    
    def test_feature_definition_creation(self):
        """Test FeatureDefinition creation."""
        feature = FeatureDefinition.objects.create(**self.feature_data)
        
        # Check that the feature was created
        self.assertEqual(FeatureDefinition.objects.count(), 1)
        
        # Check that the feature has the expected attributes
        self.assertEqual(feature.name, self.feature_data['name'])
        self.assertEqual(feature.description, self.feature_data['description'])
        self.assertEqual(feature.data_type, self.feature_data['data_type'])
        self.assertEqual(feature.source, self.feature_data['source'])
        self.assertEqual(feature.transformation, self.feature_data['transformation'])
        self.assertEqual(feature.is_active, self.feature_data['is_active'])
    
    def test_feature_definition_string_representation(self):
        """Test FeatureDefinition string representation."""
        feature = FeatureDefinition.objects.create(**self.feature_data)
        
        # Check that the string representation is as expected
        self.assertEqual(str(feature), self.feature_data['name'])