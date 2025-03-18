"""
Geographic rules for the Rule Engine.
"""

from ..models import Rule
from apps.core.constants import HIGH_RISK_COUNTRIES


# Example geographic rules
GEOGRAPHIC_RULES = [
    {
        'name': 'High Risk Country Transaction',
        'description': 'Flag transactions from high-risk countries',
        'rule_type': 'location',
        'condition': f'transaction.get("location_data", {{}}).get("country") in {HIGH_RISK_COUNTRIES}',
        'action': 'review',
        'risk_score': 75.0,
        'priority': 85,
    },
    {
        'name': 'IP Mismatch with Country',
        'description': 'Flag transactions where IP country differs from location country',
        'rule_type': 'location',
        'condition': 'transaction.get("location_data", {}).get("country") != transaction.get("location_data", {}).get("ip_country", transaction.get("location_data", {}).get("country"))',
        'action': 'review',
        'risk_score': 70.0,
        'priority': 80,
    },
    {
        'name': 'Cross-Border Transaction',
        'description': 'Flag transactions where user country differs from merchant country',
        'rule_type': 'location',
        'condition': 'transaction.get("location_data", {}).get("country") != transaction.get("merchant_location", {}).get("country", transaction.get("location_data", {}).get("country"))',
        'action': 'review',
        'risk_score': 60.0,
        'priority': 70,
    },
]


def create_geographic_rules(created_by='system'):
    """
    Create geographic rules in the database.
    
    Args:
        created_by: Username of the creator
    """
    for rule_data in GEOGRAPHIC_RULES:
        Rule.objects.get_or_create(
            name=rule_data['name'],
            defaults={
                'description': rule_data['description'],
                'rule_type': rule_data['rule_type'],
                'condition': rule_data['condition'],
                'action': rule_data['action'],
                'risk_score': rule_data['risk_score'],
                'priority': rule_data['priority'],
                'created_by': created_by,
            }
        )