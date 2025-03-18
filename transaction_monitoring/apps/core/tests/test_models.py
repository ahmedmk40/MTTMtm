"""
Tests for core models.
"""

from django.test import TestCase
from django.utils import timezone
from apps.core.models import TimeStampedModel
from django.db import models


# Create a concrete model for testing the abstract TimeStampedModel
class TestModel(TimeStampedModel):
    """Concrete model for testing TimeStampedModel."""
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'core'


class TimeStampedModelTests(TestCase):
    """Tests for TimeStampedModel."""
    
    def test_timestamped_model_creation(self):
        """Test TimeStampedModel creation."""
        # Create a test model instance
        test_model = TestModel(name='Test')
        test_model.save()
        
        # Check that the created_at field is set
        self.assertIsNotNone(test_model.created_at)
        
        # Check that the updated_at field is set
        self.assertIsNotNone(test_model.updated_at)
        
        # Check that created_at and updated_at are the same on creation
        self.assertEqual(test_model.created_at, test_model.updated_at)
    
    def test_timestamped_model_update(self):
        """Test TimeStampedModel update."""
        # Create a test model instance
        test_model = TestModel(name='Test')
        test_model.save()
        
        # Store the original timestamps
        original_created_at = test_model.created_at
        original_updated_at = test_model.updated_at
        
        # Wait a moment to ensure the timestamps will be different
        import time
        time.sleep(0.1)
        
        # Update the test model
        test_model.name = 'Updated Test'
        test_model.save()
        
        # Check that the created_at field hasn't changed
        self.assertEqual(test_model.created_at, original_created_at)
        
        # Check that the updated_at field has changed
        self.assertNotEqual(test_model.updated_at, original_updated_at)
        
        # Check that updated_at is later than created_at
        self.assertGreater(test_model.updated_at, test_model.created_at)
    
    def test_timestamped_model_ordering(self):
        """Test TimeStampedModel ordering."""
        # Create multiple test model instances
        TestModel.objects.create(name='Test 1')
        
        # Wait a moment to ensure the timestamps will be different
        import time
        time.sleep(0.1)
        
        TestModel.objects.create(name='Test 2')
        
        # Wait a moment to ensure the timestamps will be different
        time.sleep(0.1)
        
        TestModel.objects.create(name='Test 3')
        
        # Get all test models ordered by created_at (default ordering)
        test_models = TestModel.objects.all()
        
        # Check that the models are ordered by created_at in ascending order
        self.assertEqual(test_models[0].name, 'Test 1')
        self.assertEqual(test_models[1].name, 'Test 2')
        self.assertEqual(test_models[2].name, 'Test 3')
        
        # Check that the created_at timestamps are in ascending order
        self.assertLess(test_models[0].created_at, test_models[1].created_at)
        self.assertLess(test_models[1].created_at, test_models[2].created_at)