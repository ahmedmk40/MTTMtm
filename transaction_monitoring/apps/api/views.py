"""
Views for the API app.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db import connection
from django.conf import settings
import redis
import json
import uuid
from datetime import datetime

from apps.core.utils import generate_transaction_id
from apps.transactions.models import (
    Transaction,
    POSTransaction,
    EcommerceTransaction,
    WalletTransaction
)
from apps.transactions.serializers import (
    POSTransactionSerializer,
    EcommerceTransactionSerializer,
    WalletTransactionSerializer
)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_transaction(request):
    """
    Process a new transaction.
    
    This endpoint accepts transaction data, validates it, creates the appropriate
    transaction record, and initiates the fraud detection process.
    """
    data = request.data
    
    # Validate required fields
    required_fields = ['transaction_type', 'channel', 'amount', 'currency', 'user_id']
    for field in required_fields:
        if field not in data:
            return Response(
                {'error': f'Missing required field: {field}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Generate transaction ID if not provided
    if 'transaction_id' not in data:
        data['transaction_id'] = generate_transaction_id()
    
    # Add timestamp if not provided
    if 'timestamp' not in data:
        data['timestamp'] = timezone.now().isoformat()
    
    # Process based on channel
    channel = data.get('channel')
    
    if channel == 'pos':
        serializer = POSTransactionSerializer(data=data)
    elif channel == 'ecommerce':
        serializer = EcommerceTransactionSerializer(data=data)
    elif channel == 'wallet':
        serializer = WalletTransactionSerializer(data=data)
    else:
        return Response(
            {'error': f'Invalid channel: {channel}. Must be one of: pos, ecommerce, wallet'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if serializer.is_valid():
        # Save the transaction
        transaction = serializer.save()
        
        # Process the transaction synchronously
        try:
            # Import the necessary modules
            from apps.rule_engine.services import apply_rules
            from apps.ml_engine.services.prediction_service import get_fraud_prediction
            
            # Apply rules
            rule_results = apply_rules(transaction)
            
            # Get ML prediction
            ml_results = get_fraud_prediction(transaction)
            
            # Update transaction with results
            transaction.risk_score = ml_results.get('risk_score', 0)
            transaction.is_flagged = rule_results.get('is_flagged', False) or ml_results.get('is_fraudulent', False)
            
            if transaction.is_flagged:
                transaction.flag_reason = rule_results.get('flag_reason') or 'ML model flagged as high risk'
                transaction.status = 'flagged'
            else:
                transaction.status = 'approved'
            
            transaction.save()
            
            # Return the transaction data with processing results
            return Response(
                {
                    'status': 'success',
                    'message': 'Transaction processed successfully',
                    'transaction_id': transaction.transaction_id,
                    'transaction_status': transaction.status,
                    'risk_score': float(transaction.risk_score),
                    'is_flagged': transaction.is_flagged,
                    'flag_reason': transaction.flag_reason,
                    'ml_results': {
                        'model_name': ml_results.get('model_name'),
                        'model_version': ml_results.get('model_version'),
                        'models_used': ml_results.get('models_used', []),
                        'execution_time': ml_results.get('execution_time')
                    }
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            # Log the error but still return success for the transaction creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error processing transaction {transaction.transaction_id}: {str(e)}", exc_info=True)
            
            return Response(
                {
                    'status': 'partial_success',
                    'message': f'Transaction created but processing failed: {str(e)}',
                    'transaction_id': transaction.transaction_id,
                    'transaction_status': transaction.status,
                },
                status=status.HTTP_201_CREATED
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint for API monitoring.
    """
    # Check database connection
    db_status = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        db_status = False
    
    # Check Redis connection
    redis_status = True
    try:
        r = redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
    except Exception:
        redis_status = False
    
    # Overall status
    status_ok = db_status and redis_status
    
    # Response data
    data = {
        "status": "healthy" if status_ok else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "redis": "connected" if redis_status else "disconnected",
        "timestamp": datetime.now().isoformat(),
        "version": getattr(settings, "VERSION", "1.0.0"),
    }
    
    return Response(data, status=status.HTTP_200_OK if status_ok else status.HTTP_503_SERVICE_UNAVAILABLE)