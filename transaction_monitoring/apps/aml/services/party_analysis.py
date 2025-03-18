"""
Party connection analysis service for the AML app.

This service is responsible for analyzing connections between transaction parties.
"""

import logging
import networkx as nx
from typing import Dict, Any, List, Set, Tuple
from django.db.models import Q
from apps.transactions.models import Transaction, WalletTransaction

logger = logging.getLogger(__name__)


def analyze_party_connections(user_id: str) -> Dict[str, Any]:
    """
    Analyze connections between transaction parties for a user.
    
    Args:
        user_id: The user ID to analyze
        
    Returns:
        Dictionary with the party connection analysis result
    """
    # Initialize result
    result = {
        'connection_score': 0.0,
        'connected_parties': [],
        'common_attributes': [],
        'transaction_patterns': [],
    }
    
    try:
        # Get transactions for the user (last 90 days)
        from django.utils import timezone
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=90)
        
        transactions = Transaction.objects.filter(
            user_id=user_id,
            timestamp__gte=start_date
        )
        
        if not transactions.exists():
            return result
        
        # Build party graph
        G = build_party_graph(transactions)
        
        # Find connected parties
        connected_parties = find_connected_parties(G, user_id)
        result['connected_parties'] = connected_parties
        
        # Find common attributes
        common_attributes = find_common_attributes(transactions, connected_parties)
        result['common_attributes'] = common_attributes
        
        # Find transaction patterns
        transaction_patterns = find_transaction_patterns(transactions, connected_parties)
        result['transaction_patterns'] = transaction_patterns
        
        # Calculate connection score
        connection_score = calculate_connection_score(
            connected_parties,
            common_attributes,
            transaction_patterns
        )
        result['connection_score'] = connection_score
        
        logger.info(
            f"Party connection analysis for user {user_id}: "
            f"connection_score={result['connection_score']:.2f}, "
            f"connected_parties={len(result['connected_parties'])}, "
            f"common_attributes={len(result['common_attributes'])}, "
            f"transaction_patterns={len(result['transaction_patterns'])}"
        )
    
    except Exception as e:
        logger.error(f"Error analyzing party connections for user {user_id}: {str(e)}", exc_info=True)
    
    return result


def build_party_graph(transactions) -> nx.Graph:
    """
    Build an undirected graph of transaction parties.
    
    Args:
        transactions: QuerySet of transactions
        
    Returns:
        NetworkX Graph of transaction parties
    """
    # Create undirected graph
    G = nx.Graph()
    
    # Add nodes and edges to the graph
    for tx in transactions:
        # Add user node
        if not G.has_node(tx.user_id):
            G.add_node(tx.user_id, type='user')
        
        # Add merchant node if applicable
        if hasattr(tx, 'merchant_id') and tx.merchant_id:
            if not G.has_node(tx.merchant_id):
                G.add_node(tx.merchant_id, type='merchant')
            
            # Add edge between user and merchant
            G.add_edge(
                tx.user_id,
                tx.merchant_id,
                transaction_ids=[tx.transaction_id],
                count=1
            )
        
        # Add wallet transaction connections if applicable
        if isinstance(tx, WalletTransaction):
            # Add source and destination nodes
            source = f"{tx.source_type}:{tx.source_id}"
            destination = f"{tx.destination_type}:{tx.destination_id}"
            
            if not G.has_node(source):
                G.add_node(source, type=tx.source_type)
            
            if not G.has_node(destination):
                G.add_node(destination, type=tx.destination_type)
            
            # Add edges
            if source != tx.user_id:
                if G.has_edge(tx.user_id, source):
                    G[tx.user_id][source]['count'] += 1
                    G[tx.user_id][source]['transaction_ids'].append(tx.transaction_id)
                else:
                    G.add_edge(
                        tx.user_id,
                        source,
                        transaction_ids=[tx.transaction_id],
                        count=1
                    )
            
            if destination != tx.user_id:
                if G.has_edge(tx.user_id, destination):
                    G[tx.user_id][destination]['count'] += 1
                    G[tx.user_id][destination]['transaction_ids'].append(tx.transaction_id)
                else:
                    G.add_edge(
                        tx.user_id,
                        destination,
                        transaction_ids=[tx.transaction_id],
                        count=1
                    )
    
    return G


def find_connected_parties(G: nx.Graph, user_id: str) -> List[Dict[str, Any]]:
    """
    Find parties connected to a user.
    
    Args:
        G: NetworkX Graph of transaction parties
        user_id: The user ID to analyze
        
    Returns:
        List of connected parties
    """
    connected_parties = []
    
    # Get neighbors of the user
    if G.has_node(user_id):
        neighbors = list(G.neighbors(user_id))
        
        for neighbor in neighbors:
            edge_data = G.get_edge_data(user_id, neighbor)
            
            connected_parties.append({
                'party_id': neighbor,
                'type': G.nodes[neighbor].get('type', 'unknown'),
                'transaction_count': edge_data['count'],
                'transaction_ids': edge_data['transaction_ids'],
            })
    
    return connected_parties


def find_common_attributes(transactions, connected_parties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Find common attributes between a user and connected parties.
    
    Args:
        transactions: QuerySet of transactions
        connected_parties: List of connected parties
        
    Returns:
        List of common attributes
    """
    common_attributes = []
    
    # Extract party IDs
    party_ids = [party['party_id'] for party in connected_parties]
    
    # Check for common IP addresses
    ip_addresses = set()
    for tx in transactions:
        if hasattr(tx, 'location_data') and tx.location_data:
            ip = tx.location_data.get('ip_address')
            if ip:
                ip_addresses.add(ip)
    
    if ip_addresses:
        # Check if any other transactions from connected parties use the same IPs
        common_ip_transactions = Transaction.objects.filter(
            ~Q(user_id=transactions[0].user_id),
            user_id__in=party_ids
        ).filter(
            location_data__ip_address__in=list(ip_addresses)
        )
        
        if common_ip_transactions.exists():
            common_attributes.append({
                'type': 'ip_address',
                'description': 'Shared IP addresses',
                'count': common_ip_transactions.count(),
                'risk_score': 70.0,
            })
    
    # Check for common device IDs
    device_ids = set()
    for tx in transactions:
        if hasattr(tx, 'device_id') and tx.device_id:
            device_ids.add(tx.device_id)
    
    if device_ids:
        # Check if any other transactions from connected parties use the same devices
        common_device_transactions = Transaction.objects.filter(
            ~Q(user_id=transactions[0].user_id),
            user_id__in=party_ids
        ).filter(
            device_id__in=list(device_ids)
        )
        
        if common_device_transactions.exists():
            common_attributes.append({
                'type': 'device_id',
                'description': 'Shared devices',
                'count': common_device_transactions.count(),
                'risk_score': 80.0,
            })
    
    # Check for common payment methods
    card_numbers = set()
    for tx in transactions:
        if hasattr(tx, 'payment_method_data') and tx.payment_method_data:
            payment_method = tx.payment_method_data.get('type')
            if payment_method in ['credit_card', 'debit_card']:
                card_details = tx.payment_method_data.get('card_details', {})
                if card_details and 'card_number' in card_details:
                    card_numbers.add(card_details['card_number'])
    
    if card_numbers:
        # This is a simplified approach - in a real system, you'd need to handle hashed card numbers
        common_attributes.append({
            'type': 'payment_method',
            'description': 'Potentially shared payment methods',
            'count': len(card_numbers),
            'risk_score': 60.0,
        })
    
    return common_attributes


def find_transaction_patterns(transactions, connected_parties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Find transaction patterns between a user and connected parties.
    
    Args:
        transactions: QuerySet of transactions
        connected_parties: List of connected parties
        
    Returns:
        List of transaction patterns
    """
    transaction_patterns = []
    
    # Extract party IDs
    party_ids = [party['party_id'] for party in connected_parties]
    
    # Check for synchronized transactions
    # This is a simplified approach - in a real system, you'd use more sophisticated time-based analysis
    from django.utils import timezone
    from datetime import timedelta
    
    for tx in transactions:
        # Look for transactions within 5 minutes
        start_time = tx.timestamp - timedelta(minutes=5)
        end_time = tx.timestamp + timedelta(minutes=5)
        
        synchronized_transactions = Transaction.objects.filter(
            ~Q(user_id=tx.user_id),
            user_id__in=party_ids,
            timestamp__gte=start_time,
            timestamp__lte=end_time
        )
        
        if synchronized_transactions.exists():
            transaction_patterns.append({
                'type': 'synchronized_transactions',
                'description': 'Transactions occurring at similar times',
                'count': synchronized_transactions.count(),
                'risk_score': 65.0,
                'transaction_ids': [tx.transaction_id] + [t.transaction_id for t in synchronized_transactions],
            })
            break  # Only add this pattern once
    
    # Check for similar amounts
    for tx in transactions:
        amount = float(tx.amount)
        
        # Look for transactions with similar amounts (within 5%)
        min_amount = amount * 0.95
        max_amount = amount * 1.05
        
        similar_amount_transactions = Transaction.objects.filter(
            ~Q(user_id=tx.user_id),
            user_id__in=party_ids,
            amount__gte=min_amount,
            amount__lte=max_amount
        )
        
        if similar_amount_transactions.exists():
            transaction_patterns.append({
                'type': 'similar_amounts',
                'description': 'Transactions with similar amounts',
                'count': similar_amount_transactions.count(),
                'risk_score': 60.0,
                'transaction_ids': [tx.transaction_id] + [t.transaction_id for t in similar_amount_transactions],
            })
            break  # Only add this pattern once
    
    # Check for complementary transactions (e.g., A sends to B, B sends to C)
    # This is a simplified approach - in a real system, you'd use graph analysis
    wallet_transactions = [tx for tx in transactions if isinstance(tx, WalletTransaction)]
    
    for tx in wallet_transactions:
        # Look for transactions where this user's destination is another party's source
        if tx.destination_type == 'wallet':
            complementary_transactions = WalletTransaction.objects.filter(
                ~Q(user_id=tx.user_id),
                user_id__in=party_ids,
                source_type='wallet',
                source_id=tx.destination_id
            )
            
            if complementary_transactions.exists():
                transaction_patterns.append({
                    'type': 'complementary_transactions',
                    'description': 'Funds moving through multiple parties',
                    'count': complementary_transactions.count(),
                    'risk_score': 75.0,
                    'transaction_ids': [tx.transaction_id] + [t.transaction_id for t in complementary_transactions],
                })
                break  # Only add this pattern once
    
    return transaction_patterns


def calculate_connection_score(
    connected_parties: List[Dict[str, Any]],
    common_attributes: List[Dict[str, Any]],
    transaction_patterns: List[Dict[str, Any]]
) -> float:
    """
    Calculate a connection score based on party connections, common attributes, and transaction patterns.
    
    Args:
        connected_parties: List of connected parties
        common_attributes: List of common attributes
        transaction_patterns: List of transaction patterns
        
    Returns:
        Connection score (0-100)
    """
    # Base score
    score = 0.0
    
    # Add score based on number of connected parties
    party_score = min(len(connected_parties) * 5.0, 30.0)
    score += party_score
    
    # Add score based on common attributes
    for attr in common_attributes:
        score += attr['risk_score'] * 0.2  # Weight by 20%
    
    # Add score based on transaction patterns
    for pattern in transaction_patterns:
        score += pattern['risk_score'] * 0.3  # Weight by 30%
    
    # Cap at 100
    return min(score, 100.0)