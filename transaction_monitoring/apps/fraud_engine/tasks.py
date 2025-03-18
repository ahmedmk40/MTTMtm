"""
Celery tasks for the Fraud Engine app.
"""

import time
import logging
import json
from transaction_monitoring.celery_app import app
from django.utils import timezone
from django.db import transaction as db_transaction
from apps.transactions.models import Transaction, POSTransaction, EcommerceTransaction, WalletTransaction
from .models import FraudDetectionResult
from apps.core.utils import CustomJSONEncoder
from .services.decision_service import make_fraud_decision
from .services.block_service import check_blocklist
from apps.rule_engine.services.evaluator import evaluate_rules
from apps.velocity_engine.services import check_velocity
from apps.ml_engine.services.prediction_service import get_fraud_prediction
from apps.aml.services.monitoring_service import check_aml_risk

logger = logging.getLogger(__name__)


@app.task
def process_transaction(transaction_id, transaction_type, channel):
    """
    Process a transaction through the fraud detection pipeline.
    
    Args:
        transaction_id: The ID of the transaction to process
        transaction_type: The type of transaction (acquiring, wallet)
        channel: The channel of the transaction (pos, ecommerce, wallet)
    """
    logger.info(f"Processing transaction {transaction_id} for fraud detection")
    start_time = time.time()
    
    try:
        # Get the transaction object based on channel
        if channel == 'pos':
            transaction = POSTransaction.objects.get(transaction_id=transaction_id)
        elif channel == 'ecommerce':
            transaction = EcommerceTransaction.objects.get(transaction_id=transaction_id)
        elif channel == 'wallet':
            transaction = WalletTransaction.objects.get(transaction_id=transaction_id)
        else:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
        
        # Initialize results dictionary
        results = {
            'block_check': {},
            'rule_engine': {},
            'velocity_engine': {},
            'ml_engine': {},
            'aml_engine': {},
            'triggered_rules': [],
        }
        
        # Step 1: Check blocklist
        block_result = check_blocklist(transaction)
        results['block_check'] = block_result
        
        # If blocked, update transaction and return early
        if block_result.get('is_blocked', False):
            with db_transaction.atomic():
                transaction.status = 'rejected'
                transaction.is_flagged = True
                transaction.flag_reason = block_result.get('reason', 'Blocked entity')
                transaction.risk_score = 100.0  # Maximum risk score
                transaction.save()
            
            # Create fraud detection result
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            FraudDetectionResult.objects.create(
                transaction_id=transaction_id,
                risk_score=100.0,
                is_fraudulent=True,
                decision='reject',
                processing_time=processing_time,
                block_check_result=block_result,
                rule_engine_result={},
                velocity_engine_result={},
                ml_engine_result={},
                aml_engine_result={},
                triggered_rules=[]
            )
            
            logger.info(f"Transaction {transaction_id} blocked: {block_result.get('reason')}")
            return
        
        # Step 2: Evaluate rules
        rule_result = evaluate_rules(transaction)
        results['rule_engine'] = rule_result
        results['triggered_rules'] = rule_result.get('triggered_rules', [])
        
        # Step 3: Check velocity
        velocity_result = check_velocity(transaction)
        results['velocity_engine'] = velocity_result
        
        # Add velocity triggered rules to the list
        if velocity_result.get('triggered_rules'):
            results['triggered_rules'].extend(velocity_result.get('triggered_rules', []))
        
        # Step 4: Get ML prediction
        ml_result = get_fraud_prediction(transaction)
        results['ml_engine'] = ml_result
        
        # Step 5: Check AML risk
        aml_result = check_aml_risk(transaction)
        results['aml_engine'] = aml_result
        
        # Add AML triggered rules to the list
        if aml_result.get('triggered_rules'):
            results['triggered_rules'].extend(aml_result.get('triggered_rules', []))
        
        # Step 6: Make final decision
        decision_result = make_fraud_decision(transaction, results)
        
        # Step 7: Update transaction with decision
        with db_transaction.atomic():
            transaction.status = decision_result.get('status', 'pending')
            transaction.is_flagged = decision_result.get('is_flagged', False)
            transaction.flag_reason = decision_result.get('flag_reason', '')
            transaction.risk_score = decision_result.get('risk_score', 0.0)
            transaction.save()
        
        # Step 8: Create fraud detection result
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Serialize JSON fields using our custom encoder
        block_check_json = json.dumps(results['block_check'], cls=CustomJSONEncoder)
        rule_engine_json = json.dumps(results['rule_engine'], cls=CustomJSONEncoder)
        velocity_engine_json = json.dumps(results['velocity_engine'], cls=CustomJSONEncoder)
        ml_engine_json = json.dumps(results['ml_engine'], cls=CustomJSONEncoder)
        aml_engine_json = json.dumps(results['aml_engine'], cls=CustomJSONEncoder)
        triggered_rules_json = json.dumps(results['triggered_rules'], cls=CustomJSONEncoder)
        
        # Create the fraud detection result with pre-serialized JSON data
        FraudDetectionResult.objects.create(
            transaction_id=transaction_id,
            risk_score=decision_result.get('risk_score', 0.0),
            is_fraudulent=decision_result.get('is_fraudulent', False),
            decision=decision_result.get('decision', 'approve'),
            processing_time=processing_time,
            block_check_result=json.loads(block_check_json),
            rule_engine_result=json.loads(rule_engine_json),
            velocity_engine_result=json.loads(velocity_engine_json),
            ml_engine_result=json.loads(ml_engine_json),
            aml_engine_result=json.loads(aml_engine_json),
            triggered_rules=json.loads(triggered_rules_json)
        )
        
        logger.info(f"Transaction {transaction_id} processed: {decision_result.get('decision')} in {processing_time:.2f}ms")
        
        # Step 9: If flagged for review, create a case
        if decision_result.get('is_flagged', False):
            # Use Celery to create the fraud case asynchronously
            create_fraud_case.delay(transaction_id, decision_result, results)
    
    except Exception as e:
        logger.error(f"Error processing transaction {transaction_id}: {str(e)}", exc_info=True)
        
        # Try to update transaction status if possible
        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
            transaction.status = 'error'
            transaction.save()
        except Exception:
            pass


@app.task
def create_fraud_case(transaction_id, decision_result, detection_results):
    """
    Create a fraud case for a flagged transaction.
    
    Args:
        transaction_id: The ID of the transaction
        decision_result: The decision result from the fraud engine
        detection_results: The detailed results from all detection engines
    """
    from .models import FraudCase
    import uuid
    
    try:
        # Get the transaction
        transaction = Transaction.objects.get(transaction_id=transaction_id)
        
        # Generate a case ID
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        
        # Determine priority based on risk score
        risk_score = decision_result.get('risk_score', 0.0)
        if risk_score >= 90:
            priority = 'critical'
        elif risk_score >= 70:
            priority = 'high'
        elif risk_score >= 50:
            priority = 'medium'
        else:
            priority = 'low'
        
        # Create a title based on triggered rules
        triggered_rules = detection_results.get('triggered_rules', [])
        if triggered_rules:
            title = f"Fraud alert: {', '.join(rule.get('name', 'Unknown rule') for rule in triggered_rules[:3])}"
            if len(triggered_rules) > 3:
                title += f" and {len(triggered_rules) - 3} more"
        else:
            title = f"Suspicious transaction {transaction_id}"
        
        # Create description
        description = f"""
Transaction ID: {transaction_id}
User ID: {transaction.user_id}
Amount: {transaction.amount} {transaction.currency}
Channel: {transaction.get_channel_display()}
Risk Score: {risk_score}

Triggered Rules:
"""
        for rule in triggered_rules:
            description += f"- {rule.get('name', 'Unknown rule')}: {rule.get('description', '')}\n"
        
        # Create the case
        FraudCase.objects.create(
            case_id=case_id,
            user_id=transaction.user_id,
            title=title,
            description=description,
            status='open',
            priority=priority,
            related_transactions=[transaction_id]
        )
        
        logger.info(f"Created fraud case {case_id} for transaction {transaction_id}")
        
        # TODO: Send notification to fraud analysts (implement in notifications app)
    
    except Exception as e:
        logger.error(f"Error creating fraud case for transaction {transaction_id}: {str(e)}", exc_info=True)