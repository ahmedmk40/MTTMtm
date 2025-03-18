"""
Amount-based rules for the Rule Engine.
"""

from ..models import Rule


# Example amount rules
AMOUNT_RULES = [
    {
        'name': 'High Amount Transaction',
        'description': 'Flag transactions with unusually high amounts',
        'rule_type': 'amount',
        'condition': 'transaction["amount"] > 5000',
        'action': 'review',
        'risk_score': 70.0,
        'priority': 80,
    },
    {
        'name': 'Very High Amount Transaction',
        'description': 'Reject transactions with extremely high amounts',
        'rule_type': 'amount',
        'condition': 'transaction["amount"] > 10000',
        'action': 'reject',
        'risk_score': 90.0,
        'priority': 90,
    },
    {
        'name': 'Round Amount Transaction',
        'description': 'Flag transactions with suspiciously round amounts',
        'rule_type': 'amount',
        'condition': 'transaction["amount"] % 1000 == 0 and transaction["amount"] >= 1000',
        'action': 'review',
        'risk_score': 60.0,
        'priority': 70,
    },
    {
        'name': 'Just Below Threshold Transaction',
        'description': 'Flag transactions just below common reporting thresholds',
        'rule_type': 'amount',
        'condition': '(transaction["amount"] >= 9000 and transaction["amount"] < 10000) or (transaction["amount"] >= 4500 and transaction["amount"] < 5000)',
        'action': 'review',
        'risk_score': 65.0,
        'priority': 75,
    },
]


def create_amount_rules(created_by='system'):
    """
    Create amount rules in the database.
    
    Args:
        created_by: Username of the creator
    """
    for rule_data in AMOUNT_RULES:
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