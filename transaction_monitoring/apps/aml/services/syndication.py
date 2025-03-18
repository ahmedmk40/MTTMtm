"""
Syndication detection service for the AML app.

This service is responsible for detecting transaction syndication patterns.
"""

import logging
import networkx as nx
from typing import Dict, Any, List, Set, Tuple
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta
from apps.transactions.models import Transaction, WalletTransaction
from .circular_flow import detect_circular_flows
from .party_analysis import analyze_party_connections

logger = logging.getLogger(__name__)


def detect_syndication(user_id: str) -> Dict[str, Any]:
    """
    Detect transaction syndication for a user.
    
    Args:
        user_id: The user ID to analyze
        
    Returns:
        Dictionary with the syndication detection result
    """
    # Initialize result
    result = {
        'syndication_detected': False,
        'syndication_score': 0.0,
        'circular_flows': {},
        'party_connections': {},
        'layering_patterns': [],
        'structuring_patterns': [],
    }
    
    try:
        # Check for circular flows
        circular_flows = detect_circular_flows(user_id)
        result['circular_flows'] = circular_flows
        
        # Check for party connections
        party_connections = analyze_party_connections(user_id)
        result['party_connections'] = party_connections
        
        # Check for layering patterns
        layering_patterns = detect_layering(user_id)
        result['layering_patterns'] = layering_patterns
        
        # Check for structuring patterns
        structuring_patterns = detect_structuring(user_id)
        result['structuring_patterns'] = structuring_patterns
        
        # Calculate syndication score
        syndication_score = calculate_syndication_score(
            circular_flows,
            party_connections,
            layering_patterns,
            structuring_patterns
        )
        result['syndication_score'] = syndication_score
        
        # Determine if syndication is detected
        result['syndication_detected'] = syndication_score >= 70.0
        
        logger.info(
            f"Syndication detection for user {user_id}: "
            f"detected={result['syndication_detected']}, "
            f"score={result['syndication_score']:.2f}"
        )
    
    except Exception as e:
        logger.error(f"Error detecting syndication for user {user_id}: {str(e)}", exc_info=True)
    
    return result


def detect_layering(user_id: str) -> List[Dict[str, Any]]:
    """
    Detect layering patterns for a user.
    
    Layering involves moving funds through multiple accounts to obscure the source.
    
    Args:
        user_id: The user ID to analyze
        
    Returns:
        List of layering patterns
    """
    layering_patterns = []
    
    try:
        # Get wallet transactions for the user (last 90 days)
        start_date = timezone.now() - timedelta(days=90)
        
        transactions = WalletTransaction.objects.filter(
            user_id=user_id,
            timestamp__gte=start_date
        )
        
        if not transactions.exists():
            return layering_patterns
        
        # Build transaction graph
        G = nx.DiGraph()
        
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
        
        # Find paths with length > 2 (indicating layering)
        for source in G.nodes():
            for destination in G.nodes():
                if source != destination:
                    # Find all simple paths between source and destination
                    paths = list(nx.all_simple_paths(G, source, destination, cutoff=5))
                    
                    for path in paths:
                        if len(path) > 2:  # Path with at least 3 nodes (2 hops)
                            # Extract transactions along the path
                            path_transactions = []
                            total_amount = 0.0
                            currency = None
                            
                            for i in range(len(path) - 1):
                                source_node = path[i]
                                destination_node = path[i + 1]
                                
                                if G.has_edge(source_node, destination_node):
                                    edge_data = G.get_edge_data(source_node, destination_node)
                                    
                                    path_transactions.append({
                                        'transaction_id': edge_data['transaction_id'],
                                        'source': source_node,
                                        'destination': destination_node,
                                        'amount': edge_data['amount'],
                                        'currency': edge_data['currency'],
                                        'timestamp': edge_data['timestamp'],
                                        'user_id': edge_data['user_id'],
                                    })
                                    
                                    # Update total amount and currency
                                    if currency is None:
                                        currency = edge_data['currency']
                                    
                                    if currency == edge_data['currency']:
                                        total_amount += edge_data['amount']
                            
                            # Add layering pattern
                            layering_patterns.append({
                                'path': path,
                                'path_length': len(path),
                                'transactions': path_transactions,
                                'total_amount': total_amount,
                                'currency': currency,
                                'risk_score': 60.0 + (len(path) - 2) * 5.0,  # Higher score for longer paths
                            })
    
    except Exception as e:
        logger.error(f"Error detecting layering for user {user_id}: {str(e)}", exc_info=True)
    
    return layering_patterns


def detect_structuring(user_id: str) -> List[Dict[str, Any]]:
    """
    Detect structuring patterns for a user.
    
    Structuring involves breaking up large transactions into smaller ones to avoid reporting thresholds.
    
    Args:
        user_id: The user ID to analyze
        
    Returns:
        List of structuring patterns
    """
    structuring_patterns = []
    
    try:
        # Get transactions for the user (last 90 days)
        start_date = timezone.now() - timedelta(days=90)
        
        transactions = Transaction.objects.filter(
            user_id=user_id,
            timestamp__gte=start_date
        )
        
        if not transactions.exists():
            return structuring_patterns
        
        # Common reporting thresholds
        thresholds = [10000, 5000, 3000]
        
        for threshold in thresholds:
            # Look for multiple transactions just below threshold
            threshold_min = threshold * 0.8
            threshold_max = threshold * 0.99
            
            # Group by day and count transactions in the threshold range
            from django.db.models.functions import TruncDay
            
            daily_counts = transactions.filter(
                amount__gte=threshold_min,
                amount__lte=threshold_max
            ).annotate(
                day=TruncDay('timestamp')
            ).values('day').annotate(
                count=Count('id'),
                total=Sum('amount')
            ).filter(
                count__gte=2  # At least 2 transactions per day
            ).order_by('-day')
            
            for daily_count in daily_counts:
                # Get the transactions for this day
                day_start = daily_count['day']
                day_end = day_start + timedelta(days=1)
                
                day_transactions = transactions.filter(
                    amount__gte=threshold_min,
                    amount__lte=threshold_max,
                    timestamp__gte=day_start,
                    timestamp__lt=day_end
                )
                
                # Add structuring pattern
                structuring_patterns.append({
                    'threshold': threshold,
                    'day': day_start.isoformat(),
                    'transaction_count': daily_count['count'],
                    'total_amount': float(daily_count['total']),
                    'transactions': [
                        {
                            'transaction_id': tx.transaction_id,
                            'amount': float(tx.amount),
                            'currency': tx.currency,
                            'timestamp': tx.timestamp.isoformat(),
                        }
                        for tx in day_transactions
                    ],
                    'risk_score': 70.0 + (daily_count['count'] - 2) * 5.0,  # Higher score for more transactions
                })
    
    except Exception as e:
        logger.error(f"Error detecting structuring for user {user_id}: {str(e)}", exc_info=True)
    
    return structuring_patterns


def calculate_syndication_score(
    circular_flows: Dict[str, Any],
    party_connections: Dict[str, Any],
    layering_patterns: List[Dict[str, Any]],
    structuring_patterns: List[Dict[str, Any]]
) -> float:
    """
    Calculate a syndication score based on various detection results.
    
    Args:
        circular_flows: Circular flow detection result
        party_connections: Party connection analysis result
        layering_patterns: List of layering patterns
        structuring_patterns: List of structuring patterns
        
    Returns:
        Syndication score (0-100)
    """
    # Base score
    score = 0.0
    
    # Add score based on circular flows
    if circular_flows.get('circular_flows_detected', False):
        flow_count = len(circular_flows.get('flows', []))
        flow_score = min(flow_count * 20.0, 60.0)
        score += flow_score
    
    # Add score based on party connections
    connection_score = party_connections.get('connection_score', 0.0)
    score += connection_score * 0.3  # Weight by 30%
    
    # Add score based on layering patterns
    if layering_patterns:
        max_layering_score = max(pattern['risk_score'] for pattern in layering_patterns)
        score += max_layering_score * 0.2  # Weight by 20%
    
    # Add score based on structuring patterns
    if structuring_patterns:
        max_structuring_score = max(pattern['risk_score'] for pattern in structuring_patterns)
        score += max_structuring_score * 0.2  # Weight by 20%
    
    # Cap at 100
    return min(score, 100.0)