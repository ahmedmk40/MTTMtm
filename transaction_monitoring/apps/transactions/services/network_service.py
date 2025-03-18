"""
Network analysis service for transactions.

This service provides methods for analyzing transaction networks.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from django.db.models import Count, Sum, F, Q
from django.utils import timezone
from datetime import datetime, timedelta
from ..models import Transaction

logger = logging.getLogger(__name__)


def get_transaction_network_data(days: int = 30, 
                                min_transactions: int = 2,
                                max_nodes: int = 100) -> Dict[str, Any]:
    """
    Get transaction network data for visualization.
    
    Args:
        days: Number of days to include
        min_transactions: Minimum number of transactions for a node to be included
        max_nodes: Maximum number of nodes to include
        
    Returns:
        Dictionary with network data
    """
    try:
        # Set time range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions in the time range
        transactions = Transaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        # Get user nodes
        user_counts = transactions.values('user_id').annotate(
            transaction_count=Count('id'),
            total_amount=Sum('amount')
        ).filter(
            transaction_count__gte=min_transactions
        ).order_by('-transaction_count')[:max_nodes]
        
        # Get merchant nodes
        merchant_counts = transactions.exclude(
            merchant_id__isnull=True
        ).exclude(
            merchant_id__exact=''
        ).values('merchant_id').annotate(
            transaction_count=Count('id'),
            total_amount=Sum('amount')
        ).filter(
            transaction_count__gte=min_transactions
        ).order_by('-transaction_count')[:max_nodes]
        
        # Create nodes
        nodes = []
        user_ids = set()
        merchant_ids = set()
        
        # Add user nodes
        for user in user_counts:
            user_id = user['user_id']
            user_ids.add(user_id)
            
            # Get risk level
            risk_level = 'low'
            if transactions.filter(user_id=user_id, is_flagged=True).exists():
                risk_level = 'high'
            elif transactions.filter(user_id=user_id, risk_score__gte=50).exists():
                risk_level = 'medium'
            
            nodes.append({
                'id': f"user_{user_id}",
                'label': f"User: {user_id}",
                'type': 'user',
                'size': min(50, max(10, user['transaction_count'] * 3)),
                'transactions': user['transaction_count'],
                'amount': float(user['total_amount']),
                'risk_level': risk_level
            })
        
        # Add merchant nodes
        for merchant in merchant_counts:
            merchant_id = merchant['merchant_id']
            merchant_ids.add(merchant_id)
            
            # Get risk level
            risk_level = 'low'
            if transactions.filter(merchant_id=merchant_id, is_flagged=True).exists():
                risk_level = 'high'
            elif transactions.filter(merchant_id=merchant_id, risk_score__gte=50).exists():
                risk_level = 'medium'
            
            nodes.append({
                'id': f"merchant_{merchant_id}",
                'label': f"Merchant: {merchant_id}",
                'type': 'merchant',
                'size': min(50, max(10, merchant['transaction_count'] * 3)),
                'transactions': merchant['transaction_count'],
                'amount': float(merchant['total_amount']),
                'risk_level': risk_level
            })
        
        # Create edges
        edges = []
        
        # Get user-merchant connections
        connections = transactions.filter(
            user_id__in=user_ids,
            merchant_id__in=merchant_ids
        ).values('user_id', 'merchant_id').annotate(
            transaction_count=Count('id'),
            total_amount=Sum('amount'),
            flagged_count=Count('id', filter=Q(is_flagged=True))
        )
        
        for conn in connections:
            user_id = conn['user_id']
            merchant_id = conn['merchant_id']
            
            # Skip if either node doesn't exist
            if user_id not in user_ids or merchant_id not in merchant_ids:
                continue
            
            # Determine edge color based on flagged transactions
            edge_color = '#aaa'  # Default gray
            if conn['flagged_count'] > 0:
                edge_color = '#e74a3b'  # Red for flagged
            
            edges.append({
                'id': f"edge_{user_id}_{merchant_id}",
                'source': f"user_{user_id}",
                'target': f"merchant_{merchant_id}",
                'size': min(10, max(1, conn['transaction_count'] / 2)),
                'transactions': conn['transaction_count'],
                'amount': float(conn['total_amount']),
                'flagged': conn['flagged_count'] > 0,
                'color': edge_color
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'total_transactions': transactions.count(),
                'total_users': len(user_ids),
                'total_merchants': len(merchant_ids),
                'total_connections': len(edges),
                'flagged_transactions': transactions.filter(is_flagged=True).count(),
                'high_risk_transactions': transactions.filter(risk_score__gte=80).count(),
                'medium_risk_transactions': transactions.filter(risk_score__gte=50, risk_score__lt=80).count(),
                'low_risk_transactions': transactions.filter(risk_score__lt=50).count(),
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting transaction network data: {str(e)}", exc_info=True)
        return {
            'nodes': [],
            'edges': [],
            'stats': {
                'total_transactions': 0,
                'total_users': 0,
                'total_merchants': 0,
                'total_connections': 0,
                'flagged_transactions': 0,
                'high_risk_transactions': 0,
                'medium_risk_transactions': 0,
                'low_risk_transactions': 0,
            },
            'error': str(e)
        }


def get_user_transaction_network(user_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Get transaction network data for a specific user.
    
    Args:
        user_id: User ID
        days: Number of days to include
        
    Returns:
        Dictionary with network data
    """
    try:
        # Set time range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get user's transactions
        user_transactions = Transaction.objects.filter(
            user_id=user_id,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        # Get merchants the user has transacted with
        merchant_ids = user_transactions.exclude(
            merchant_id__isnull=True
        ).exclude(
            merchant_id__exact=''
        ).values_list('merchant_id', flat=True).distinct()
        
        # Create nodes
        nodes = []
        edges = []
        
        # Add user node
        user_stats = user_transactions.aggregate(
            transaction_count=Count('id'),
            total_amount=Sum('amount'),
            flagged_count=Count('id', filter=Q(is_flagged=True))
        )
        
        # Get risk level
        risk_level = 'low'
        if user_transactions.filter(is_flagged=True).exists():
            risk_level = 'high'
        elif user_transactions.filter(risk_score__gte=50).exists():
            risk_level = 'medium'
        
        nodes.append({
            'id': f"user_{user_id}",
            'label': f"User: {user_id}",
            'type': 'user',
            'size': 30,
            'transactions': user_stats['transaction_count'],
            'amount': float(user_stats['total_amount'] or 0),
            'risk_level': risk_level
        })
        
        # Add merchant nodes
        for merchant_id in merchant_ids:
            merchant_transactions = user_transactions.filter(merchant_id=merchant_id)
            merchant_stats = merchant_transactions.aggregate(
                transaction_count=Count('id'),
                total_amount=Sum('amount'),
                flagged_count=Count('id', filter=Q(is_flagged=True))
            )
            
            # Get risk level
            risk_level = 'low'
            if merchant_transactions.filter(is_flagged=True).exists():
                risk_level = 'high'
            elif merchant_transactions.filter(risk_score__gte=50).exists():
                risk_level = 'medium'
            
            nodes.append({
                'id': f"merchant_{merchant_id}",
                'label': f"Merchant: {merchant_id}",
                'type': 'merchant',
                'size': min(30, max(10, merchant_stats['transaction_count'] * 3)),
                'transactions': merchant_stats['transaction_count'],
                'amount': float(merchant_stats['total_amount'] or 0),
                'risk_level': risk_level
            })
            
            # Add edge
            edge_color = '#aaa'  # Default gray
            if merchant_stats['flagged_count'] > 0:
                edge_color = '#e74a3b'  # Red for flagged
            
            edges.append({
                'id': f"edge_{user_id}_{merchant_id}",
                'source': f"user_{user_id}",
                'target': f"merchant_{merchant_id}",
                'size': min(10, max(1, merchant_stats['transaction_count'] / 2)),
                'transactions': merchant_stats['transaction_count'],
                'amount': float(merchant_stats['total_amount'] or 0),
                'flagged': merchant_stats['flagged_count'] > 0,
                'color': edge_color
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'total_transactions': user_transactions.count(),
                'total_merchants': len(merchant_ids),
                'flagged_transactions': user_transactions.filter(is_flagged=True).count(),
                'high_risk_transactions': user_transactions.filter(risk_score__gte=80).count(),
                'medium_risk_transactions': user_transactions.filter(risk_score__gte=50, risk_score__lt=80).count(),
                'low_risk_transactions': user_transactions.filter(risk_score__lt=50).count(),
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting user transaction network data: {str(e)}", exc_info=True)
        return {
            'nodes': [],
            'edges': [],
            'stats': {
                'total_transactions': 0,
                'total_merchants': 0,
                'flagged_transactions': 0,
                'high_risk_transactions': 0,
                'medium_risk_transactions': 0,
                'low_risk_transactions': 0,
            },
            'error': str(e)
        }


def get_merchant_transaction_network(merchant_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Get transaction network data for a specific merchant.
    
    Args:
        merchant_id: Merchant ID
        days: Number of days to include
        
    Returns:
        Dictionary with network data
    """
    try:
        # Set time range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get merchant's transactions
        merchant_transactions = Transaction.objects.filter(
            merchant_id=merchant_id,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        # Get users who have transacted with this merchant
        user_ids = merchant_transactions.values_list('user_id', flat=True).distinct()
        
        # Create nodes
        nodes = []
        edges = []
        
        # Add merchant node
        merchant_stats = merchant_transactions.aggregate(
            transaction_count=Count('id'),
            total_amount=Sum('amount'),
            flagged_count=Count('id', filter=Q(is_flagged=True))
        )
        
        # Get risk level
        risk_level = 'low'
        if merchant_transactions.filter(is_flagged=True).exists():
            risk_level = 'high'
        elif merchant_transactions.filter(risk_score__gte=50).exists():
            risk_level = 'medium'
        
        nodes.append({
            'id': f"merchant_{merchant_id}",
            'label': f"Merchant: {merchant_id}",
            'type': 'merchant',
            'size': 30,
            'transactions': merchant_stats['transaction_count'],
            'amount': float(merchant_stats['total_amount'] or 0),
            'risk_level': risk_level
        })
        
        # Add user nodes
        for user_id in user_ids:
            user_transactions = merchant_transactions.filter(user_id=user_id)
            user_stats = user_transactions.aggregate(
                transaction_count=Count('id'),
                total_amount=Sum('amount'),
                flagged_count=Count('id', filter=Q(is_flagged=True))
            )
            
            # Get risk level
            risk_level = 'low'
            if user_transactions.filter(is_flagged=True).exists():
                risk_level = 'high'
            elif user_transactions.filter(risk_score__gte=50).exists():
                risk_level = 'medium'
            
            nodes.append({
                'id': f"user_{user_id}",
                'label': f"User: {user_id}",
                'type': 'user',
                'size': min(30, max(10, user_stats['transaction_count'] * 3)),
                'transactions': user_stats['transaction_count'],
                'amount': float(user_stats['total_amount'] or 0),
                'risk_level': risk_level
            })
            
            # Add edge
            edge_color = '#aaa'  # Default gray
            if user_stats['flagged_count'] > 0:
                edge_color = '#e74a3b'  # Red for flagged
            
            edges.append({
                'id': f"edge_{user_id}_{merchant_id}",
                'source': f"user_{user_id}",
                'target': f"merchant_{merchant_id}",
                'size': min(10, max(1, user_stats['transaction_count'] / 2)),
                'transactions': user_stats['transaction_count'],
                'amount': float(user_stats['total_amount'] or 0),
                'flagged': user_stats['flagged_count'] > 0,
                'color': edge_color
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'total_transactions': merchant_transactions.count(),
                'total_users': len(user_ids),
                'flagged_transactions': merchant_transactions.filter(is_flagged=True).count(),
                'high_risk_transactions': merchant_transactions.filter(risk_score__gte=80).count(),
                'medium_risk_transactions': merchant_transactions.filter(risk_score__gte=50, risk_score__lt=80).count(),
                'low_risk_transactions': merchant_transactions.filter(risk_score__lt=50).count(),
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting merchant transaction network data: {str(e)}", exc_info=True)
        return {
            'nodes': [],
            'edges': [],
            'stats': {
                'total_transactions': 0,
                'total_users': 0,
                'flagged_transactions': 0,
                'high_risk_transactions': 0,
                'medium_risk_transactions': 0,
                'low_risk_transactions': 0,
            },
            'error': str(e)
        }


def detect_unusual_patterns(days: int = 30) -> List[Dict[str, Any]]:
    """
    Detect unusual patterns in the transaction network.
    
    Args:
        days: Number of days to include
        
    Returns:
        List of unusual patterns
    """
    try:
        # Set time range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions in the time range
        transactions = Transaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        # Initialize patterns list
        patterns = []
        
        # 1. Detect users with high transaction volume
        high_volume_users = transactions.values('user_id').annotate(
            transaction_count=Count('id'),
            total_amount=Sum('amount')
        ).filter(
            transaction_count__gte=10  # Adjust threshold as needed
        ).order_by('-transaction_count')[:10]
        
        for user in high_volume_users:
            patterns.append({
                'type': 'high_volume_user',
                'user_id': user['user_id'],
                'transaction_count': user['transaction_count'],
                'total_amount': float(user['total_amount']),
                'description': f"User {user['user_id']} has {user['transaction_count']} transactions totaling {user['total_amount']} in the last {days} days."
            })
        
        # 2. Detect merchants with high flagged transaction rate
        high_flag_merchants = transactions.exclude(
            merchant_id__isnull=True
        ).exclude(
            merchant_id__exact=''
        ).values('merchant_id').annotate(
            transaction_count=Count('id'),
            flagged_count=Count('id', filter=Q(is_flagged=True)),
            flag_rate=Count('id', filter=Q(is_flagged=True)) * 100.0 / Count('id')
        ).filter(
            transaction_count__gte=5,  # Minimum transactions
            flag_rate__gte=20  # At least 20% flagged
        ).order_by('-flag_rate')[:10]
        
        for merchant in high_flag_merchants:
            patterns.append({
                'type': 'high_flag_merchant',
                'merchant_id': merchant['merchant_id'],
                'transaction_count': merchant['transaction_count'],
                'flagged_count': merchant['flagged_count'],
                'flag_rate': merchant['flag_rate'],
                'description': f"Merchant {merchant['merchant_id']} has {merchant['flagged_count']} flagged transactions ({merchant['flag_rate']:.1f}% of total) in the last {days} days."
            })
        
        # 3. Detect unusual user-merchant connections
        # (Users who transact with high-risk merchants)
        high_risk_merchants = transactions.filter(
            is_flagged=True
        ).exclude(
            merchant_id__isnull=True
        ).exclude(
            merchant_id__exact=''
        ).values_list('merchant_id', flat=True).distinct()
        
        for merchant_id in high_risk_merchants:
            # Find users who transact with this high-risk merchant
            users = transactions.filter(
                merchant_id=merchant_id
            ).values('user_id').annotate(
                transaction_count=Count('id'),
                total_amount=Sum('amount')
            ).order_by('-transaction_count')[:5]
            
            for user in users:
                patterns.append({
                    'type': 'high_risk_connection',
                    'user_id': user['user_id'],
                    'merchant_id': merchant_id,
                    'transaction_count': user['transaction_count'],
                    'total_amount': float(user['total_amount']),
                    'description': f"User {user['user_id']} has {user['transaction_count']} transactions with high-risk merchant {merchant_id}."
                })
        
        return patterns
    
    except Exception as e:
        logger.error(f"Error detecting unusual patterns: {str(e)}", exc_info=True)
        return []