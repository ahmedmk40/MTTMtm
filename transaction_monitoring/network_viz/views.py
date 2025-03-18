"""
Views for network visualization.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@login_required
def network_dashboard(request):
    """
    Network dashboard view.
    """
    from django.db.models import Count, Sum, Q, F, Avg, StdDev, Max, Min
    from apps.transactions.models import Transaction
    from django.utils import timezone
    from datetime import timedelta
    from django.core.paginator import Paginator
    import numpy as np
    
    # Get filter parameters
    days = int(request.GET.get('days', 30))
    min_transactions = int(request.GET.get('min_transactions', 2))
    max_nodes = int(request.GET.get('max_nodes', 100))
    filter_type = request.GET.get('filter_type', 'all')  # all, flagged, high_risk
    layout = request.GET.get('layout', 'force')  # force, circular, hierarchical
    pattern_type = request.GET.get('pattern_type', 'all')  # all, high_volume_user, high_flag_merchant, etc.
    page = request.GET.get('page', 1)
    
    # Set time range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get transactions in the time range
    transactions = Transaction.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Apply additional filters
    if filter_type == 'flagged':
        transactions = transactions.filter(is_flagged=True)
    elif filter_type == 'high_risk':
        transactions = transactions.filter(risk_score__gte=80)
    
    # Get transaction statistics
    total_count = transactions.count()
    total_amount = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
    avg_amount = transactions.aggregate(Avg('amount'))['amount__avg'] or 0
    max_amount = transactions.aggregate(Max('amount'))['amount__max'] or 0
    min_amount = transactions.aggregate(Min('amount'))['amount__min'] or 0
    
    # Calculate transaction volume over time (for time series)
    time_series_data = []
    for i in range(days):
        day = end_date - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        day_transactions = transactions.filter(timestamp__gte=day_start, timestamp__lte=day_end)
        day_count = day_transactions.count()
        day_amount = day_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        day_flagged = day_transactions.filter(is_flagged=True).count()
        
        time_series_data.append({
            'date': day_start.strftime('%Y-%m-%d'),
            'count': day_count,
            'amount': float(day_amount),
            'flagged': day_flagged
        })
    
    # Reverse to get chronological order
    time_series_data.reverse()
    
    # Detect unusual patterns
    all_patterns = []
    
    # 1. High volume users
    high_volume_users = transactions.values('user_id').annotate(
        transaction_count=Count('id'),
        total_amount=Sum('amount'),
        avg_amount=Avg('amount'),
        flagged_count=Count('id', filter=Q(is_flagged=True))
    ).filter(
        transaction_count__gte=5  # At least 5 transactions
    ).order_by('-transaction_count')[:10]  # Increased to 10
    
    for user in high_volume_users:
        all_patterns.append({
            'type': 'high_volume_user',
            'user_id': user['user_id'],
            'transaction_count': user['transaction_count'],
            'total_amount': float(user['total_amount']),
            'avg_amount': float(user['avg_amount']),
            'flagged_count': user['flagged_count'],
            'severity': 'medium' if user['transaction_count'] > 10 else 'low',
            'description': f"User {user['user_id']} has {user['transaction_count']} transactions totaling ${float(user['total_amount']):.2f} in the last {days} days."
        })
    
    # 2. High risk merchants
    high_risk_merchants = transactions.exclude(
        merchant_id__isnull=True
    ).exclude(
        merchant_id__exact=''
    ).values('merchant_id').annotate(
        transaction_count=Count('id'),
        total_amount=Sum('amount'),
        avg_amount=Avg('amount'),
        flagged_count=Count('id', filter=Q(is_flagged=True)),
        flag_rate=Count('id', filter=Q(is_flagged=True)) * 100.0 / Count('id')
    ).filter(
        transaction_count__gte=2,  # At least 2 transactions
        flagged_count__gte=1  # At least 1 flagged transaction
    ).order_by('-flag_rate')[:10]  # Increased to 10
    
    for merchant in high_risk_merchants:
        all_patterns.append({
            'type': 'high_flag_merchant',
            'merchant_id': merchant['merchant_id'],
            'transaction_count': merchant['transaction_count'],
            'total_amount': float(merchant['total_amount']),
            'avg_amount': float(merchant['avg_amount']),
            'flagged_count': merchant['flagged_count'],
            'flag_rate': float(merchant['flag_rate']),
            'severity': 'high' if merchant['flag_rate'] > 50 else 'medium',
            'description': f"Merchant {merchant['merchant_id']} has {merchant['flagged_count']} flagged transactions ({float(merchant['flag_rate']):.1f}% of total) in the last {days} days."
        })
    
    # 3. High amount transactions
    high_amount_transactions = transactions.filter(
        amount__gte=5000  # Transactions over $5,000
    ).values('user_id', 'merchant_id', 'transaction_id', 'amount', 'risk_score', 'is_flagged').order_by('-amount')[:10]  # Increased to 10
    
    # Convert max_amount to float for comparison
    max_amount_float = float(max_amount) if max_amount else 0
    
    for tx in high_amount_transactions:
        # Calculate severity based on amount percentile
        tx_amount = float(tx['amount'])
        severity = 'low'
        if tx_amount > max_amount_float * 0.75:
            severity = 'high'
        elif tx_amount > max_amount_float * 0.5:
            severity = 'medium'
            
        all_patterns.append({
            'type': 'high_amount_transaction',
            'user_id': tx['user_id'],
            'merchant_id': tx['merchant_id'],
            'transaction_id': tx['transaction_id'],
            'amount': float(tx['amount']),
            'risk_score': float(tx['risk_score']) if tx['risk_score'] else None,
            'is_flagged': tx['is_flagged'],
            'severity': severity,
            'description': f"High amount transaction of ${float(tx['amount']):.2f} between {tx['user_id']} and {tx['merchant_id']}."
        })
    
    # 4. Velocity patterns (rapid succession of transactions)
    # Group transactions by user and find users with multiple transactions in short time periods
    user_transactions = {}
    for tx in transactions.order_by('user_id', 'timestamp').values('user_id', 'timestamp', 'amount'):
        if tx['user_id'] not in user_transactions:
            user_transactions[tx['user_id']] = []
        user_transactions[tx['user_id']].append(tx)
    
    velocity_patterns = []
    for user_id, txs in user_transactions.items():
        if len(txs) < 3:  # Need at least 3 transactions to detect velocity
            continue
        
        # Check for transactions within 1 hour of each other
        for i in range(len(txs) - 2):
            if (txs[i+2]['timestamp'] - txs[i]['timestamp']).total_seconds() < 3600:  # 1 hour
                total_amount = sum(float(txs[j]['amount']) for j in range(i, i+3))
                velocity_patterns.append({
                    'user_id': user_id,
                    'transaction_count': 3,
                    'time_window': '1 hour',
                    'total_amount': total_amount,
                    'severity': 'high' if total_amount > 10000 else 'medium',
                    'description': f"User {user_id} made 3 transactions totaling ${total_amount:.2f} within 1 hour."
                })
                break
    
    # Add top velocity patterns
    velocity_patterns.sort(key=lambda x: x['total_amount'], reverse=True)
    for pattern in velocity_patterns[:5]:  # Increased to 5
        all_patterns.append({
            'type': 'velocity_pattern',
            'user_id': pattern['user_id'],
            'transaction_count': pattern['transaction_count'],
            'time_window': pattern['time_window'],
            'total_amount': pattern['total_amount'],
            'severity': pattern.get('severity', 'medium'),
            'description': pattern['description']
        })
    
    # 5. ML integration - Get transactions with highest risk scores
    high_risk_score_transactions = transactions.filter(
        risk_score__isnull=False
    ).order_by('-risk_score')[:5]  # Increased to 5
    
    for tx in high_risk_score_transactions:
        risk_score = float(tx.risk_score) if tx.risk_score else 0
        all_patterns.append({
            'type': 'ml_high_risk',
            'user_id': tx.user_id,
            'merchant_id': tx.merchant_id,
            'transaction_id': tx.transaction_id,
            'amount': float(tx.amount),
            'risk_score': risk_score,
            'severity': 'high' if risk_score > 90 else ('medium' if risk_score > 70 else 'low'),
            'description': f"ML flagged transaction with risk score {risk_score:.1f} between {tx.user_id} and {tx.merchant_id}."
        })
    
    # Filter patterns by type if requested
    if pattern_type != 'all':
        filtered_patterns = [p for p in all_patterns if p['type'] == pattern_type]
    else:
        filtered_patterns = all_patterns
    
    # Sort patterns by severity
    filtered_patterns.sort(key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x.get('severity', 'low'), 3))
    
    # Paginate patterns
    paginator = Paginator(filtered_patterns, 10)  # Show 10 patterns per page
    patterns_page = paginator.get_page(page)
    
    # Calculate pattern type counts for the filter dropdown
    pattern_counts = {
        'all': len(all_patterns),
        'high_volume_user': len([p for p in all_patterns if p['type'] == 'high_volume_user']),
        'high_flag_merchant': len([p for p in all_patterns if p['type'] == 'high_flag_merchant']),
        'high_amount_transaction': len([p for p in all_patterns if p['type'] == 'high_amount_transaction']),
        'velocity_pattern': len([p for p in all_patterns if p['type'] == 'velocity_pattern']),
        'ml_high_risk': len([p for p in all_patterns if p['type'] == 'ml_high_risk']),
    }
    
    # Calculate severity counts
    severity_counts = {
        'high': len([p for p in all_patterns if p.get('severity') == 'high']),
        'medium': len([p for p in all_patterns if p.get('severity') == 'medium']),
        'low': len([p for p in all_patterns if p.get('severity') == 'low']),
    }
    
    return render(request, 'network_viz/network_dashboard.html', {
        'title': 'Transaction Network',
        'days': days,
        'min_transactions': min_transactions,
        'max_nodes': max_nodes,
        'filter_type': filter_type,
        'layout': layout,
        'pattern_type': pattern_type,
        'patterns': patterns_page,
        'pattern_counts': pattern_counts,
        'severity_counts': severity_counts,
        'stats': {
            'total_count': total_count,
            'total_amount': float(total_amount),
            'avg_amount': float(avg_amount),
            'max_amount': float(max_amount),
            'min_amount': float(min_amount),
        },
        'time_series_data': time_series_data
    })


@login_required
def network_data(request):
    """
    Network data API.
    """
    from django.db.models import Count, Sum, Q, Avg, Max, Min, F
    from apps.transactions.models import Transaction
    from django.utils import timezone
    from datetime import timedelta
    import numpy as np
    from collections import defaultdict
    
    # Get filter parameters
    days = int(request.GET.get('days', 30))
    min_transactions = int(request.GET.get('min_transactions', 2))
    max_nodes = int(request.GET.get('max_nodes', 100))
    filter_type = request.GET.get('filter_type', 'all')  # all, flagged, high_risk
    layout = request.GET.get('layout', 'force')  # force, circular, hierarchical
    
    # Set time range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get transactions in the time range
    transactions = Transaction.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Apply additional filters
    if filter_type == 'flagged':
        transactions = transactions.filter(is_flagged=True)
    elif filter_type == 'high_risk':
        transactions = transactions.filter(risk_score__gte=80)
    
    # Get user nodes
    user_counts = transactions.values('user_id').annotate(
        transaction_count=Count('id'),
        total_amount=Sum('amount'),
        avg_amount=Avg('amount'),
        max_amount=Max('amount'),
        min_amount=Min('amount'),
        flagged_count=Count('id', filter=Q(is_flagged=True)),
        high_risk_count=Count('id', filter=Q(risk_score__gte=80)),
        medium_risk_count=Count('id', filter=Q(risk_score__gte=50, risk_score__lt=80)),
        low_risk_count=Count('id', filter=Q(risk_score__lt=50))
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
        total_amount=Sum('amount'),
        avg_amount=Avg('amount'),
        max_amount=Max('amount'),
        min_amount=Min('amount'),
        flagged_count=Count('id', filter=Q(is_flagged=True)),
        high_risk_count=Count('id', filter=Q(risk_score__gte=80)),
        medium_risk_count=Count('id', filter=Q(risk_score__gte=50, risk_score__lt=80)),
        low_risk_count=Count('id', filter=Q(risk_score__lt=50))
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
        if user['flagged_count'] > 0 or user['high_risk_count'] > 0:
            risk_level = 'high'
        elif user['medium_risk_count'] > 0:
            risk_level = 'medium'
        
        # Calculate risk score for visualization
        risk_score = 0
        if user['transaction_count'] > 0:
            risk_score = (user['flagged_count'] * 100 + user['high_risk_count'] * 80 + 
                         user['medium_risk_count'] * 50) / user['transaction_count']
        
        nodes.append({
            'id': f"user_{user_id}",
            'label': f"User: {user_id}",
            'type': 'user',
            'size': min(50, max(10, user['transaction_count'] * 3)),
            'transactions': user['transaction_count'],
            'amount': float(user['total_amount']),
            'avg_amount': float(user['avg_amount']),
            'max_amount': float(user['max_amount']),
            'min_amount': float(user['min_amount']),
            'flagged_count': user['flagged_count'],
            'high_risk_count': user['high_risk_count'],
            'medium_risk_count': user['medium_risk_count'],
            'low_risk_count': user['low_risk_count'],
            'risk_level': risk_level,
            'risk_score': min(100, risk_score)
        })
    
    # Add merchant nodes
    for merchant in merchant_counts:
        merchant_id = merchant['merchant_id']
        merchant_ids.add(merchant_id)
        
        # Get risk level
        risk_level = 'low'
        if merchant['flagged_count'] > 0 or merchant['high_risk_count'] > 0:
            risk_level = 'high'
        elif merchant['medium_risk_count'] > 0:
            risk_level = 'medium'
        
        # Calculate risk score for visualization
        risk_score = 0
        if merchant['transaction_count'] > 0:
            risk_score = (merchant['flagged_count'] * 100 + merchant['high_risk_count'] * 80 + 
                         merchant['medium_risk_count'] * 50) / merchant['transaction_count']
        
        nodes.append({
            'id': f"merchant_{merchant_id}",
            'label': f"Merchant: {merchant_id}",
            'type': 'merchant',
            'size': min(50, max(10, merchant['transaction_count'] * 3)),
            'transactions': merchant['transaction_count'],
            'amount': float(merchant['total_amount']),
            'avg_amount': float(merchant['avg_amount']),
            'max_amount': float(merchant['max_amount']),
            'min_amount': float(merchant['min_amount']),
            'flagged_count': merchant['flagged_count'],
            'high_risk_count': merchant['high_risk_count'],
            'medium_risk_count': merchant['medium_risk_count'],
            'low_risk_count': merchant['low_risk_count'],
            'risk_level': risk_level,
            'risk_score': min(100, risk_score)
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
        avg_amount=Avg('amount'),
        max_amount=Max('amount'),
        min_amount=Min('amount'),
        flagged_count=Count('id', filter=Q(is_flagged=True)),
        high_risk_count=Count('id', filter=Q(risk_score__gte=80)),
        medium_risk_count=Count('id', filter=Q(risk_score__gte=50, risk_score__lt=80)),
        low_risk_count=Count('id', filter=Q(risk_score__lt=50))
    )
    
    for conn in connections:
        user_id = conn['user_id']
        merchant_id = conn['merchant_id']
        
        # Skip if either node doesn't exist
        if user_id not in user_ids or merchant_id not in merchant_ids:
            continue
        
        # Determine edge color based on risk
        edge_color = '#aaa'  # Default gray
        if conn['flagged_count'] > 0:
            edge_color = '#e74a3b'  # Red for flagged
        elif conn['high_risk_count'] > 0:
            edge_color = '#f6c23e'  # Yellow for high risk
        
        # Calculate risk score for the connection
        risk_score = 0
        if conn['transaction_count'] > 0:
            risk_score = (conn['flagged_count'] * 100 + conn['high_risk_count'] * 80 + 
                         conn['medium_risk_count'] * 50) / conn['transaction_count']
        
        edges.append({
            'id': f"edge_{user_id}_{merchant_id}",
            'source': f"user_{user_id}",
            'target': f"merchant_{merchant_id}",
            'size': min(10, max(1, conn['transaction_count'] / 2)),
            'transactions': conn['transaction_count'],
            'amount': float(conn['total_amount']),
            'avg_amount': float(conn['avg_amount']),
            'max_amount': float(conn['max_amount']),
            'min_amount': float(conn['min_amount']),
            'flagged_count': conn['flagged_count'],
            'high_risk_count': conn['high_risk_count'],
            'medium_risk_count': conn['medium_risk_count'],
            'low_risk_count': conn['low_risk_count'],
            'flagged': conn['flagged_count'] > 0,
            'color': edge_color,
            'risk_score': min(100, risk_score)
        })
    
    # Calculate network metrics
    # 1. Centrality - identify key nodes in the network
    centrality = defaultdict(float)
    for edge in edges:
        source = edge['source']
        target = edge['target']
        weight = edge['transactions']
        centrality[source] += weight
        centrality[target] += weight
    
    # Update node centrality
    for node in nodes:
        node['centrality'] = centrality.get(node['id'], 0)
    
    # 2. Community detection (simplified)
    # Group nodes by risk level as a simple form of community detection
    communities = defaultdict(list)
    for node in nodes:
        communities[node['risk_level']].append(node['id'])
    
    # Calculate statistics
    stats = {
        'total_transactions': transactions.count(),
        'total_users': len(user_ids),
        'total_merchants': len(merchant_ids),
        'total_connections': len(edges),
        'flagged_transactions': transactions.filter(is_flagged=True).count(),
        'high_risk_transactions': transactions.filter(risk_score__gte=80).count(),
        'medium_risk_transactions': transactions.filter(risk_score__gte=50, risk_score__lt=80).count(),
        'low_risk_transactions': transactions.filter(risk_score__lt=50).count(),
        'total_amount': float(transactions.aggregate(Sum('amount'))['amount__sum'] or 0),
        'avg_amount': float(transactions.aggregate(Avg('amount'))['amount__avg'] or 0),
        'max_amount': float(transactions.aggregate(Max('amount'))['amount__max'] or 0),
        'min_amount': float(transactions.aggregate(Min('amount'))['amount__min'] or 0),
    }
    
    # Add layout information
    layout_options = {
        'force': {
            'physics': {
                'enabled': True,
                'barnesHut': {
                    'gravitationalConstant': -2000,
                    'centralGravity': 0.3,
                    'springLength': 95,
                    'springConstant': 0.04,
                    'damping': 0.09
                },
                'stabilization': {
                    'enabled': True,
                    'iterations': 1000
                }
            }
        },
        'circular': {
            'physics': False,
            'layout': {
                'improvedLayout': True,
                'circular': {
                    'enabled': True,
                    'radius': 300
                }
            }
        },
        'hierarchical': {
            'physics': False,
            'layout': {
                'hierarchical': {
                    'enabled': True,
                    'direction': 'UD',
                    'sortMethod': 'directed',
                    'nodeSpacing': 150,
                    'treeSpacing': 200
                }
            }
        }
    }
    
    return JsonResponse({
        'nodes': nodes,
        'edges': edges,
        'stats': stats,
        'communities': dict(communities),
        'layout': layout_options.get(layout, layout_options['force'])
    })
