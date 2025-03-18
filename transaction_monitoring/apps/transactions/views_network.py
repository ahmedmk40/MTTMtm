"""
Views for transaction network visualization.
"""

import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator

from .models import Transaction
from .services.network_service import (
    get_transaction_network_data,
    get_user_transaction_network,
    get_merchant_transaction_network,
    detect_unusual_patterns
)


@login_required
def network_dashboard(request):
    """
    Transaction network dashboard.
    """
    # Simplified version for testing
    return render(request, 'transactions/network_dashboard.html', {
        'title': 'Transaction Network',
        'days': 30,
        'min_transactions': 2,
        'max_nodes': 100,
        'patterns': []
    })


@login_required
@require_GET
def network_data(request):
    """
    Get transaction network data for visualization.
    """
    # Get filter parameters
    days = int(request.GET.get('days', 30))
    min_transactions = int(request.GET.get('min_transactions', 2))
    max_nodes = int(request.GET.get('max_nodes', 100))
    
    # Get network data
    network_data = get_transaction_network_data(
        days=days,
        min_transactions=min_transactions,
        max_nodes=max_nodes
    )
    
    return JsonResponse(network_data)


@login_required
def user_network(request, user_id):
    """
    User transaction network visualization.
    """
    # Get filter parameters
    days = int(request.GET.get('days', 30))
    
    # Get user's transactions
    transactions = Transaction.objects.filter(user_id=user_id).order_by('-timestamp')
    
    # Paginate transactions
    paginator = Paginator(transactions, 20)  # 20 transactions per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': f'User Network: {user_id}',
        'user_id': user_id,
        'days': days,
        'page_obj': page_obj
    }
    
    return render(request, 'transactions/user_network.html', context)


@login_required
@require_GET
def user_network_data(request, user_id):
    """
    Get user transaction network data for visualization.
    """
    # Get filter parameters
    days = int(request.GET.get('days', 30))
    
    # Get network data
    network_data = get_user_transaction_network(user_id, days=days)
    
    return JsonResponse(network_data)


@login_required
def merchant_network(request, merchant_id):
    """
    Merchant transaction network visualization.
    """
    # Get filter parameters
    days = int(request.GET.get('days', 30))
    
    # Get merchant's transactions
    transactions = Transaction.objects.filter(merchant_id=merchant_id).order_by('-timestamp')
    
    # Paginate transactions
    paginator = Paginator(transactions, 20)  # 20 transactions per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': f'Merchant Network: {merchant_id}',
        'merchant_id': merchant_id,
        'days': days,
        'page_obj': page_obj
    }
    
    return render(request, 'transactions/merchant_network.html', context)


@login_required
@require_GET
def merchant_network_data(request, merchant_id):
    """
    Get merchant transaction network data for visualization.
    """
    # Get filter parameters
    days = int(request.GET.get('days', 30))
    
    # Get network data
    network_data = get_merchant_transaction_network(merchant_id, days=days)
    
    return JsonResponse(network_data)


@login_required
@require_GET
def unusual_patterns(request):
    """
    Get unusual patterns in the transaction network.
    """
    # Get filter parameters
    days = int(request.GET.get('days', 30))
    
    # Get unusual patterns
    patterns = detect_unusual_patterns(days=days)
    
    return JsonResponse({'patterns': patterns})