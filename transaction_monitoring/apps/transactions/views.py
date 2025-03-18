"""
Views for the transactions app.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Transaction, POSTransaction, EcommerceTransaction, WalletTransaction
from .serializers import (
    TransactionSerializer, 
    POSTransactionSerializer, 
    EcommerceTransactionSerializer, 
    WalletTransactionSerializer
)
from .forms import TransactionSearchForm, TransactionReviewForm, TransactionCreateForm
import requests
import json
from django.conf import settings
from apps.core.utils import generate_transaction_id


# Web Views

@login_required
def transaction_list(request):
    """
    View for listing transactions with filtering.
    """
    form = TransactionSearchForm(request.GET)
    transactions = Transaction.objects.all().order_by('-created_at')
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('transaction_id'):
            transactions = transactions.filter(transaction_id__icontains=data['transaction_id'])
        
        if data.get('user_id'):
            transactions = transactions.filter(user_id__icontains=data['user_id'])
        
        if data.get('merchant_id'):
            transactions = transactions.filter(merchant_id__icontains=data['merchant_id'])
        
        if data.get('transaction_type'):
            transactions = transactions.filter(transaction_type=data['transaction_type'])
        
        if data.get('channel'):
            transactions = transactions.filter(channel=data['channel'])
        
        if data.get('status'):
            transactions = transactions.filter(status=data['status'])
        
        if data.get('is_flagged') is not None:
            transactions = transactions.filter(is_flagged=data['is_flagged'])
        
        if data.get('min_amount'):
            transactions = transactions.filter(amount__gte=data['min_amount'])
        
        if data.get('max_amount'):
            transactions = transactions.filter(amount__lte=data['max_amount'])
        
        if data.get('start_date'):
            transactions = transactions.filter(created_at__gte=data['start_date'])
        
        if data.get('end_date'):
            transactions = transactions.filter(created_at__lte=data['end_date'])
    
    # Get fraud detection results for each transaction
    from apps.fraud_engine.models import FraudDetectionResult
    
    # Prefetch fraud detection results to avoid N+1 queries
    transaction_ids = [t.transaction_id for t in transactions]
    fraud_results = {
        result.transaction_id: result 
        for result in FraudDetectionResult.objects.filter(transaction_id__in=transaction_ids)
    }
    
    # Add fraud results to transactions
    for transaction in transactions:
        transaction.fraud_result = fraud_results.get(transaction.transaction_id)
    
    # Calculate statistics
    total_count = transactions.count()
    
    # Count by decision
    approved_count = sum(1 for t in transactions if t.fraud_result and t.fraud_result.decision == 'approve')
    rejected_count = sum(1 for t in transactions if t.fraud_result and t.fraud_result.decision == 'reject')
    flagged_count = sum(1 for t in transactions if t.fraud_result and t.fraud_result.decision == 'review')
    
    # Calculate percentages
    approved_percentage = (approved_count / total_count * 100) if total_count > 0 else 0
    rejected_percentage = (rejected_count / total_count * 100) if total_count > 0 else 0
    flagged_percentage = (flagged_count / total_count * 100) if total_count > 0 else 0
    
    # Pagination
    paginator = Paginator(transactions, 25)  # Show 25 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'transactions': page_obj.object_list,
        'total_count': total_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'flagged_count': flagged_count,
        'approved_percentage': approved_percentage,
        'rejected_percentage': rejected_percentage,
        'flagged_percentage': flagged_percentage,
        'paginator': paginator,
    }
    
    return render(request, 'transactions/list.html', context)


@login_required
def transaction_detail(request, transaction_id):
    """
    View for transaction details.
    """
    transaction = get_object_or_404(Transaction, transaction_id=transaction_id)
    
    # Get the specific transaction type instance
    if transaction.channel == 'pos':
        try:
            transaction = POSTransaction.objects.get(pk=transaction.pk)
        except POSTransaction.DoesNotExist:
            pass
    elif transaction.channel == 'ecommerce':
        try:
            transaction = EcommerceTransaction.objects.get(pk=transaction.pk)
        except EcommerceTransaction.DoesNotExist:
            pass
    elif transaction.channel == 'wallet':
        try:
            transaction = WalletTransaction.objects.get(pk=transaction.pk)
        except WalletTransaction.DoesNotExist:
            pass
    
    # Get fraud detection result
    from apps.fraud_engine.models import FraudDetectionResult
    try:
        fraud_result = FraudDetectionResult.objects.get(transaction_id=transaction_id)
    except FraudDetectionResult.DoesNotExist:
        fraud_result = None
    
    # Handle review form submission
    if request.method == 'POST':
        form = TransactionReviewForm(request.POST)
        if form.is_valid():
            transaction.review_status = form.cleaned_data['review_status']
            transaction.reviewed_by = request.user.username
            transaction.reviewed_at = timezone.now()
            
            # If cleared, update the transaction status
            if form.cleaned_data['review_status'] == 'cleared':
                transaction.is_flagged = False
                transaction.status = 'approved'
            
            # If confirmed fraud, update the transaction status
            if form.cleaned_data['review_status'] == 'confirmed_fraud':
                transaction.is_flagged = True
                transaction.status = 'rejected'
            
            transaction.save()
            messages.success(request, f"Transaction {transaction_id} has been reviewed.")
            return redirect('transactions:detail', transaction_id=transaction_id)
    else:
        form = TransactionReviewForm(initial={
            'review_status': transaction.review_status
        })
    
    context = {
        'transaction': transaction,
        'form': form,
        'fraud_result': fraud_result,
    }
    
    return render(request, 'transactions/detail.html', context)


@login_required
def flagged_transactions(request):
    """
    View for listing flagged transactions.
    """
    transactions = Transaction.objects.filter(is_flagged=True).order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(transactions, 25)  # Show 25 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'title': 'Flagged Transactions',
    }
    
    return render(request, 'transactions/flagged.html', context)


@login_required
def process_transaction(request):
    """
    View for processing a transaction through the fraud detection system.
    """
    if request.method == 'POST':
        # Extract data from the form
        data = {
            'transaction_id': request.POST.get('transaction_id') or generate_transaction_id(),
            'transaction_type': request.POST.get('transaction_type'),
            'channel': request.POST.get('channel'),
            'user_id': request.POST.get('user_id'),
            'amount': float(request.POST.get('amount')),
            'currency': request.POST.get('currency'),
            'merchant_id': request.POST.get('merchant_id') or None,
            'device_id': request.POST.get('device_id') or None,
            'location_data': {
                'city': request.POST.get('city') or None,
                'country': request.POST.get('country') or None,
                'postal_code': request.POST.get('postal_code') or None,
            },
            'payment_method_data': {
                'type': request.POST.get('payment_method_type'),
            },
            'metadata': {
                'notes': request.POST.get('notes') or None,
            }
        }
        
        # Add card details if payment method is credit or debit card
        if data['payment_method_data']['type'] in ['credit_card', 'debit_card']:
            data['payment_method_data']['card_details'] = {
                'card_number': request.POST.get('card_number') or None,
                'cardholder_name': request.POST.get('cardholder_name') or None,
                'expiry_date': request.POST.get('card_expiry') or None,
                'cvv': request.POST.get('cvv') or None,
            }
        
        try:
            # Import the transaction processor
            from .transaction_processor import create_transaction
            
            # Create transaction using the processor
            transaction = create_transaction(data)
            
            # Success message
            messages.success(
                request, 
                f"Transaction processed successfully. Transaction ID: {transaction.transaction_id}"
            )
            
            # Redirect to transaction detail page
            return redirect('transactions:detail', transaction_id=transaction.transaction_id)
            
        except Exception as e:
            messages.error(request, f"Error processing transaction: {str(e)}")
    
    context = {
        'title': 'Process Transaction',
    }
    
    return render(request, 'transactions/process_transaction.html', context)


@login_required
def transaction_create(request):
    """
    View for creating and processing a new transaction through the fraud detection system.
    """
    if request.method == 'POST':
        form = TransactionCreateForm(request.POST)
        if form.is_valid():
            try:
                # Import the transaction processor
                from .transaction_processor import create_transaction
                
                # Create transaction using the processor
                transaction = create_transaction(form.cleaned_data)
                
                # Process the transaction directly (synchronously)
                # Simulate fraud detection pipeline
                
                # 1. Check for high-risk conditions
                is_blocked = False
                
                # Check for high-risk countries
                high_risk_countries = ['NK', 'IR', 'CU']
                if transaction.location_data.get('country') in high_risk_countries:
                    is_blocked = True
                
                # 2. Apply simple rules
                is_flagged = False
                
                # Large transaction rule
                if transaction.amount > 10000:
                    is_flagged = True
                
                # High-risk channel rule
                if transaction.channel == 'E-commerce':
                    is_flagged = True
                
                # 3. ML prediction - simulate a risk score
                import random
                risk_score = random.randint(1, 100)
                
                # Update transaction with results
                transaction.risk_score = risk_score
                transaction.is_flagged = is_flagged or (risk_score > 80)
                transaction.is_blocked = is_blocked
                transaction.save()
                
                # Success message
                messages.success(
                    request, 
                    f"Transaction created and processed through fraud detection. Transaction ID: {transaction.transaction_id}"
                )
                
                # Redirect to transaction detail page
                return redirect('transactions:detail', transaction_id=transaction.transaction_id)
                
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
    else:
        form = TransactionCreateForm()
    
    context = {
        'form': form,
        'title': 'Create and Process Transaction',
        'process_transaction': True,  # Flag to indicate this is for processing
    }
    
    return render(request, 'transactions/create.html', context)


# API Views

class TransactionViewSet(viewsets.ModelViewSet):
    """
    API viewset for transactions.
    """
    queryset = Transaction.objects.all().order_by('-timestamp')
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'channel', 'status', 'is_flagged', 'user_id', 'merchant_id']
    search_fields = ['transaction_id', 'user_id', 'merchant_id']
    ordering_fields = ['timestamp', 'amount', 'risk_score']
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """
        Review a transaction.
        """
        transaction = self.get_object()
        review_status = request.data.get('review_status')
        
        if review_status not in ['pending', 'reviewed', 'cleared', 'confirmed_fraud']:
            return Response({'error': 'Invalid review status'}, status=400)
        
        transaction.review_status = review_status
        transaction.reviewed_by = request.user.username
        transaction.reviewed_at = timezone.now()
        
        # If cleared, update the transaction status
        if review_status == 'cleared':
            transaction.is_flagged = False
            transaction.status = 'approved'
        
        # If confirmed fraud, update the transaction status
        if review_status == 'confirmed_fraud':
            transaction.is_flagged = True
            transaction.status = 'rejected'
        
        transaction.save()
        
        serializer = self.get_serializer(transaction)
        return Response(serializer.data)


class POSTransactionViewSet(viewsets.ModelViewSet):
    """
    API viewset for POS transactions.
    """
    queryset = POSTransaction.objects.all().order_by('-timestamp')
    serializer_class = POSTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_flagged', 'user_id', 'merchant_id', 'terminal_id', 'entry_mode']
    search_fields = ['transaction_id', 'user_id', 'merchant_id', 'terminal_id']
    ordering_fields = ['timestamp', 'amount', 'risk_score']


class EcommerceTransactionViewSet(viewsets.ModelViewSet):
    """
    API viewset for E-commerce transactions.
    """
    queryset = EcommerceTransaction.objects.all().order_by('-timestamp')
    serializer_class = EcommerceTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_flagged', 'user_id', 'merchant_id', 'is_3ds_verified', 'is_billing_shipping_match']
    search_fields = ['transaction_id', 'user_id', 'merchant_id', 'website_url']
    ordering_fields = ['timestamp', 'amount', 'risk_score']


class WalletTransactionViewSet(viewsets.ModelViewSet):
    """
    API viewset for Wallet transactions.
    """
    queryset = WalletTransaction.objects.all().order_by('-timestamp')
    serializer_class = WalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_flagged', 'user_id', 'wallet_id', 'source_type', 'destination_type', 'transaction_purpose', 'is_internal']
    search_fields = ['transaction_id', 'user_id', 'wallet_id', 'source_id', 'destination_id']
    ordering_fields = ['timestamp', 'amount', 'risk_score']