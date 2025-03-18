"""
Anti-Money Laundering (AML) rules for the Rule Engine.
"""

from ..models import Rule


# Example AML rules
AML_RULES = [
    {
        'name': 'Structuring Detection',
        'description': 'Flag potential structuring activity (multiple transactions just below reporting thresholds)',
        'rule_type': 'aml',
        'condition': 'transaction["amount"] >= 9000 and transaction["amount"] < 10000',
        'action': 'review',
        'risk_score': 80.0,
        'priority': 90,
    },
    {
        'name': 'Rapid Fund Movement',
        'description': 'Flag rapid movement of funds through accounts',
        'rule_type': 'aml',
        'condition': 'transaction.get("channel") == "wallet" and transaction.get("transaction_purpose") in ["transfer", "withdrawal"] and transaction["amount"] > 5000',
        'action': 'review',
        'risk_score': 75.0,
        'priority': 85,
    },
    {
        'name': 'High-Risk Jurisdiction Transfer',
        'description': 'Flag transfers to/from high-risk jurisdictions',
        'rule_type': 'aml',
        'condition': 'transaction.get("channel") == "wallet" and transaction.get("destination_type") == "external" and transaction["amount"] > 1000',
        'action': 'review',
        'risk_score': 70.0,
        'priority': 80,
    },
    {
        'name': 'Round Amount Transfers',
        'description': 'Flag suspiciously round amount transfers',
        'rule_type': 'aml',
        'condition': 'transaction.get("channel") == "wallet" and transaction["amount"] % 1000 == 0 and transaction["amount"] >= 3000',
        'action': 'review',
        'risk_score': 65.0,
        'priority': 75,
    },
    {
        'name': 'Multiple Same-Day Transfers',
        'description': 'Flag multiple transfers on the same day',
        'rule_type': 'aml',
        'condition': 'transaction.get("channel") == "wallet" and transaction.get("transaction_purpose") == "transfer" and transaction["amount"] > 1000',
        'action': 'notify',
        'risk_score': 60.0,
        'priority': 70,
    },
    # New AML rules
    {
        'name': 'High Cumulative Round-Amount Transactions',
        'description': 'Flag users with high cumulative value of round-amount transactions',
        'rule_type': 'aml',
        'condition': 'transaction["amount"] % 1000 == 0 and transaction["amount"] >= 1000',
        'action': 'review',
        'risk_score': 85.0,
        'priority': 88,
    },
    {
        'name': 'High Cumulative Round-Number Transfers',
        'description': 'Flag users with high cumulative total of round-number transfers',
        'rule_type': 'aml',
        'condition': 'transaction.get("channel") == "wallet" and transaction.get("transaction_purpose") == "transfer" and transaction["amount"] % 100 == 0 and transaction["amount"] >= 500',
        'action': 'review',
        'risk_score': 82.0,
        'priority': 86,
    },
    {
        'name': 'Multiple Accounts Sending Identical Amounts',
        'description': 'Flag when 2+ accounts send identical amounts to the same recipient',
        'rule_type': 'aml',
        'condition': 'transaction.get("channel") == "wallet" and transaction.get("transaction_purpose") == "transfer" and transaction["amount"] >= 1000',
        'action': 'review',
        'risk_score': 88.0,
        'priority': 89,
    },
    {
        'name': 'Multiple Transactions Between Two Accounts',
        'description': 'Flag when there are 3+ transactions between the same two accounts',
        'rule_type': 'aml',
        'condition': 'transaction.get("channel") == "wallet" and transaction.get("transaction_purpose") == "transfer"',
        'action': 'review',
        'risk_score': 78.0,
        'priority': 82,
    },
    {
        'name': 'Sequential Account Generation Attack',
        'description': 'Flag transactions from accounts that appear to be part of a sequential generation pattern',
        'rule_type': 'aml',
        'condition': 'transaction.get("metadata", {}).get("account_age_days", 30) < 7',  # New accounts less than 7 days old
        'action': 'review',
        'risk_score': 90.0,
        'priority': 92,
    },
]


def create_aml_rules(created_by='system'):
    """
    Create AML rules in the database.
    
    Args:
        created_by: Username of the creator
    """
    for rule_data in AML_RULES:
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