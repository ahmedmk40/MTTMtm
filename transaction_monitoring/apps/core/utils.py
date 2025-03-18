"""
Utility functions for Transaction Monitoring and Fraud Detection System.
"""

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from django.core.serializers.json import DjangoJSONEncoder


def generate_transaction_id(prefix: str = 'tx') -> str:
    """
    Generate a unique transaction ID.
    
    Args:
        prefix: Prefix for the transaction ID (default: 'tx')
        
    Returns:
        A unique transaction ID string
    """
    unique_id = str(uuid.uuid4()).replace('-', '')
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{prefix}_{timestamp}_{unique_id[:8]}"


def hash_sensitive_data(data: str) -> str:
    """
    Securely hash sensitive data using SHA-256.
    
    Args:
        data: The sensitive data to hash
        
    Returns:
        Hashed data string
    """
    if not data:
        return ''
    
    # Use SHA-256 for secure hashing
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def mask_card_number(card_number: str) -> str:
    """
    Mask a card number, showing only the last 4 digits.
    
    Args:
        card_number: The card number to mask
        
    Returns:
        Masked card number string
    """
    if not card_number or len(card_number) < 4:
        return card_number
    
    return f"{'*' * (len(card_number) - 4)}{card_number[-4:]}"


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the Haversine distance between two points in kilometers.
    
    Args:
        lat1: Latitude of the first point
        lon1: Longitude of the first point
        lat2: Latitude of the second point
        lon2: Longitude of the second point
        
    Returns:
        Distance in kilometers
    """
    import math
    
    # Convert latitude and longitude from degrees to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    
    return c * r


def format_json(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Format a dictionary as a JSON string.
    
    Args:
        data: Dictionary to format
        indent: Number of spaces for indentation
        
    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=indent, sort_keys=True)


def parse_json(json_str: str) -> Optional[Dict[str, Any]]:
    """
    Parse a JSON string into a dictionary.
    
    Args:
        json_str: JSON string to parse
        
    Returns:
        Dictionary or None if parsing fails
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None


class CustomJSONEncoder(DjangoJSONEncoder):
    """
    Custom JSON encoder that handles additional types like booleans.
    """
    def default(self, obj):
        if isinstance(obj, bool):
            return str(obj).lower()  # Convert boolean to string
        return super().default(obj)