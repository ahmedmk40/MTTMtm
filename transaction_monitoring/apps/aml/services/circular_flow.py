"""
Circular flow detection service for the AML app.

This service is responsible for detecting circular flows of funds.
"""

import logging
import networkx as nx
from typing import Dict, Any, List, Set, Tuple
from django.db.models import Q
from apps.transactions.models import WalletTransaction

logger = logging.getLogger(__name__)


def detect_circular_flows(user_id: str, transaction_id: str = None, max_depth: int = 5) -> Dict[str, Any]:
    """
    Detect circular flows of funds for a user.
    
    Args:
        user_id: The user ID to check
        transaction_id: Optional transaction ID to start from
        max_depth: Maximum depth for circular flow detection
        
    Returns:
        Dictionary with the circular flow detection result
    """
    # Initialize result
    result = {
        'circular_flows_detected': False,
        'flows': [],
        'transaction_count': 0,
    }
    
    try:
        # Build transaction graph
        G = build_transaction_graph(user_id, transaction_id)
        
        # Get transaction count
        result['transaction_count'] = G.number_of_edges()
        
        if result['transaction_count'] == 0:
            return result
        
        # Find circular flows
        circular_flows = find_circular_flows(G, user_id, max_depth)
        
        if circular_flows:
            result['circular_flows_detected'] = True
            result['flows'] = circular_flows
        
        logger.info(
            f"Circular flow detection for user {user_id}: "
            f"detected={result['circular_flows_detected']}, "
            f"flows={len(result['flows'])}, "
            f"transactions={result['transaction_count']}"
        )
    
    except Exception as e:
        logger.error(f"Error detecting circular flows for user {user_id}: {str(e)}", exc_info=True)
    
    return result


def build_transaction_graph(user_id: str, transaction_id: str = None) -> nx.DiGraph:
    """
    Build a directed graph of transactions.
    
    Args:
        user_id: The user ID to build the graph for
        transaction_id: Optional transaction ID to start from
        
    Returns:
        NetworkX DiGraph of transactions
    """
    # Create directed graph
    G = nx.DiGraph()
    
    # Get transactions for the user
    if transaction_id:
        # Start with the specific transaction
        transaction = WalletTransaction.objects.get(transaction_id=transaction_id)
        transactions = [transaction]
        
        # Add related transactions (last 30 days)
        from django.utils import timezone
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=30)
        
        related_transactions = WalletTransaction.objects.filter(
            Q(user_id=user_id) | 
            Q(source_id=transaction.source_id) | 
            Q(destination_id=transaction.destination_id)
        ).filter(
            timestamp__gte=start_date
        ).exclude(
            transaction_id=transaction_id
        )
        
        transactions.extend(related_transactions)
    else:
        # Get all transactions for the user (last 90 days)
        from django.utils import timezone
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=90)
        
        transactions = WalletTransaction.objects.filter(
            user_id=user_id,
            timestamp__gte=start_date
        )
    
    # Add nodes and edges to the graph
    for tx in transactions:
        source = f"{tx.source_type}:{tx.source_id}"
        destination = f"{tx.destination_type}:{tx.destination_id}"
        
        # Add nodes if they don't exist
        if not G.has_node(source):
            G.add_node(source, type=tx.source_type)
        
        if not G.has_node(destination):
            G.add_node(destination, type=tx.destination_type)
        
        # Add edge
        G.add_edge(
            source, 
            destination, 
            transaction_id=tx.transaction_id,
            amount=float(tx.amount),
            currency=tx.currency,
            timestamp=tx.timestamp.isoformat(),
            user_id=tx.user_id
        )
    
    return G


def find_circular_flows(G: nx.DiGraph, user_id: str, max_depth: int = 5) -> List[Dict[str, Any]]:
    """
    Find circular flows in a transaction graph.
    
    Args:
        G: NetworkX DiGraph of transactions
        user_id: The user ID to check
        max_depth: Maximum depth for circular flow detection
        
    Returns:
        List of circular flows
    """
    circular_flows = []
    
    # Find all simple cycles in the graph
    try:
        cycles = list(nx.simple_cycles(G))
        
        # Filter cycles by max depth
        cycles = [cycle for cycle in cycles if len(cycle) <= max_depth]
        
        # Convert cycles to flow dictionaries
        for cycle in cycles:
            flow = {
                'nodes': cycle,
                'transactions': [],
                'total_amount': 0.0,
                'currency': None,
            }
            
            # Add transactions
            for i in range(len(cycle)):
                source = cycle[i]
                destination = cycle[(i + 1) % len(cycle)]
                
                if G.has_edge(source, destination):
                    edge_data = G.get_edge_data(source, destination)
                    
                    flow['transactions'].append({
                        'transaction_id': edge_data['transaction_id'],
                        'source': source,
                        'destination': destination,
                        'amount': edge_data['amount'],
                        'currency': edge_data['currency'],
                        'timestamp': edge_data['timestamp'],
                        'user_id': edge_data['user_id'],
                    })
                    
                    # Update total amount and currency
                    if flow['currency'] is None:
                        flow['currency'] = edge_data['currency']
                    
                    if flow['currency'] == edge_data['currency']:
                        flow['total_amount'] += edge_data['amount']
            
            circular_flows.append(flow)
    
    except nx.NetworkXNoCycle:
        # No cycles found
        pass
    
    return circular_flows