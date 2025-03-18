"""
Views for the Rule Engine app.
"""

import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Max, Min
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.urls import reverse

from .models import Rule, RuleSet, RuleExecution
from .services.compiler import compile_rule_condition
from .services.evaluator import evaluate_condition
from .rules.amount_rules import AMOUNT_RULES
from .rules.geographic_rules import GEOGRAPHIC_RULES
from .rules.card_rules import CARD_RULES
from .rules.aml_rules import AML_RULES

logger = logging.getLogger(__name__)


@login_required
def rule_list(request):
    """
    Display a list of rules with filtering and sorting.
    """
    # Get filter parameters
    rule_type = request.GET.get('rule_type', '')
    is_active = request.GET.get('is_active', '')
    search_query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', 'priority')
    
    # Start with all rules
    rules = Rule.objects.all()
    
    # Apply filters
    if rule_type:
        rules = rules.filter(rule_type=rule_type)
    
    if is_active:
        is_active_bool = is_active.lower() == 'true'
        rules = rules.filter(is_active=is_active_bool)
    
    if search_query:
        rules = rules.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(condition__icontains=search_query)
        )
    
    # Apply sorting
    if sort_by.startswith('-'):
        sort_field = sort_by[1:]
        sort_direction = '-'
    else:
        sort_field = sort_by
        sort_direction = ''
    
    valid_sort_fields = ['name', 'rule_type', 'priority', 'hit_count', 'created_at', 'last_triggered']
    if sort_field in valid_sort_fields:
        rules = rules.order_by(f'{sort_direction}{sort_field}')
    else:
        # Default sort by priority (higher first) then name
        rules = rules.order_by('-priority', 'name')
    
    # Get rule statistics
    rule_stats = {
        'total': rules.count(),
        'active': rules.filter(is_active=True).count(),
        'inactive': rules.filter(is_active=False).count(),
        'by_type': rules.values('rule_type').annotate(count=Count('id')),
        'avg_hit_count': rules.aggregate(avg=Avg('hit_count'))['avg'] or 0,
        'max_hit_count': rules.aggregate(max=Max('hit_count'))['max'] or 0,
    }
    
    # Paginate the results
    paginator = Paginator(rules, 20)  # 20 rules per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Prepare context
    context = {
        'page_obj': page_obj,
        'rule_stats': rule_stats,
        'rule_types': Rule.RULE_TYPE_CHOICES,
        'filter_rule_type': rule_type,
        'filter_is_active': is_active,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    
    return render(request, 'rule_engine/list.html', context)


@login_required
def rule_detail(request, rule_id):
    """
    Display details of a specific rule.
    """
    rule = get_object_or_404(Rule, id=rule_id)
    
    # Get recent executions
    recent_executions = RuleExecution.objects.filter(rule=rule).order_by('-created_at')[:50]
    
    # Calculate execution statistics
    execution_stats = {
        'total': RuleExecution.objects.filter(rule=rule).count(),
        'triggered': RuleExecution.objects.filter(rule=rule, triggered=True).count(),
        'not_triggered': RuleExecution.objects.filter(rule=rule, triggered=False).count(),
        'avg_execution_time': RuleExecution.objects.filter(rule=rule).aggregate(avg=Avg('execution_time'))['avg'] or 0,
        'max_execution_time': RuleExecution.objects.filter(rule=rule).aggregate(max=Max('execution_time'))['max'] or 0,
        'min_execution_time': RuleExecution.objects.filter(rule=rule).aggregate(min=Min('execution_time'))['min'] or 0,
    }
    
    # Calculate trigger rate
    if execution_stats['total'] > 0:
        execution_stats['trigger_rate'] = (execution_stats['triggered'] / execution_stats['total']) * 100
    else:
        execution_stats['trigger_rate'] = 0
    
    # Get rule sets this rule belongs to
    rule_sets = rule.rule_sets.all()
    
    context = {
        'rule': rule,
        'recent_executions': recent_executions,
        'execution_stats': execution_stats,
        'rule_sets': rule_sets,
    }
    
    return render(request, 'rule_engine/detail.html', context)


@login_required
def rule_create(request):
    """
    Create a new rule.
    """
    if request.method == 'POST':
        # Extract form data
        name = request.POST.get('name')
        description = request.POST.get('description')
        rule_type = request.POST.get('rule_type')
        condition = request.POST.get('condition')
        action = request.POST.get('action')
        risk_score = request.POST.get('risk_score')
        priority = request.POST.get('priority')
        is_active = request.POST.get('is_active') == 'on'
        applies_to_pos = request.POST.get('applies_to_pos') == 'on'
        applies_to_ecommerce = request.POST.get('applies_to_ecommerce') == 'on'
        applies_to_wallet = request.POST.get('applies_to_wallet') == 'on'
        
        # Validate the condition
        is_valid, error_message = compile_rule_condition(condition)
        
        if not is_valid:
            messages.error(request, f"Invalid rule condition: {error_message}")
            # Return to form with entered data
            context = {
                'rule_types': Rule.RULE_TYPE_CHOICES,
                'action_choices': Rule.ACTION_CHOICES,
                'form_data': request.POST,
            }
            return render(request, 'rule_engine/create.html', context)
        
        # Get merchant-specific settings
        merchant_specific = request.POST.get('merchant_specific') == 'on'
        included_merchants = request.POST.get('included_merchants', '')
        excluded_merchants = request.POST.get('excluded_merchants', '')
        
        # Parse merchant lists (comma-separated values)
        included_merchants_list = [m.strip() for m in included_merchants.split(',')] if included_merchants else []
        excluded_merchants_list = [m.strip() for m in excluded_merchants.split(',')] if excluded_merchants else []
        
        # Create the rule
        rule = Rule.objects.create(
            name=name,
            description=description,
            rule_type=rule_type,
            condition=condition,
            action=action,
            risk_score=risk_score,
            priority=priority,
            is_active=is_active,
            applies_to_pos=applies_to_pos,
            applies_to_ecommerce=applies_to_ecommerce,
            applies_to_wallet=applies_to_wallet,
            merchant_specific=merchant_specific,
            included_merchants=included_merchants_list,
            excluded_merchants=excluded_merchants_list,
            created_by=request.user.username,
        )
        
        messages.success(request, f"Rule '{name}' created successfully.")
        return redirect('rule_engine:detail', rule_id=rule.id)
    
    # GET request - show the form
    context = {
        'rule_types': Rule.RULE_TYPE_CHOICES,
        'action_choices': Rule.ACTION_CHOICES,
    }
    return render(request, 'rule_engine/create.html', context)


@login_required
def rule_edit(request, rule_id):
    """
    Edit an existing rule.
    """
    rule = get_object_or_404(Rule, id=rule_id)
    
    if request.method == 'POST':
        # Extract form data
        name = request.POST.get('name')
        description = request.POST.get('description')
        rule_type = request.POST.get('rule_type')
        condition = request.POST.get('condition')
        action = request.POST.get('action')
        risk_score = request.POST.get('risk_score')
        priority = request.POST.get('priority')
        is_active = request.POST.get('is_active') == 'on'
        applies_to_pos = request.POST.get('applies_to_pos') == 'on'
        applies_to_ecommerce = request.POST.get('applies_to_ecommerce') == 'on'
        applies_to_wallet = request.POST.get('applies_to_wallet') == 'on'
        
        # Validate the condition
        is_valid, error_message = compile_rule_condition(condition)
        
        if not is_valid:
            messages.error(request, f"Invalid rule condition: {error_message}")
            # Return to form with entered data
            context = {
                'rule': rule,
                'rule_types': Rule.RULE_TYPE_CHOICES,
                'action_choices': Rule.ACTION_CHOICES,
                'form_data': request.POST,
            }
            return render(request, 'rule_engine/edit.html', context)
        
        # Get merchant-specific settings
        merchant_specific = request.POST.get('merchant_specific') == 'on'
        included_merchants = request.POST.get('included_merchants', '')
        excluded_merchants = request.POST.get('excluded_merchants', '')
        
        # Parse merchant lists (comma-separated values)
        included_merchants_list = [m.strip() for m in included_merchants.split(',')] if included_merchants else []
        excluded_merchants_list = [m.strip() for m in excluded_merchants.split(',')] if excluded_merchants else []
        
        # Update the rule
        rule.name = name
        rule.description = description
        rule.rule_type = rule_type
        rule.condition = condition
        rule.action = action
        rule.risk_score = risk_score
        rule.priority = priority
        rule.is_active = is_active
        rule.applies_to_pos = applies_to_pos
        rule.applies_to_ecommerce = applies_to_ecommerce
        rule.applies_to_wallet = applies_to_wallet
        rule.merchant_specific = merchant_specific
        rule.included_merchants = included_merchants_list
        rule.excluded_merchants = excluded_merchants_list
        rule.last_modified_by = request.user.username
        rule.version += 1
        rule.save()
        
        messages.success(request, f"Rule '{name}' updated successfully.")
        return redirect('rule_engine:detail', rule_id=rule.id)
    
    # GET request - show the form with current data
    context = {
        'rule': rule,
        'rule_types': Rule.RULE_TYPE_CHOICES,
        'action_choices': Rule.ACTION_CHOICES,
    }
    return render(request, 'rule_engine/edit.html', context)


@login_required
@require_POST
def rule_toggle_active(request, rule_id):
    """
    Toggle the active status of a rule.
    """
    rule = get_object_or_404(Rule, id=rule_id)
    rule.is_active = not rule.is_active
    rule.last_modified_by = request.user.username
    rule.save()
    
    status = 'activated' if rule.is_active else 'deactivated'
    messages.success(request, f"Rule '{rule.name}' {status} successfully.")
    
    # Return to the referring page or the rule detail page
    return redirect(request.META.get('HTTP_REFERER', reverse('rule_engine:detail', args=[rule_id])))


@login_required
def rule_test(request, rule_id=None):
    """
    Test a rule against sample transaction data.
    """
    rule = None
    if rule_id:
        rule = get_object_or_404(Rule, id=rule_id)
    
    if request.method == 'POST':
        # Get the rule condition and test data
        condition = request.POST.get('condition')
        test_data_json = request.POST.get('test_data')
        
        try:
            # Parse the test data
            test_data = json.loads(test_data_json)
            
            # Validate the condition
            is_valid, error_message = compile_rule_condition(condition)
            
            if not is_valid:
                return JsonResponse({
                    'success': False,
                    'message': f"Invalid rule condition: {error_message}"
                })
            
            # Evaluate the condition
            start_time = timezone.now()
            triggered, condition_values = evaluate_condition(condition, test_data)
            execution_time = (timezone.now() - start_time).total_seconds() * 1000  # in milliseconds
            
            return JsonResponse({
                'success': True,
                'triggered': triggered,
                'condition_values': condition_values,
                'execution_time': execution_time
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': "Invalid JSON in test data"
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Error evaluating condition: {str(e)}"
            })
    
    # Prepare sample transaction data for different channels
    sample_transactions = {
        'pos': {
            'transaction_id': 'tx_pos_sample',
            'transaction_type': 'acquiring',
            'channel': 'pos',
            'amount': 500.0,
            'currency': 'USD',
            'user_id': 'user_123',
            'merchant_id': 'merchant_456',
            'timestamp': timezone.now().timestamp(),
            'device_id': 'device_789',
            'location_data': {
                'country': 'US',
                'city': 'New York',
                'zip': '10001',
                'ip_address': '192.168.1.1'
            },
            'payment_method_data': {
                'type': 'credit_card',
                'card_details': {
                    'card_number': '4111111111111111',
                    'expiry_month': '12',
                    'expiry_year': '2025',
                    'cardholder_name': 'John Doe',
                    'is_new': False
                }
            },
            'mcc': '5411',
            'terminal_id': 'term_123',
            'entry_mode': 'chip',
            'terminal_type': 'standard',
            'attendance': 'attended',
            'condition': 'card_present'
        },
        'ecommerce': {
            'transaction_id': 'tx_ecom_sample',
            'transaction_type': 'acquiring',
            'channel': 'ecommerce',
            'amount': 300.0,
            'currency': 'EUR',
            'user_id': 'user_123',
            'merchant_id': 'merchant_456',
            'timestamp': timezone.now().timestamp(),
            'device_id': 'device_789',
            'location_data': {
                'country': 'DE',
                'city': 'Berlin',
                'zip': '10115',
                'ip_address': '192.168.1.1'
            },
            'payment_method_data': {
                'type': 'credit_card',
                'card_details': {
                    'card_number': '4111111111111111',
                    'expiry_month': '12',
                    'expiry_year': '2025',
                    'cardholder_name': 'John Doe',
                    'is_new': False
                }
            },
            'website_url': 'https://example.com/checkout',
            'is_3ds_verified': True,
            'device_fingerprint': 'fp_123456',
            'shipping_address': {
                'street': '123 Main St',
                'city': 'Berlin',
                'state': 'Berlin',
                'postal_code': '10115',
                'country': 'DE'
            },
            'billing_address': {
                'street': '123 Main St',
                'city': 'Berlin',
                'state': 'Berlin',
                'postal_code': '10115',
                'country': 'DE'
            },
            'is_billing_shipping_match': True
        },
        'wallet': {
            'transaction_id': 'tx_wallet_sample',
            'transaction_type': 'wallet',
            'channel': 'wallet',
            'amount': 200.0,
            'currency': 'GBP',
            'user_id': 'user_123',
            'timestamp': timezone.now().timestamp(),
            'device_id': 'device_789',
            'location_data': {
                'country': 'GB',
                'city': 'London',
                'zip': 'SW1A 1AA',
                'ip_address': '192.168.1.1'
            },
            'wallet_id': 'wallet_123',
            'source_type': 'wallet',
            'destination_type': 'bank_account',
            'source_id': 'wallet_123',
            'destination_id': 'bank_456',
            'transaction_purpose': 'withdrawal',
            'is_internal': False
        }
    }
    
    # Get example rules
    example_rules = {
        'amount': AMOUNT_RULES,
        'geographic': GEOGRAPHIC_RULES,
        'card': CARD_RULES,
        'aml': AML_RULES
    }
    
    context = {
        'rule': rule,
        'sample_transactions': sample_transactions,
        'example_rules': example_rules,
        'rule_types': Rule.RULE_TYPE_CHOICES,
        'action_choices': Rule.ACTION_CHOICES,
    }
    
    return render(request, 'rule_engine/test.html', context)


@login_required
def ruleset_list(request):
    """
    Display a list of rule sets.
    """
    rulesets = RuleSet.objects.all().order_by('name')
    
    # Get statistics
    ruleset_stats = {
        'total': rulesets.count(),
        'active': rulesets.filter(is_active=True).count(),
        'inactive': rulesets.filter(is_active=False).count(),
        'avg_rules': rulesets.annotate(rule_count=Count('rules')).aggregate(avg=Avg('rule_count'))['avg'] or 0,
    }
    
    context = {
        'rulesets': rulesets,
        'ruleset_stats': ruleset_stats,
    }
    
    return render(request, 'rule_engine/ruleset_list.html', context)


@login_required
def ruleset_detail(request, ruleset_id):
    """
    Display details of a specific rule set.
    """
    ruleset = get_object_or_404(RuleSet, id=ruleset_id)
    
    # Get rules in this set
    rules = ruleset.rules.all().order_by('-priority', 'name')
    
    # Get rule statistics
    rule_stats = {
        'total': rules.count(),
        'active': rules.filter(is_active=True).count(),
        'inactive': rules.filter(is_active=False).count(),
        'by_type': rules.values('rule_type').annotate(count=Count('id')),
        'by_action': rules.values('action').annotate(count=Count('id')),
    }
    
    context = {
        'ruleset': ruleset,
        'rules': rules,
        'rule_stats': rule_stats,
    }
    
    return render(request, 'rule_engine/ruleset_detail.html', context)


@login_required
def ruleset_create(request):
    """
    Create a new rule set.
    """
    if request.method == 'POST':
        # Extract form data
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'
        rule_ids = request.POST.getlist('rules')
        
        # Create the rule set
        ruleset = RuleSet.objects.create(
            name=name,
            description=description,
            is_active=is_active,
            created_by=request.user.username,
        )
        
        # Add rules to the set
        if rule_ids:
            rules = Rule.objects.filter(id__in=rule_ids)
            ruleset.rules.add(*rules)
        
        messages.success(request, f"Rule set '{name}' created successfully.")
        return redirect('rule_engine:ruleset_detail', ruleset_id=ruleset.id)
    
    # GET request - show the form
    rules = Rule.objects.filter(is_active=True).order_by('rule_type', 'name')
    
    context = {
        'rules': rules,
        'rule_types': Rule.RULE_TYPE_CHOICES,
    }
    
    return render(request, 'rule_engine/ruleset_create.html', context)


@login_required
def ruleset_edit(request, ruleset_id):
    """
    Edit an existing rule set.
    """
    ruleset = get_object_or_404(RuleSet, id=ruleset_id)
    
    if request.method == 'POST':
        # Extract form data
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'
        rule_ids = request.POST.getlist('rules')
        
        # Update the rule set
        ruleset.name = name
        ruleset.description = description
        ruleset.is_active = is_active
        ruleset.last_modified_by = request.user.username
        ruleset.save()
        
        # Update rules in the set
        ruleset.rules.clear()
        if rule_ids:
            rules = Rule.objects.filter(id__in=rule_ids)
            ruleset.rules.add(*rules)
        
        messages.success(request, f"Rule set '{name}' updated successfully.")
        return redirect('rule_engine:ruleset_detail', ruleset_id=ruleset.id)
    
    # GET request - show the form with current data
    rules = Rule.objects.filter(is_active=True).order_by('rule_type', 'name')
    selected_rule_ids = ruleset.rules.values_list('id', flat=True)
    
    context = {
        'ruleset': ruleset,
        'rules': rules,
        'selected_rule_ids': list(selected_rule_ids),
        'rule_types': Rule.RULE_TYPE_CHOICES,
    }
    
    return render(request, 'rule_engine/ruleset_edit.html', context)


@login_required
@require_POST
def ruleset_toggle_active(request, ruleset_id):
    """
    Toggle the active status of a rule set.
    """
    ruleset = get_object_or_404(RuleSet, id=ruleset_id)
    ruleset.is_active = not ruleset.is_active
    ruleset.last_modified_by = request.user.username
    ruleset.save()
    
    status = 'activated' if ruleset.is_active else 'deactivated'
    messages.success(request, f"Rule set '{ruleset.name}' {status} successfully.")
    
    # Return to the referring page or the rule set detail page
    return redirect(request.META.get('HTTP_REFERER', reverse('rule_engine:ruleset_detail', args=[ruleset_id])))


@login_required
def execution_list(request):
    """
    Display a list of rule executions.
    """
    # Get filter parameters
    rule_id = request.GET.get('rule_id', '')
    triggered = request.GET.get('triggered', '')
    transaction_id = request.GET.get('transaction_id', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Start with all executions
    executions = RuleExecution.objects.all()
    
    # Apply filters
    if rule_id:
        executions = executions.filter(rule_id=rule_id)
    
    if triggered:
        triggered_bool = triggered.lower() == 'true'
        executions = executions.filter(triggered=triggered_bool)
    
    if transaction_id:
        executions = executions.filter(transaction_id__icontains=transaction_id)
    
    if start_date:
        executions = executions.filter(created_at__gte=start_date)
    
    if end_date:
        executions = executions.filter(created_at__lte=end_date)
    
    # Order by most recent first
    executions = executions.order_by('-created_at')
    
    # Get execution statistics
    execution_stats = {
        'total': executions.count(),
        'triggered': executions.filter(triggered=True).count(),
        'not_triggered': executions.filter(triggered=False).count(),
        'avg_execution_time': executions.aggregate(avg=Avg('execution_time'))['avg'] or 0,
    }
    
    # Calculate trigger rates
    if execution_stats['total'] > 0:
        execution_stats['trigger_rate'] = (execution_stats['triggered'] / execution_stats['total']) * 100
        execution_stats['not_triggered_rate'] = (execution_stats['not_triggered'] / execution_stats['total']) * 100
    else:
        execution_stats['trigger_rate'] = 0
        execution_stats['not_triggered_rate'] = 0
    
    # Paginate the results
    paginator = Paginator(executions, 50)  # 50 executions per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all rules for the filter dropdown
    rules = Rule.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'execution_stats': execution_stats,
        'rules': rules,
        'filter_rule_id': rule_id,
        'filter_triggered': triggered,
        'filter_transaction_id': transaction_id,
        'filter_start_date': start_date,
        'filter_end_date': end_date,
    }
    
    return render(request, 'rule_engine/execution_list.html', context)


@login_required
def execution_detail(request, execution_id):
    """
    Display details of a specific rule execution.
    """
    execution = get_object_or_404(RuleExecution, id=execution_id)
    
    # Get related executions for the same transaction
    related_executions = RuleExecution.objects.filter(
        transaction_id=execution.transaction_id
    ).exclude(id=execution_id).order_by('-created_at')
    
    context = {
        'execution': execution,
        'related_executions': related_executions,
    }
    
    return render(request, 'rule_engine/execution_detail.html', context)


@login_required
def dashboard(request):
    """
    Display a dashboard with rule engine statistics and metrics.
    """
    # Get time range filter
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timezone.timedelta(days=days)
    
    # Get rule statistics
    rules = Rule.objects.all()
    rule_stats = {
        'total': rules.count(),
        'active': rules.filter(is_active=True).count(),
        'inactive': rules.filter(is_active=False).count(),
        'by_type': list(rules.values('rule_type').annotate(count=Count('id')).order_by('rule_type')),
        'by_action': list(rules.values('action').annotate(count=Count('id')).order_by('action')),
        'top_triggered': list(rules.order_by('-hit_count')[:10].values('id', 'name', 'hit_count', 'rule_type')),
    }
    
    # Get execution statistics
    executions = RuleExecution.objects.filter(created_at__gte=start_date)
    execution_stats = {
        'total': executions.count(),
        'triggered': executions.filter(triggered=True).count(),
        'not_triggered': executions.filter(triggered=False).count(),
        'avg_execution_time': executions.aggregate(avg=Avg('execution_time'))['avg'] or 0,
    }
    
    # Calculate trigger rate
    if execution_stats['total'] > 0:
        execution_stats['trigger_rate'] = (execution_stats['triggered'] / execution_stats['total']) * 100
    else:
        execution_stats['trigger_rate'] = 0
    
    # Get daily execution counts for chart
    daily_executions = []
    daily_triggers = []
    
    for i in range(days):
        day = timezone.now() - timezone.timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        day_executions = executions.filter(created_at__gte=day_start, created_at__lte=day_end)
        day_count = day_executions.count()
        day_triggered = day_executions.filter(triggered=True).count()
        
        daily_executions.append({
            'date': day_start.strftime('%Y-%m-%d'),
            'count': day_count
        })
        
        daily_triggers.append({
            'date': day_start.strftime('%Y-%m-%d'),
            'count': day_triggered
        })
    
    # Reverse the lists to show oldest to newest
    daily_executions.reverse()
    daily_triggers.reverse()
    
    # Get ruleset statistics
    rulesets = RuleSet.objects.all()
    ruleset_stats = {
        'total': rulesets.count(),
        'active': rulesets.filter(is_active=True).count(),
        'inactive': rulesets.filter(is_active=False).count(),
    }
    
    context = {
        'rule_stats': rule_stats,
        'execution_stats': execution_stats,
        'ruleset_stats': ruleset_stats,
        'daily_executions': daily_executions,
        'daily_triggers': daily_triggers,
        'days': days,
    }
    
    return render(request, 'rule_engine/dashboard.html', context)