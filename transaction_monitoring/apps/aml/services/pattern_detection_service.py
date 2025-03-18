"""
Pattern detection service for AML monitoring.

This service is responsible for detecting complex AML patterns across multiple transactions.
"""

import logging
from typing import Dict, Any, List
from django.utils import timezone
from django.db.models import Sum, Count, Q, F
from datetime import timedelta
from apps.transactions.models import Transaction
from apps.aml.models import TransactionPattern

logger = logging.getLogger(__name__)


def detect_round_amount_patterns(user_id: str, time_window_days: int = 30) -> Dict[str, Any]:
    """
    Detect patterns of round amount transactions for a user.
    
    Args:
        user_id: The user ID to check
        time_window_days: Time window in days to look back
        
    Returns:
        Dictionary with detection results
    """
    # Calculate time window
    start_date = timezone.now() - timedelta(days=time_window_days)
    
    # Find round amount transactions
    round_amount_transactions = Transaction.objects.filter(
        user_id=user_id,
        timestamp__gte=start_date,
        amount__gte=1000
    ).extra(
        where=["amount % 1000 = 0"]
    )
    
    # Calculate total
    total_amount = round_amount_transactions.aggregate(total=Sum('amount'))['total'] or 0
    transaction_count = round_amount_transactions.count()
    
    # Determine if this is suspicious
    is_suspicious = total_amount >= 10000 and transaction_count >= 3
    
    # Create or update pattern
    if is_suspicious:
        pattern, created = TransactionPattern.objects.update_or_create(
            user_id=user_id,
            pattern_type='round_amount_transactions',
            defaults={
                'description': f"User made {transaction_count} round-amount transactions totaling {total_amount} in the last {time_window_days} days",
                'risk_score': min(85 + (transaction_count * 2), 100),  # Increase risk with more transactions
                'transaction_count': transaction_count,
                'total_amount': total_amount,
                'time_window': f"{time_window_days} days",
                'is_active': True,
                'last_detected': timezone.now()
            }
        )
        
        logger.info(f"{'Created' if created else 'Updated'} round amount pattern for user {user_id}: {transaction_count} transactions, {total_amount} total")
    
    return {
        'user_id': user_id,
        'pattern_type': 'round_amount_transactions',
        'transaction_count': transaction_count,
        'total_amount': total_amount,
        'is_suspicious': is_suspicious
    }


def detect_round_transfers_patterns(user_id: str, time_window_days: int = 30) -> Dict[str, Any]:
    """
    Detect patterns of round number transfers for a user.
    
    Args:
        user_id: The user ID to check
        time_window_days: Time window in days to look back
        
    Returns:
        Dictionary with detection results
    """
    # Calculate time window
    start_date = timezone.now() - timedelta(days=time_window_days)
    
    # Find round number transfers
    round_transfers = Transaction.objects.filter(
        user_id=user_id,
        timestamp__gte=start_date,
        channel='wallet',
        transaction_type='wallet',
        amount__gte=500
    ).extra(
        where=["amount % 100 = 0"]
    )
    
    # Calculate total
    total_amount = round_transfers.aggregate(total=Sum('amount'))['total'] or 0
    transfer_count = round_transfers.count()
    
    # Determine if this is suspicious
    is_suspicious = total_amount >= 5000 and transfer_count >= 3
    
    # Create or update pattern
    if is_suspicious:
        pattern, created = TransactionPattern.objects.update_or_create(
            user_id=user_id,
            pattern_type='round_number_transfers',
            defaults={
                'description': f"User made {transfer_count} round-number transfers totaling {total_amount} in the last {time_window_days} days",
                'risk_score': min(80 + (transfer_count * 2), 100),  # Increase risk with more transfers
                'transaction_count': transfer_count,
                'total_amount': total_amount,
                'time_window': f"{time_window_days} days",
                'is_active': True,
                'last_detected': timezone.now()
            }
        )
        
        logger.info(f"{'Created' if created else 'Updated'} round transfer pattern for user {user_id}: {transfer_count} transfers, {total_amount} total")
    
    return {
        'user_id': user_id,
        'pattern_type': 'round_number_transfers',
        'transfer_count': transfer_count,
        'total_amount': total_amount,
        'is_suspicious': is_suspicious
    }


def detect_identical_amount_patterns(merchant_id: str, time_window_days: int = 30) -> Dict[str, Any]:
    """
    Detect patterns of multiple accounts sending identical amounts to the same merchant.
    
    Args:
        merchant_id: The merchant ID to check
        time_window_days: Time window in days to look back
        
    Returns:
        Dictionary with detection results
    """
    # Calculate time window
    start_date = timezone.now() - timedelta(days=time_window_days)
    
    # Find transactions with identical amounts from different users
    transactions = Transaction.objects.filter(
        merchant_id=merchant_id,
        timestamp__gte=start_date,
        amount__gte=1000
    )
    
    # Group by amount and count distinct users
    amount_groups = transactions.values('amount').annotate(
        user_count=Count('user_id', distinct=True),
        tx_count=Count('id')
    ).filter(user_count__gte=2)  # At least 2 different users
    
    # Process suspicious patterns
    suspicious_patterns = []
    
    for group in amount_groups:
        amount = group['amount']
        user_count = group['user_count']
        tx_count = group['tx_count']
        
        # Get the users involved
        users = transactions.filter(amount=amount).values_list('user_id', flat=True).distinct()
        
        pattern = {
            'amount': amount,
            'user_count': user_count,
            'transaction_count': tx_count,
            'users': list(users)[:10]  # Limit to first 10 users
        }
        
        suspicious_patterns.append(pattern)
        
        # Create or update pattern in database
        pattern_desc = f"{user_count} users sent identical amounts of {amount} to merchant {merchant_id} in the last {time_window_days} days"
        risk_score = min(75 + (user_count * 5), 100)  # Increase risk with more users
        
        TransactionPattern.objects.update_or_create(
            merchant_id=merchant_id,
            pattern_type='identical_amount_transfers',
            amount=amount,
            defaults={
                'description': pattern_desc,
                'risk_score': risk_score,
                'transaction_count': tx_count,
                'total_amount': amount * tx_count,
                'time_window': f"{time_window_days} days",
                'is_active': True,
                'last_detected': timezone.now(),
                'metadata': {'users': list(users)[:20]}  # Store up to 20 users
            }
        )
        
        logger.info(f"Detected identical amount pattern for merchant {merchant_id}: {pattern_desc}")
    
    return {
        'merchant_id': merchant_id,
        'pattern_type': 'identical_amount_transfers',
        'pattern_count': len(suspicious_patterns),
        'patterns': suspicious_patterns,
        'is_suspicious': len(suspicious_patterns) > 0
    }


def detect_multiple_transactions_between_accounts(user_id: str, time_window_days: int = 30) -> Dict[str, Any]:
    """
    Detect patterns of multiple transactions between the same two accounts.
    
    Args:
        user_id: The user ID to check
        time_window_days: Time window in days to look back
        
    Returns:
        Dictionary with detection results
    """
    # Calculate time window
    start_date = timezone.now() - timedelta(days=time_window_days)
    
    # Find wallet transactions for this user
    transactions = Transaction.objects.filter(
        Q(user_id=user_id) | Q(merchant_id=user_id),
        timestamp__gte=start_date,
        channel='wallet',
        transaction_type='wallet'
    )
    
    # Group by the other party (user_id or merchant_id)
    user_sent = transactions.filter(user_id=user_id).values('merchant_id').annotate(
        tx_count=Count('id'),
        total_amount=Sum('amount')
    ).filter(tx_count__gte=3)  # At least 3 transactions
    
    user_received = transactions.filter(merchant_id=user_id).values('user_id').annotate(
        tx_count=Count('id'),
        total_amount=Sum('amount')
    ).filter(tx_count__gte=3)  # At least 3 transactions
    
    # Combine results
    suspicious_patterns = []
    
    for group in user_sent:
        other_id = group['merchant_id']
        tx_count = group['tx_count']
        total_amount = group['total_amount']
        
        suspicious_patterns.append({
            'other_id': other_id,
            'direction': 'sent',
            'transaction_count': tx_count,
            'total_amount': total_amount
        })
    
    for group in user_received:
        other_id = group['user_id']
        tx_count = group['tx_count']
        total_amount = group['total_amount']
        
        suspicious_patterns.append({
            'other_id': other_id,
            'direction': 'received',
            'transaction_count': tx_count,
            'total_amount': total_amount
        })
    
    # Create or update patterns in database
    for pattern in suspicious_patterns:
        other_id = pattern['other_id']
        direction = pattern['direction']
        tx_count = pattern['transaction_count']
        total_amount = pattern['total_amount']
        
        pattern_desc = f"User {user_id} {direction} {tx_count} transactions totaling {total_amount} {'to' if direction == 'sent' else 'from'} {other_id} in the last {time_window_days} days"
        risk_score = min(70 + (tx_count * 3), 100)  # Increase risk with more transactions
        
        TransactionPattern.objects.update_or_create(
            user_id=user_id,
            related_user_id=other_id,
            pattern_type='multiple_transactions_between_accounts',
            defaults={
                'description': pattern_desc,
                'risk_score': risk_score,
                'transaction_count': tx_count,
                'total_amount': total_amount,
                'time_window': f"{time_window_days} days",
                'is_active': True,
                'last_detected': timezone.now(),
                'metadata': {
                    'direction': direction,
                    'other_id': other_id
                }
            }
        )
        
        logger.info(f"Detected multiple transactions pattern: {pattern_desc}")
    
    return {
        'user_id': user_id,
        'pattern_type': 'multiple_transactions_between_accounts',
        'pattern_count': len(suspicious_patterns),
        'patterns': suspicious_patterns,
        'is_suspicious': len(suspicious_patterns) > 0
    }


def detect_sequential_account_generation(ip_address: str = None, device_id: str = None, time_window_hours: int = 24) -> Dict[str, Any]:
    """
    Detect sequential account generation patterns.
    
    Args:
        ip_address: The IP address to check
        device_id: The device ID to check
        time_window_hours: Time window in hours to look back
        
    Returns:
        Dictionary with detection results
    """
    from django.db import connection
    from apps.accounts.models import User
    from datetime import timedelta
    
    # Calculate time window
    start_date = timezone.now() - timedelta(hours=time_window_hours)
    
    # Initialize result
    result = {
        'is_suspicious': False,
        'account_count': 0,
        'sequential_patterns': [],
        'common_attributes': {}
    }
    
    # Find accounts created from the same IP or device
    filters = {}
    if ip_address:
        filters['last_login_ip'] = ip_address
    if device_id:
        filters['last_login_device_id'] = device_id
    
    if not filters:
        return result
    
    # Find recently created accounts with the same IP or device
    recent_accounts = User.objects.filter(
        date_joined__gte=start_date,
        **filters
    ).order_by('date_joined')
    
    account_count = recent_accounts.count()
    
    # If we have at least 3 accounts, check for sequential patterns
    if account_count >= 3:
        # Extract usernames and user IDs for pattern analysis
        usernames = list(recent_accounts.values_list('username', flat=True))
        user_ids = list(recent_accounts.values_list('id', flat=True))
        emails = list(recent_accounts.values_list('email', flat=True))
        
        # Check for sequential numeric patterns in usernames
        numeric_pattern = detect_numeric_sequence(usernames)
        if numeric_pattern['is_sequential']:
            result['sequential_patterns'].append({
                'type': 'username_numeric',
                'description': f"Sequential numeric pattern in usernames: {', '.join(numeric_pattern['examples'][:5])}",
                'count': numeric_pattern['count']
            })
            result['is_suspicious'] = True
        
        # Check for sequential numeric patterns in user IDs
        id_pattern = detect_numeric_sequence([str(uid) for uid in user_ids])
        if id_pattern['is_sequential']:
            result['sequential_patterns'].append({
                'type': 'user_id_numeric',
                'description': f"Sequential numeric pattern in user IDs: {', '.join(id_pattern['examples'][:5])}",
                'count': id_pattern['count']
            })
            result['is_suspicious'] = True
        
        # Check for email patterns (same domain or similar usernames)
        email_pattern = detect_email_pattern(emails)
        if email_pattern['is_pattern']:
            result['sequential_patterns'].append({
                'type': 'email_pattern',
                'description': f"Pattern detected in email addresses: {email_pattern['pattern_description']}",
                'count': email_pattern['count']
            })
            result['is_suspicious'] = True
        
        # Record common attributes
        if ip_address:
            result['common_attributes']['ip_address'] = ip_address
            result['common_attributes']['ip_account_count'] = account_count
        
        if device_id:
            result['common_attributes']['device_id'] = device_id
            result['common_attributes']['device_account_count'] = account_count
        
        # Set account count
        result['account_count'] = account_count
        
        # If we have a high number of accounts, it's suspicious regardless of patterns
        if account_count >= 5:
            result['is_suspicious'] = True
            if not result['sequential_patterns']:
                result['sequential_patterns'].append({
                    'type': 'high_volume',
                    'description': f"High volume of accounts ({account_count}) created from same source",
                    'count': account_count
                })
        
        # Create or update pattern in database if suspicious
        if result['is_suspicious']:
            # Use the first account as a reference
            reference_account = recent_accounts.first()
            
            # Create pattern description
            pattern_desc = f"{account_count} accounts created within {time_window_hours} hours"
            if result['sequential_patterns']:
                pattern_types = [p['type'] for p in result['sequential_patterns']]
                pattern_desc += f" with patterns: {', '.join(pattern_types)}"
            
            # Calculate risk score based on account count and pattern types
            base_risk = 75
            risk_score = min(base_risk + (account_count * 3), 100)
            
            # Add extra risk for certain pattern types
            if any(p['type'] == 'username_numeric' for p in result['sequential_patterns']):
                risk_score = min(risk_score + 10, 100)
            
            if any(p['type'] == 'email_pattern' for p in result['sequential_patterns']):
                risk_score = min(risk_score + 5, 100)
            
            # Create or update the pattern
            TransactionPattern.objects.update_or_create(
                user_id=reference_account.id,
                pattern_type='sequential_account_generation',
                defaults={
                    'description': pattern_desc,
                    'risk_score': risk_score,
                    'transaction_count': account_count,
                    'time_window': f"{time_window_hours} hours",
                    'is_active': True,
                    'is_suspicious': True,
                    'last_detected': timezone.now(),
                    'metadata': {
                        'ip_address': ip_address,
                        'device_id': device_id,
                        'account_count': account_count,
                        'sequential_patterns': result['sequential_patterns'],
                        'accounts': [
                            {
                                'id': account.id,
                                'username': account.username,
                                'email': account.email,
                                'date_joined': account.date_joined.isoformat()
                            } 
                            for account in recent_accounts[:20]  # Limit to 20 accounts
                        ]
                    }
                }
            )
    
    return result


def detect_numeric_sequence(values: List[str]) -> Dict[str, Any]:
    """
    Detect numeric sequences in a list of values.
    
    Args:
        values: List of string values to check
        
    Returns:
        Dictionary with detection results
    """
    import re
    
    result = {
        'is_sequential': False,
        'count': 0,
        'examples': []
    }
    
    # Extract numeric parts from values
    numeric_parts = []
    for value in values:
        # Find all numeric sequences in the value
        matches = re.findall(r'\d+', value)
        if matches:
            numeric_parts.append((value, matches[-1]))  # Use the last numeric part
    
    if len(numeric_parts) < 3:
        return result
    
    # Check for sequential numbers
    sequential_count = 0
    sequential_examples = []
    
    # Sort by numeric part
    sorted_parts = sorted(numeric_parts, key=lambda x: int(x[1]))
    
    # Check for sequences
    for i in range(1, len(sorted_parts)):
        prev_num = int(sorted_parts[i-1][1])
        curr_num = int(sorted_parts[i][1])
        
        if curr_num == prev_num + 1:
            sequential_count += 1
            if sorted_parts[i-1][0] not in sequential_examples:
                sequential_examples.append(sorted_parts[i-1][0])
            if sorted_parts[i][0] not in sequential_examples:
                sequential_examples.append(sorted_parts[i][0])
    
    # If we have at least 2 sequential pairs (3 sequential values)
    if sequential_count >= 2:
        result['is_sequential'] = True
        result['count'] = sequential_count + 1  # +1 because we count pairs
        result['examples'] = sequential_examples
    
    return result


def detect_email_pattern(emails: List[str]) -> Dict[str, Any]:
    """
    Detect patterns in email addresses.
    
    Args:
        emails: List of email addresses
        
    Returns:
        Dictionary with detection results
    """
    result = {
        'is_pattern': False,
        'pattern_description': '',
        'count': 0,
        'examples': []
    }
    
    if len(emails) < 3:
        return result
    
    # Check for common domains
    domains = {}
    for email in emails:
        if '@' in email:
            domain = email.split('@')[1]
            domains[domain] = domains.get(domain, 0) + 1
    
    # Find domains used multiple times
    common_domains = [(domain, count) for domain, count in domains.items() if count >= 3]
    
    if common_domains:
        most_common = max(common_domains, key=lambda x: x[1])
        result['is_pattern'] = True
        result['pattern_description'] = f"{most_common[1]} accounts using domain {most_common[0]}"
        result['count'] = most_common[1]
        
        # Add examples
        for email in emails:
            if email.endswith('@' + most_common[0]) and len(result['examples']) < 5:
                result['examples'].append(email)
    
    # Check for similar usernames with different domains
    usernames = {}
    for email in emails:
        if '@' in email:
            username = email.split('@')[0]
            usernames[username] = usernames.get(username, 0) + 1
    
    # Find username patterns
    import re
    username_patterns = {}
    
    for username in usernames.keys():
        # Look for patterns like name1, name2, name3
        match = re.match(r'([a-zA-Z]+)(\d+)', username)
        if match:
            base_name = match.group(1)
            username_patterns[base_name] = username_patterns.get(base_name, 0) + 1
    
    # Find patterns used multiple times
    common_patterns = [(pattern, count) for pattern, count in username_patterns.items() if count >= 3]
    
    if common_patterns:
        most_common = max(common_patterns, key=lambda x: x[1])
        result['is_pattern'] = True
        if result['pattern_description']:
            result['pattern_description'] += f" and {most_common[1]} accounts with username pattern '{most_common[0]}X'"
        else:
            result['pattern_description'] = f"{most_common[1]} accounts with username pattern '{most_common[0]}X'"
        result['count'] = max(result['count'], most_common[1])
        
        # Add examples
        pattern_regex = re.compile(f"^{most_common[0]}\\d+")
        for email in emails:
            if '@' in email:
                username = email.split('@')[0]
                if pattern_regex.match(username) and len(result['examples']) < 5:
                    result['examples'].append(email)
    
    return result


def check_aml_patterns(transaction) -> Dict[str, Any]:
    """
    Check for AML patterns after a transaction is processed.
    
    Args:
        transaction: The transaction object
        
    Returns:
        Dictionary with the pattern detection results
    """
    user_id = transaction.user_id
    merchant_id = getattr(transaction, 'merchant_id', None)
    
    results = {
        'patterns_detected': [],
        'risk_score': 0.0,
    }
    
    # Check for round amount patterns
    round_amount_result = detect_round_amount_patterns(user_id)
    if round_amount_result['is_suspicious']:
        results['patterns_detected'].append({
            'pattern_type': 'round_amount_transactions',
            'description': f"User made {round_amount_result['transaction_count']} round-amount transactions totaling {round_amount_result['total_amount']}",
            'risk_score': min(85 + (round_amount_result['transaction_count'] * 2), 100)
        })
    
    # Check for round transfers patterns
    if transaction.channel == 'wallet':
        round_transfers_result = detect_round_transfers_patterns(user_id)
        if round_transfers_result['is_suspicious']:
            results['patterns_detected'].append({
                'pattern_type': 'round_number_transfers',
                'description': f"User made {round_transfers_result['transfer_count']} round-number transfers totaling {round_transfers_result['total_amount']}",
                'risk_score': min(80 + (round_transfers_result['transfer_count'] * 2), 100)
            })
    
    # Check for identical amount patterns
    if merchant_id:
        identical_amount_result = detect_identical_amount_patterns(merchant_id)
        if identical_amount_result['is_suspicious']:
            for pattern in identical_amount_result['patterns'][:3]:  # Limit to first 3 patterns
                results['patterns_detected'].append({
                    'pattern_type': 'identical_amount_transfers',
                    'description': f"{pattern['user_count']} users sent identical amounts of {pattern['amount']} to merchant {merchant_id}",
                    'risk_score': min(75 + (pattern['user_count'] * 5), 100)
                })
    
    # Check for multiple transactions between accounts
    multiple_tx_result = detect_multiple_transactions_between_accounts(user_id)
    if multiple_tx_result['is_suspicious']:
        for pattern in multiple_tx_result['patterns'][:3]:  # Limit to first 3 patterns
            results['patterns_detected'].append({
                'pattern_type': 'multiple_transactions_between_accounts',
                'description': f"User {user_id} {pattern['direction']} {pattern['transaction_count']} transactions totaling {pattern['total_amount']} {'to' if pattern['direction'] == 'sent' else 'from'} {pattern['other_id']}",
                'risk_score': min(70 + (pattern['transaction_count'] * 3), 100)
            })
    
    # Check for sequential account generation
    # We can only do this if we have IP or device information
    ip_address = None
    device_id = None
    
    if hasattr(transaction, 'location_data') and transaction.location_data:
        ip_address = transaction.location_data.get('ip_address')
    
    if hasattr(transaction, 'device_id'):
        device_id = transaction.device_id
    
    if ip_address or device_id:
        seq_account_result = detect_sequential_account_generation(ip_address, device_id)
        if seq_account_result['is_suspicious']:
            for pattern in seq_account_result.get('sequential_patterns', [])[:2]:  # Limit to first 2 patterns
                results['patterns_detected'].append({
                    'pattern_type': 'sequential_account_generation',
                    'description': f"Sequential account generation detected: {pattern['description']}",
                    'risk_score': min(90 + (seq_account_result['account_count'] * 2), 100)
                })
    
    # Calculate overall risk score (max of all pattern risk scores)
    if results['patterns_detected']:
        results['risk_score'] = max(pattern['risk_score'] for pattern in results['patterns_detected'])
    
    return results