"""
Tests for core utility functions.
"""

from django.test import TestCase
from apps.core.utils import (
    generate_transaction_id,
    hash_sensitive_data,
    mask_card_number,
    calculate_distance,
    format_json,
    parse_json
)


class GenerateTransactionIdTests(TestCase):
    """Tests for generate_transaction_id function."""
    
    def test_generate_transaction_id_default_prefix(self):
        """Test generate_transaction_id with default prefix."""
        transaction_id = generate_transaction_id()
        
        # Check that the transaction ID starts with the default prefix
        self.assertTrue(transaction_id.startswith('tx_'))
        
        # Check that the transaction ID has the expected format
        parts = transaction_id.split('_')
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], 'tx')
        
        # Check that the timestamp part has the expected length (YYYYMMDDhhmmss = 14 chars)
        self.assertEqual(len(parts[1]), 14)
        
        # Check that the unique part has the expected length (8 chars)
        self.assertEqual(len(parts[2]), 8)
    
    def test_generate_transaction_id_custom_prefix(self):
        """Test generate_transaction_id with custom prefix."""
        transaction_id = generate_transaction_id(prefix='test')
        
        # Check that the transaction ID starts with the custom prefix
        self.assertTrue(transaction_id.startswith('test_'))
        
        # Check that the transaction ID has the expected format
        parts = transaction_id.split('_')
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], 'test')
    
    def test_generate_transaction_id_uniqueness(self):
        """Test that generate_transaction_id returns unique IDs."""
        transaction_ids = [generate_transaction_id() for _ in range(10)]
        
        # Check that all transaction IDs are unique
        self.assertEqual(len(transaction_ids), len(set(transaction_ids)))


class HashSensitiveDataTests(TestCase):
    """Tests for hash_sensitive_data function."""
    
    def test_hash_sensitive_data(self):
        """Test hash_sensitive_data with valid input."""
        data = 'sensitive_data'
        hashed_data = hash_sensitive_data(data)
        
        # Check that the hashed data is a string
        self.assertIsInstance(hashed_data, str)
        
        # Check that the hashed data is not the same as the input
        self.assertNotEqual(hashed_data, data)
        
        # Check that the hashed data has the expected length (SHA-256 = 64 chars)
        self.assertEqual(len(hashed_data), 64)
        
        # Check that the same input always produces the same hash
        self.assertEqual(hashed_data, hash_sensitive_data(data))
    
    def test_hash_sensitive_data_empty_input(self):
        """Test hash_sensitive_data with empty input."""
        self.assertEqual(hash_sensitive_data(''), '')
    
    def test_hash_sensitive_data_none_input(self):
        """Test hash_sensitive_data with None input."""
        self.assertEqual(hash_sensitive_data(None), '')


class MaskCardNumberTests(TestCase):
    """Tests for mask_card_number function."""
    
    def test_mask_card_number(self):
        """Test mask_card_number with valid input."""
        card_number = '4111111111111111'
        masked_card_number = mask_card_number(card_number)
        
        # Check that the masked card number is a string
        self.assertIsInstance(masked_card_number, str)
        
        # Check that the masked card number has the expected format
        self.assertEqual(masked_card_number, '************1111')
        
        # Check that the masked card number has the same length as the input
        self.assertEqual(len(masked_card_number), len(card_number))
    
    def test_mask_card_number_short_input(self):
        """Test mask_card_number with short input."""
        card_number = '1234'
        masked_card_number = mask_card_number(card_number)
        
        # Check that the masked card number is the same as the input
        self.assertEqual(masked_card_number, card_number)
    
    def test_mask_card_number_empty_input(self):
        """Test mask_card_number with empty input."""
        self.assertEqual(mask_card_number(''), '')
    
    def test_mask_card_number_none_input(self):
        """Test mask_card_number with None input."""
        self.assertEqual(mask_card_number(None), None)


class CalculateDistanceTests(TestCase):
    """Tests for calculate_distance function."""
    
    def test_calculate_distance(self):
        """Test calculate_distance with valid input."""
        # New York City coordinates
        lat1, lon1 = 40.7128, -74.0060
        
        # Los Angeles coordinates
        lat2, lon2 = 34.0522, -118.2437
        
        distance = calculate_distance(lat1, lon1, lat2, lon2)
        
        # Check that the distance is a float
        self.assertIsInstance(distance, float)
        
        # Check that the distance is approximately correct (around 3935 km)
        self.assertAlmostEqual(distance, 3935, delta=10)
    
    def test_calculate_distance_same_point(self):
        """Test calculate_distance with same point."""
        lat, lon = 40.7128, -74.0060
        
        distance = calculate_distance(lat, lon, lat, lon)
        
        # Check that the distance is 0
        self.assertEqual(distance, 0)


class FormatJsonTests(TestCase):
    """Tests for format_json function."""
    
    def test_format_json(self):
        """Test format_json with valid input."""
        data = {'key': 'value', 'nested': {'key': 'value'}}
        formatted_json = format_json(data)
        
        # Check that the formatted JSON is a string
        self.assertIsInstance(formatted_json, str)
        
        # Check that the formatted JSON contains the expected data
        self.assertIn('"key": "value"', formatted_json)
        self.assertIn('"nested": {', formatted_json)
    
    def test_format_json_custom_indent(self):
        """Test format_json with custom indent."""
        data = {'key': 'value'}
        formatted_json = format_json(data, indent=4)
        
        # Check that the formatted JSON has the expected indentation
        self.assertIn('    "key"', formatted_json)


class ParseJsonTests(TestCase):
    """Tests for parse_json function."""
    
    def test_parse_json(self):
        """Test parse_json with valid input."""
        json_str = '{"key": "value", "nested": {"key": "value"}}'
        parsed_json = parse_json(json_str)
        
        # Check that the parsed JSON is a dictionary
        self.assertIsInstance(parsed_json, dict)
        
        # Check that the parsed JSON contains the expected data
        self.assertEqual(parsed_json['key'], 'value')
        self.assertEqual(parsed_json['nested']['key'], 'value')
    
    def test_parse_json_invalid_input(self):
        """Test parse_json with invalid input."""
        json_str = 'invalid_json'
        parsed_json = parse_json(json_str)
        
        # Check that the parsed JSON is None
        self.assertIsNone(parsed_json)
    
    def test_parse_json_none_input(self):
        """Test parse_json with None input."""
        self.assertIsNone(parse_json(None))