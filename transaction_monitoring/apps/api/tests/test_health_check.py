"""
Tests for the health_check API endpoint.
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch, MagicMock


class HealthCheckAPITests(APITestCase):
    """Tests for the health_check API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        # Set up the API client
        self.client = APIClient()
        
        # URL for the health_check endpoint
        self.url = reverse('api:health_check')
    
    def test_health_check_success(self):
        """Test health check when all services are healthy."""
        # Mock the database and Redis connections to return success
        with patch('django.db.connection.cursor') as mock_db_cursor, \
             patch('redis.from_url') as mock_redis:
            
            # Set up the database cursor mock
            mock_cursor = MagicMock()
            mock_db_cursor.return_value.__enter__.return_value = mock_cursor
            
            # Set up the Redis mock
            mock_redis_client = MagicMock()
            mock_redis.return_value = mock_redis_client
            
            # Make the request
            response = self.client.get(self.url)
            
            # Check that the response has the expected status code
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Check that the response contains the expected data
            self.assertEqual(response.data['status'], 'healthy')
            self.assertEqual(response.data['database'], 'connected')
            self.assertEqual(response.data['redis'], 'connected')
            self.assertIn('timestamp', response.data)
            self.assertIn('version', response.data)
    
    def test_health_check_database_failure(self):
        """Test health check when the database connection fails."""
        # Mock the database connection to raise an exception and Redis to succeed
        with patch('django.db.connection.cursor') as mock_db_cursor, \
             patch('redis.from_url') as mock_redis:
            
            # Set up the database cursor mock to raise an exception
            mock_db_cursor.side_effect = Exception('Database connection error')
            
            # Set up the Redis mock
            mock_redis_client = MagicMock()
            mock_redis.return_value = mock_redis_client
            
            # Make the request
            response = self.client.get(self.url)
            
            # Check that the response has the expected status code
            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Check that the response contains the expected data
            self.assertEqual(response.data['status'], 'unhealthy')
            self.assertEqual(response.data['database'], 'disconnected')
            self.assertEqual(response.data['redis'], 'connected')
    
    def test_health_check_redis_failure(self):
        """Test health check when the Redis connection fails."""
        # Mock the database connection to succeed and Redis to raise an exception
        with patch('django.db.connection.cursor') as mock_db_cursor, \
             patch('redis.from_url') as mock_redis:
            
            # Set up the database cursor mock
            mock_cursor = MagicMock()
            mock_db_cursor.return_value.__enter__.return_value = mock_cursor
            
            # Set up the Redis mock to raise an exception
            mock_redis_client = MagicMock()
            mock_redis_client.ping.side_effect = Exception('Redis connection error')
            mock_redis.return_value = mock_redis_client
            
            # Make the request
            response = self.client.get(self.url)
            
            # Check that the response has the expected status code
            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Check that the response contains the expected data
            self.assertEqual(response.data['status'], 'unhealthy')
            self.assertEqual(response.data['database'], 'connected')
            self.assertEqual(response.data['redis'], 'disconnected')
    
    def test_health_check_all_failures(self):
        """Test health check when all service connections fail."""
        # Mock both the database and Redis connections to raise exceptions
        with patch('django.db.connection.cursor') as mock_db_cursor, \
             patch('redis.from_url') as mock_redis:
            
            # Set up the database cursor mock to raise an exception
            mock_db_cursor.side_effect = Exception('Database connection error')
            
            # Set up the Redis mock to raise an exception
            mock_redis_client = MagicMock()
            mock_redis_client.ping.side_effect = Exception('Redis connection error')
            mock_redis.return_value = mock_redis_client
            
            # Make the request
            response = self.client.get(self.url)
            
            # Check that the response has the expected status code
            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Check that the response contains the expected data
            self.assertEqual(response.data['status'], 'unhealthy')
            self.assertEqual(response.data['database'], 'disconnected')
            self.assertEqual(response.data['redis'], 'disconnected')