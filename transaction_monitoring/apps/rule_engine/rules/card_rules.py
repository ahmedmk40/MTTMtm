"""
Card-related rules for the Rule Engine.
"""

from ..models import Rule


# Example card rules
CARD_RULES = [
    {
        'name': 'New Card High Amount',
        'description': 'Flag high amount transactions with a new card',
        'rule_type': 'card',
        'condition': 'transaction.get("payment_method_data", {}).get("card_details", {}).get("is_new", False) and transaction["amount"] > 1000',
        'action': 'review',
        'risk_score': 75.0,
        'priority': 85,
    },
    {
        'name': 'Manual Card Entry',
        'description': 'Flag transactions with manually entered card details',
        'rule_type': 'card',
        'condition': 'transaction.get("channel") == "pos" and transaction.get("entry_mode") == "manual"',
        'action': 'review',
        'risk_score': 70.0,
        'priority': 80,
    },
    {
        'name': 'Card Not Present High Amount',
        'description': 'Flag high amount card-not-present transactions',
        'rule_type': 'card',
        'condition': 'transaction.get("channel") == "pos" and transaction.get("condition") == "card_not_present" and transaction["amount"] > 500',
        'action': 'review',
        'risk_score': 65.0,
        'priority': 75,
    },
    {
        'name': 'E-commerce Without 3DS',
        'description': 'Flag e-commerce transactions without 3DS verification',
        'rule_type': 'card',
        'condition': 'transaction.get("channel") == "ecommerce" and not transaction.get("is_3ds_verified", False) and transaction["amount"] > 200',
        'action': 'review',
        'risk_score': 60.0,
        'priority': 70,
    },
    {
        'name': 'Billing/Shipping Address Mismatch',
        'description': 'Flag e-commerce transactions with mismatched billing and shipping addresses',
        'rule_type': 'card',
        'condition': 'transaction.get("channel") == "ecommerce" and not transaction.get("is_billing_shipping_match", True) and transaction["amount"] > 100',
        'action': 'review',
        'risk_score': 65.0,
        'priority': 75,
    },
]


def create_card_rules(created_by='system'):
    """
    Create card rules in the database.
    
    Args:
        created_by: Username of the creator
    """
    for rule_data in CARD_RULES:
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