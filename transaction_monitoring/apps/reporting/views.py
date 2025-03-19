"""
Views for the reporting app.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Sum, Avg, Min, Max, F, Q, Case, When, Value, FloatField, ExpressionWrapper, StdDev
from django.db.models.functions import TruncDay, TruncHour, ExtractHour, Cast, Coalesce
from django.utils import timezone
from django.contrib import messages
import csv
import io
import json
import random
import numpy as np
from datetime import timedelta, datetime
from apps.transactions.models import Transaction
from apps.transactions.merchant import Merchant
from apps.transactions.device import Device
from apps.transactions.ip_address import IPAddress
from django.contrib.auth import get_user_model
User = get_user_model()
from apps.fraud_engine.models import FraudDetectionResult, FraudCase
from apps.fraud_engine.risk_score import RiskScore
from apps.aml.models import AMLAlert
from .forms import ReportFilterForm, CustomReportForm, ScheduledReportForm
from .models import ScheduledReport, CustomReport


@login_required
def report_list(request):
    """
    View for listing available reports.
    """
    return render(request, 'reports/list.html')


@login_required
def merchant_report(request):
    """
    View for merchant transaction volume and performance reports.
    """
    form = ReportFilterForm(request.GET)
    
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Sample merchant metrics data
    merchant_metrics = [
        {
            'merchant_id': 'merchant_001',
            'merchant__name': 'Acme Corporation',
            'total_transactions': 1250,
            'total_volume': 125000.00,
            'approved_transactions': 1150,
            'declined_transactions': 100,
            'flagged_transactions': 25,
            'avg_transaction_amount': 100.00,
            'approval_rate': 92.0,
            'decline_rate': 8.0,
            'avg_risk_score': 25.5
        },
        {
            'merchant_id': 'merchant_002',
            'merchant__name': 'XYZ Retail',
            'total_transactions': 980,
            'total_volume': 98000.00,
            'approved_transactions': 900,
            'declined_transactions': 80,
            'flagged_transactions': 15,
            'avg_transaction_amount': 100.00,
            'approval_rate': 91.8,
            'decline_rate': 8.2,
            'avg_risk_score': 30.2
        },
        {
            'merchant_id': 'merchant_003',
            'merchant__name': 'Global Traders',
            'total_transactions': 750,
            'total_volume': 112500.00,
            'approved_transactions': 650,
            'declined_transactions': 100,
            'flagged_transactions': 35,
            'avg_transaction_amount': 150.00,
            'approval_rate': 86.7,
            'decline_rate': 13.3,
            'avg_risk_score': 45.8
        },
        {
            'merchant_id': 'merchant_004',
            'merchant__name': 'Tech Solutions',
            'total_transactions': 500,
            'total_volume': 75000.00,
            'approved_transactions': 475,
            'declined_transactions': 25,
            'flagged_transactions': 10,
            'avg_transaction_amount': 150.00,
            'approval_rate': 95.0,
            'decline_rate': 5.0,
            'avg_risk_score': 18.3
        },
        {
            'merchant_id': 'merchant_005',
            'merchant__name': 'High Risk Ventures',
            'total_transactions': 300,
            'total_volume': 60000.00,
            'approved_transactions': 200,
            'declined_transactions': 100,
            'flagged_transactions': 50,
            'avg_transaction_amount': 200.00,
            'approval_rate': 66.7,
            'decline_rate': 33.3,
            'avg_risk_score': 75.2
        }
    ]
    
    # Sample daily volume data
    daily_volume = []
    for i in range(30):
        day = end_date - timedelta(days=30-i)
        for merchant in merchant_metrics[:2]:  # Only include top 2 merchants
            volume = random.randint(1000, 5000)
            approved = int(volume * merchant['approval_rate'] / 100)
            declined = volume - approved
            daily_volume.append({
                'day': day,
                'merchant_id': merchant['merchant_id'],
                'merchant__name': merchant['merchant__name'],
                'total': volume,
                'volume': volume * 100,  # Assuming $100 average transaction
                'approved': approved,
                'declined': declined
            })
    
    # Identify high-risk merchants (avg risk score > 70)
    high_risk_merchants = [m for m in merchant_metrics if m['avg_risk_score'] > 70]
    
    # Identify merchants with unusual decline rates (> 30%)
    high_decline_merchants = [m for m in merchant_metrics if m['decline_rate'] > 30]
    
    context = {
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'merchant_metrics': merchant_metrics,
        'daily_volume': daily_volume,
        'high_risk_merchants': high_risk_merchants,
        'high_decline_merchants': high_decline_merchants,
        'selected_merchant_id': request.GET.get('merchant_id')
    }
    
    return render(request, 'reports/merchant.html', context)


@login_required
def country_report(request):
    """
    View for country transaction analysis.
    """
    form = ReportFilterForm(request.GET)
    
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Sample country metrics data
    country_metrics = [
        {
            'country_code': 'US',
            'total_transactions': 2500,
            'total_volume': 250000.00,
            'approved_transactions': 2350,
            'declined_transactions': 150,
            'flagged_transactions': 50,
            'avg_transaction_amount': 100.00,
            'approval_rate': 94.0,
            'decline_rate': 6.0,
            'avg_risk_score': 20.5
        },
        {
            'country_code': 'GB',
            'total_transactions': 1200,
            'total_volume': 120000.00,
            'approved_transactions': 1100,
            'declined_transactions': 100,
            'flagged_transactions': 30,
            'avg_transaction_amount': 100.00,
            'approval_rate': 91.7,
            'decline_rate': 8.3,
            'avg_risk_score': 25.8
        },
        {
            'country_code': 'CA',
            'total_transactions': 800,
            'total_volume': 80000.00,
            'approved_transactions': 750,
            'declined_transactions': 50,
            'flagged_transactions': 15,
            'avg_transaction_amount': 100.00,
            'approval_rate': 93.8,
            'decline_rate': 6.2,
            'avg_risk_score': 22.3
        },
        {
            'country_code': 'AU',
            'total_transactions': 600,
            'total_volume': 60000.00,
            'approved_transactions': 550,
            'declined_transactions': 50,
            'flagged_transactions': 10,
            'avg_transaction_amount': 100.00,
            'approval_rate': 91.7,
            'decline_rate': 8.3,
            'avg_risk_score': 24.1
        },
        {
            'country_code': 'RU',
            'total_transactions': 300,
            'total_volume': 30000.00,
            'approved_transactions': 200,
            'declined_transactions': 100,
            'flagged_transactions': 60,
            'avg_transaction_amount': 100.00,
            'approval_rate': 66.7,
            'decline_rate': 33.3,
            'avg_risk_score': 72.5
        },
        {
            'country_code': 'NG',
            'total_transactions': 150,
            'total_volume': 15000.00,
            'approved_transactions': 90,
            'declined_transactions': 60,
            'flagged_transactions': 40,
            'avg_transaction_amount': 100.00,
            'approval_rate': 60.0,
            'decline_rate': 40.0,
            'avg_risk_score': 80.2
        }
    ]
    
    # Sample daily volume data
    daily_volume = []
    for i in range(30):
        day = end_date - timedelta(days=30-i)
        for country in country_metrics[:3]:  # Only include top 3 countries
            volume = random.randint(500, 2000)
            approved = int(volume * country['approval_rate'] / 100)
            declined = volume - approved
            daily_volume.append({
                'day': day,
                'country_code': country['country_code'],
                'total': volume,
                'volume': volume * 100,  # Assuming $100 average transaction
                'approved': approved,
                'declined': declined
            })
    
    # Identify high-risk countries (avg risk score > 70)
    high_risk_countries = [c for c in country_metrics if c['avg_risk_score'] > 70]
    
    # Identify countries with unusual decline rates (> 30%)
    high_decline_countries = [c for c in country_metrics if c['decline_rate'] > 30]
    
    context = {
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'country_metrics': country_metrics,
        'daily_volume': daily_volume,
        'high_risk_countries': high_risk_countries,
        'high_decline_countries': high_decline_countries,
        'selected_country_code': request.GET.get('country_code')
    }
    
    return render(request, 'reports/country.html', context)


@login_required
def user_report(request):
    """
    View for user transaction activity and risk analysis.
    """
    form = ReportFilterForm(request.GET)
    
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Sample user metrics data
    user_metrics = [
        {
            'user_id': 'user_001',
            'username': 'johndoe',
            'total_transactions': 120,
            'total_volume': 12000.00,
            'approved_transactions': 110,
            'declined_transactions': 10,
            'flagged_transactions': 5,
            'avg_transaction_amount': 100.00,
            'approval_rate': 91.7,
            'decline_rate': 8.3,
            'avg_risk_score': 25.5
        },
        {
            'user_id': 'user_002',
            'username': 'janedoe',
            'total_transactions': 85,
            'total_volume': 8500.00,
            'approved_transactions': 80,
            'declined_transactions': 5,
            'flagged_transactions': 2,
            'avg_transaction_amount': 100.00,
            'approval_rate': 94.1,
            'decline_rate': 5.9,
            'avg_risk_score': 18.2
        },
        {
            'user_id': 'user_003',
            'username': 'bobsmith',
            'total_transactions': 65,
            'total_volume': 6500.00,
            'approved_transactions': 60,
            'declined_transactions': 5,
            'flagged_transactions': 3,
            'avg_transaction_amount': 100.00,
            'approval_rate': 92.3,
            'decline_rate': 7.7,
            'avg_risk_score': 22.7
        },
        {
            'user_id': 'user_004',
            'username': 'alicejones',
            'total_transactions': 45,
            'total_volume': 4500.00,
            'approved_transactions': 42,
            'declined_transactions': 3,
            'flagged_transactions': 1,
            'avg_transaction_amount': 100.00,
            'approval_rate': 93.3,
            'decline_rate': 6.7,
            'avg_risk_score': 15.8
        },
        {
            'user_id': 'user_005',
            'username': 'riskyuser',
            'total_transactions': 30,
            'total_volume': 6000.00,
            'approved_transactions': 20,
            'declined_transactions': 10,
            'flagged_transactions': 8,
            'avg_transaction_amount': 200.00,
            'approval_rate': 66.7,
            'decline_rate': 33.3,
            'avg_risk_score': 82.5
        }
    ]
    
    # Sample daily activity data
    daily_activity = []
    for i in range(30):
        day = end_date - timedelta(days=30-i)
        active_users = random.randint(10, 20)
        transactions = random.randint(50, 100)
        daily_activity.append({
            'day': day,
            'active_users': active_users,
            'transactions': transactions,
            'volume': transactions * 100  # Assuming $100 average transaction
        })
    
    # Identify high-risk users (avg risk score > 70)
    high_risk_users = [u for u in user_metrics if u['avg_risk_score'] > 70]
    
    # Identify users with unusual activity (high decline rate > 30%)
    unusual_activity_users = [
        {
            'user_id': u['user_id'],
            'username': u['username'],
            'activity_description': f"Decline rate of {u['decline_rate']}% (threshold: 30%)"
        }
        for u in user_metrics if u['decline_rate'] > 30
    ]
    
    # Add users with unusual transaction amounts
    for u in user_metrics:
        if u['avg_transaction_amount'] > 150 and not any(x['user_id'] == u['user_id'] for x in unusual_activity_users):
            unusual_activity_users.append({
                'user_id': u['user_id'],
                'username': u['username'],
                'activity_description': f"Average transaction amount of ${u['avg_transaction_amount']} (threshold: $150)"
            })
    
    # Calculate metrics
    active_users = len(user_metrics)
    total_transactions = sum(u['total_transactions'] for u in user_metrics)
    total_volume = sum(u['total_volume'] for u in user_metrics)
    avg_transactions_per_user = total_transactions / active_users if active_users > 0 else 0
    avg_volume_per_user = total_volume / active_users if active_users > 0 else 0
    new_users = random.randint(1, 5)  # Sample data
    
    # Risk distribution
    risk_distribution = {
        'low': len([u for u in user_metrics if u['avg_risk_score'] <= 25]),
        'medium_low': len([u for u in user_metrics if 25 < u['avg_risk_score'] <= 50]),
        'medium_high': len([u for u in user_metrics if 50 < u['avg_risk_score'] <= 75]),
        'high': len([u for u in user_metrics if u['avg_risk_score'] > 75])
    }
    
    context = {
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'user_metrics': user_metrics,
        'daily_activity': daily_activity,
        'high_risk_users': high_risk_users,
        'unusual_activity_users': unusual_activity_users,
        'active_users': active_users,
        'avg_transactions_per_user': avg_transactions_per_user,
        'avg_volume_per_user': avg_volume_per_user,
        'new_users': new_users,
        'risk_distribution': risk_distribution,
        'selected_user_id': request.GET.get('user_id')
    }
    
    return render(request, 'reports/user.html', context)


@login_required
def device_report(request):
    """
    View for device usage analysis.
    """
    form = ReportFilterForm(request.GET)
    
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Sample device metrics data
    device_metrics = [
        {
            'device_id': 'device_001',
            'type': 'mobile',
            'os': 'iOS',
            'browser': 'Safari',
            'transactions': 250,
            'users': 3,
            'last_seen': timezone.now() - timedelta(hours=2),
            'risk_score': 15.5
        },
        {
            'device_id': 'device_002',
            'type': 'desktop',
            'os': 'Windows',
            'browser': 'Chrome',
            'transactions': 180,
            'users': 2,
            'last_seen': timezone.now() - timedelta(hours=5),
            'risk_score': 12.8
        },
        {
            'device_id': 'device_003',
            'type': 'mobile',
            'os': 'Android',
            'browser': 'Chrome',
            'transactions': 120,
            'users': 1,
            'last_seen': timezone.now() - timedelta(hours=8),
            'risk_score': 22.3
        },
        {
            'device_id': 'device_004',
            'type': 'tablet',
            'os': 'iOS',
            'browser': 'Safari',
            'transactions': 85,
            'users': 1,
            'last_seen': timezone.now() - timedelta(hours=12),
            'risk_score': 18.7
        },
        {
            'device_id': 'device_005',
            'type': 'desktop',
            'os': 'macOS',
            'browser': 'Safari',
            'transactions': 65,
            'users': 1,
            'last_seen': timezone.now() - timedelta(hours=24),
            'risk_score': 10.2
        },
        {
            'device_id': 'device_006',
            'type': 'mobile',
            'os': 'Android',
            'browser': 'Firefox',
            'transactions': 45,
            'users': 1,
            'last_seen': timezone.now() - timedelta(days=2),
            'risk_score': 25.6
        },
        {
            'device_id': 'device_007',
            'type': 'desktop',
            'os': 'Linux',
            'browser': 'Firefox',
            'transactions': 30,
            'users': 1,
            'last_seen': timezone.now() - timedelta(days=3),
            'risk_score': 15.9
        },
        {
            'device_id': 'device_008',
            'type': 'mobile',
            'os': 'iOS',
            'browser': 'Chrome',
            'transactions': 25,
            'users': 1,
            'last_seen': timezone.now() - timedelta(days=5),
            'risk_score': 20.1
        },
        {
            'device_id': 'device_009',
            'type': 'tablet',
            'os': 'Android',
            'browser': 'Chrome',
            'transactions': 15,
            'users': 1,
            'last_seen': timezone.now() - timedelta(days=7),
            'risk_score': 22.8
        },
        {
            'device_id': 'device_010',
            'type': 'desktop',
            'os': 'Windows',
            'browser': 'Edge',
            'transactions': 10,
            'users': 1,
            'last_seen': timezone.now() - timedelta(days=10),
            'risk_score': 35.4
        },
        {
            'device_id': 'device_011',
            'type': 'mobile',
            'os': 'Android',
            'browser': 'Chrome',
            'transactions': 5,
            'users': 5,
            'last_seen': timezone.now() - timedelta(days=15),
            'risk_score': 85.7
        }
    ]
    
    # Sample daily activity data
    daily_activity = []
    for i in range(30):
        day = end_date - timedelta(days=30-i)
        mobile = random.randint(10, 30)
        desktop = random.randint(5, 20)
        tablet = random.randint(2, 10)
        daily_activity.append({
            'day': day,
            'mobile': mobile,
            'desktop': desktop,
            'tablet': tablet,
            'total': mobile + desktop + tablet
        })
    
    # Device type distribution
    device_types = [
        {'type': 'mobile', 'count': sum(1 for d in device_metrics if d['type'] == 'mobile')},
        {'type': 'desktop', 'count': sum(1 for d in device_metrics if d['type'] == 'desktop')},
        {'type': 'tablet', 'count': sum(1 for d in device_metrics if d['type'] == 'tablet')}
    ]
    
    # OS distribution
    os_list = list(set(d['os'] for d in device_metrics))
    os_distribution = [
        {'os': os, 'count': sum(1 for d in device_metrics if d['os'] == os)}
        for os in os_list
    ]
    
    # Browser distribution
    browser_list = list(set(d['browser'] for d in device_metrics))
    browser_distribution = [
        {'browser': browser, 'count': sum(1 for d in device_metrics if d['browser'] == browser)}
        for browser in browser_list
    ]
    
    # Identify high-risk devices (risk score > 70)
    high_risk_devices = [d for d in device_metrics if d['risk_score'] > 70]
    
    # Identify devices with unusual activity (multiple users)
    unusual_activity_devices = [
        {
            'device_id': d['device_id'],
            'activity_description': f"Used by {d['users']} different users (threshold: 3)"
        }
        for d in device_metrics if d['users'] > 3
    ]
    
    # Calculate metrics
    unique_devices = len(device_metrics)
    total_transactions = sum(d['transactions'] for d in device_metrics)
    avg_transactions_per_device = total_transactions / unique_devices if unique_devices > 0 else 0
    new_devices = random.randint(1, 5)  # Sample data
    flagged_devices = len(high_risk_devices) + len(unusual_activity_devices)
    
    context = {
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'device_metrics': device_metrics,
        'daily_activity': daily_activity,
        'device_types': device_types,
        'os_distribution': os_distribution,
        'browser_distribution': browser_distribution,
        'high_risk_devices': high_risk_devices,
        'unusual_activity_devices': unusual_activity_devices,
        'unique_devices': unique_devices,
        'avg_transactions_per_device': avg_transactions_per_device,
        'new_devices': new_devices,
        'flagged_devices': flagged_devices,
        'selected_device_id': request.GET.get('device_id')
    }
    
    return render(request, 'reports/device.html', context)


@login_required
def ip_address_report(request):
    """
    View for IP address analysis.
    """
    form = ReportFilterForm(request.GET)
    
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    ip_filter = None
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
            
        # Get IP address filter if provided
        ip_filter = data.get('ip_address')
    
    # Sample IP metrics data
    ip_metrics_all = [
        {
            'ip_address': '192.168.1.1',
            'country': 'United States',
            'city': 'New York',
            'transactions': 250,
            'users': 3,
            'last_seen': timezone.now() - timedelta(hours=2),
            'risk_score': 15.5
        },
        {
            'ip_address': '10.0.0.1',
            'country': 'United Kingdom',
            'city': 'London',
            'transactions': 180,
            'users': 2,
            'last_seen': timezone.now() - timedelta(hours=5),
            'risk_score': 22.8
        },
        {
            'ip_address': '172.16.0.1',
            'country': 'Canada',
            'city': 'Toronto',
            'transactions': 120,
            'users': 1,
            'last_seen': timezone.now() - timedelta(hours=8),
            'risk_score': 18.3
        },
        {
            'ip_address': '192.168.2.1',
            'country': 'Australia',
            'city': 'Sydney',
            'transactions': 85,
            'users': 1,
            'last_seen': timezone.now() - timedelta(hours=12),
            'risk_score': 20.7
        },
        {
            'ip_address': '10.1.1.1',
            'country': 'Germany',
            'city': 'Berlin',
            'transactions': 65,
            'users': 1,
            'last_seen': timezone.now() - timedelta(hours=24),
            'risk_score': 25.2
        },
        {
            'ip_address': '172.16.1.1',
            'country': 'France',
            'city': 'Paris',
            'transactions': 45,
            'users': 1,
            'last_seen': timezone.now() - timedelta(days=2),
            'risk_score': 30.6
        },
        {
            'ip_address': '192.168.3.1',
            'country': 'Japan',
            'city': 'Tokyo',
            'transactions': 30,
            'users': 1,
            'last_seen': timezone.now() - timedelta(days=3),
            'risk_score': 15.9
        },
        {
            'ip_address': '10.2.2.2',
            'country': 'Russia',
            'city': 'Moscow',
            'transactions': 25,
            'users': 1,
            'last_seen': timezone.now() - timedelta(days=5),
            'risk_score': 75.1
        },
        {
            'ip_address': '172.16.2.2',
            'country': 'China',
            'city': 'Beijing',
            'transactions': 15,
            'users': 1,
            'last_seen': timezone.now() - timedelta(days=7),
            'risk_score': 68.8
        },
        {
            'ip_address': '192.168.4.4',
            'country': 'Nigeria',
            'city': 'Lagos',
            'transactions': 10,
            'users': 1,
            'last_seen': timezone.now() - timedelta(days=10),
            'risk_score': 82.4
        },
        {
            'ip_address': '10.3.3.3',
            'country': 'United States',
            'city': 'Los Angeles',
            'transactions': 5,
            'users': 5,
            'last_seen': timezone.now() - timedelta(days=15),
            'risk_score': 85.7
        }
    ]
    # Apply IP address filter if provided
    if ip_filter:
        ip_metrics = [ip for ip in ip_metrics_all if ip_filter.lower() in ip["ip_address"].lower()]
    else:
        ip_metrics = ip_metrics_all
    
    # Sample daily activity data
    daily_activity = []
    for i in range(30):
        day = end_date - timedelta(days=30-i)
        unique_ips = random.randint(5, 15)
        transactions = random.randint(20, 50)
        daily_activity.append({
            'day': day,
            'unique_ips': unique_ips,
            'transactions': transactions
        })
    
    # Country distribution
    countries = list(set(ip['country'] for ip in ip_metrics_all))
    country_distribution = [
        {'country': country, 'count': sum(1 for ip in ip_metrics_all if ip['country'] == country)}
        for country in countries
    ]
    
    # Sort by count descending
    country_distribution.sort(key=lambda x: x['count'], reverse=True)
    
    # Identify high-risk IPs (risk score > 70)
    high_risk_ips = [ip for ip in ip_metrics_all if ip['risk_score'] > 70]
    
    # Identify IPs with unusual activity (multiple users)
    unusual_activity_ips = [
        {
            'ip_address': ip['ip_address'],
            'activity_description': f"Used by {ip['users']} different users (threshold: 3)"
        }
        for ip in ip_metrics_all if ip['users'] > 3
    ]
    
    # Identify high-risk countries
    high_risk_countries = [
        {
            'country': country,
            'ip_count': sum(1 for ip in ip_metrics_all if ip['country'] == country and ip['risk_score'] > 70)
        }
        for country in set(ip['country'] for ip in high_risk_ips)
    ]
    
    # Filter out countries with no high-risk IPs
    high_risk_countries = [c for c in high_risk_countries if c['ip_count'] > 0]
    
    # Calculate metrics
    unique_ips = len(ip_metrics_all)
    country_count = len(countries)
    total_transactions = sum(ip['transactions'] for ip in ip_metrics_all)
    avg_transactions_per_ip = total_transactions / unique_ips if unique_ips > 0 else 0
    flagged_ips = len(high_risk_ips) + len(unusual_activity_ips)
    
    # Risk distribution
    risk_distribution = {
        'low': len([ip for ip in ip_metrics_all if ip['risk_score'] <= 25]),
        'medium_low': len([ip for ip in ip_metrics_all if 25 < ip['risk_score'] <= 50]),
        'medium_high': len([ip for ip in ip_metrics_all if 50 < ip['risk_score'] <= 75]),
        'high': len([ip for ip in ip_metrics_all if ip['risk_score'] > 75])
    }
    
    context = {
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'ip_metrics': ip_metrics,
        'daily_activity': daily_activity,
        'country_distribution': country_distribution,
        'high_risk_ips': high_risk_ips,
        'unusual_activity_ips': unusual_activity_ips,
        'high_risk_countries': high_risk_countries,
        'unique_ips': unique_ips,
        'country_count': country_count,
        'avg_transactions_per_ip': avg_transactions_per_ip,
        'flagged_ips': flagged_ips,
        'risk_distribution': risk_distribution,
        'selected_ip_address': request.GET.get('ip_address')
    }
    
    return render(request, 'reports/ip_address.html', context)


@login_required
def volume_report(request):
    """
    View for transaction volume analysis.
    """
    form = ReportFilterForm(request.GET)
    
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Sample volume metrics
    total_transactions = 5000
    total_volume = 500000.00
    avg_transaction_amount = 100.00
    max_transaction_amount = 5000.00
    
    # Sample daily volume data
    daily_volume = []
    for i in range(30):
        day = end_date - timedelta(days=30-i)
        count = random.randint(100, 200)
        volume = count * 100  # Assuming $100 average transaction
        daily_volume.append({
            'day': day,
            'count': count,
            'volume': volume,
            'avg_amount': volume / count
        })
    
    # Sample volume by transaction type
    volume_by_type = [
        {
            'transaction_type': 'purchase',
            'count': 3500,
            'volume': 350000.00,
            'percentage': 70.0
        },
        {
            'transaction_type': 'refund',
            'count': 500,
            'volume': 50000.00,
            'percentage': 10.0
        },
        {
            'transaction_type': 'authorization',
            'count': 800,
            'volume': 80000.00,
            'percentage': 16.0
        },
        {
            'transaction_type': 'capture',
            'count': 200,
            'volume': 20000.00,
            'percentage': 4.0
        }
    ]
    
    # Sample volume by channel
    volume_by_channel = [
        {
            'channel': 'web',
            'count': 2500,
            'volume': 250000.00,
            'percentage': 50.0
        },
        {
            'channel': 'mobile_app',
            'count': 1500,
            'volume': 150000.00,
            'percentage': 30.0
        },
        {
            'channel': 'pos',
            'count': 800,
            'volume': 80000.00,
            'percentage': 16.0
        },
        {
            'channel': 'api',
            'count': 200,
            'volume': 20000.00,
            'percentage': 4.0
        }
    ]
    
    # Sample volume by status
    volume_by_status = [
        {
            'status': 'approved',
            'count': 4600,
            'volume': 460000.00,
            'percentage': 92.0
        },
        {
            'status': 'rejected',
            'count': 400,
            'volume': 40000.00,
            'percentage': 8.0
        }
    ]
    
    # Sample hourly distribution
    hourly_distribution = []
    for hour in range(24):
        if hour < 6:
            # Low volume during early morning hours
            count = random.randint(20, 50)
        elif hour < 12:
            # Medium volume during morning hours
            count = random.randint(150, 250)
        elif hour < 18:
            # High volume during afternoon hours
            count = random.randint(250, 350)
        else:
            # Medium volume during evening hours
            count = random.randint(100, 200)
        
        hourly_distribution.append({
            'hour': hour,
            'count': count,
            'volume': count * 100,  # Assuming $100 average transaction
            'percentage': (count / 5000) * 100  # Percentage of total transactions
        })
    
    context = {
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'total_transactions': total_transactions,
        'total_volume': total_volume,
        'avg_transaction_amount': avg_transaction_amount,
        'max_transaction_amount': max_transaction_amount,
        'daily_volume': daily_volume,
        'volume_by_type': volume_by_type,
        'volume_by_channel': volume_by_channel,
        'volume_by_status': volume_by_status,
        'hourly_distribution': hourly_distribution
    }
    
    return render(request, 'reports/volume.html', context)


@login_required
def risk_analysis_report(request):
    """
    View for comprehensive risk analysis.
    """
    form = ReportFilterForm(request.GET)
    
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Sample risk metrics
    avg_risk_score = 35.8
    low_risk_percentage = 65.2
    medium_risk_percentage = 28.5
    high_risk_percentage = 6.3
    
    # Sample risk alerts
    risk_alerts = [
        {
            'title': 'Unusual Spike in High-Risk Transactions',
            'message': 'High-risk transactions increased by 15% in the last 24 hours',
            'level': 'danger'
        },
        {
            'title': 'Unusual Spike in Decline Rates',
            'message': 'Decline rates increased by 18% in the last 12 hours',
            'level': 'danger'
        },
        {
            'title': 'New Risk Pattern Detected',
            'message': 'Multiple transactions from high-risk countries with unusual amounts',
            'level': 'warning'
        },
        {
            'title': 'Velocity Alert',
            'message': '3 users showing unusual transaction velocity patterns',
            'level': 'warning'
        }
    ]
    
    # Sample daily risk scores
    daily_risk_scores = []
    for i in range(30):
        day = end_date - timedelta(days=30-i)
        avg_score = random.uniform(30, 40)
        high_risk_percentage = random.uniform(5, 8)
        daily_risk_scores.append({
            'day': day,
            'avg_score': avg_score,
            'high_risk_percentage': high_risk_percentage
        })
    
    # Sample entity risk distribution
    entity_risk_distribution = [
        {'type': 'User', 'avg_score': 32.5, 'count': 500},
        {'type': 'Merchant', 'avg_score': 28.7, 'count': 120},
        {'type': 'Device', 'avg_score': 35.2, 'count': 350},
        {'type': 'IP Address', 'avg_score': 42.8, 'count': 280},
        {'type': 'Country', 'avg_score': 38.4, 'count': 45}
    ]
    
    # Sample risk distribution
    risk_distribution = {
        'low': low_risk_percentage,
        'medium_low': medium_risk_percentage / 2,
        'medium_high': medium_risk_percentage / 2,
        'high': high_risk_percentage
    }
    
    # Sample risk factors
    risk_factors = [
        {
            'name': 'High-Risk Country',
            'category': 'Location',
            'impact': 'High',
            'frequency': 8.5,
            'score_contribution': 25.3,
            'trend': 'up'
        },
        {
            'name': 'Unusual Transaction Amount',
            'category': 'Amount',
            'impact': 'Medium',
            'frequency': 12.7,
            'score_contribution': 18.6,
            'trend': 'stable'
        },
        {
            'name': 'Velocity Pattern',
            'category': 'Behavior',
            'impact': 'High',
            'frequency': 5.2,
            'score_contribution': 22.8,
            'trend': 'up'
        },
        {
            'name': 'Device Switching',
            'category': 'Device',
            'impact': 'Medium',
            'frequency': 7.8,
            'score_contribution': 15.4,
            'trend': 'stable'
        },
        {
            'name': 'IP Address Mismatch',
            'category': 'Location',
            'impact': 'Medium',
            'frequency': 9.3,
            'score_contribution': 16.7,
            'trend': 'down'
        },
        {
            'name': 'New Account',
            'category': 'History',
            'impact': 'Low',
            'frequency': 15.6,
            'score_contribution': 10.2,
            'trend': 'stable'
        },
        {
            'name': 'Time of Day',
            'category': 'Behavior',
            'impact': 'Low',
            'frequency': 18.3,
            'score_contribution': 8.5,
            'trend': 'down'
        }
    ]
    
    # Sample high-risk entities
    high_risk_entities = [
        {
            'type': 'User',
            'id': 'user_005',
            'name': 'riskyuser',
            'risk_score': 82.5,
            'transactions': 30,
            'top_risk_factors': 'High-Risk Country, Velocity Pattern'
        },
        {
            'type': 'IP Address',
            'id': '10.3.3.3',
            'name': 'United States, Los Angeles',
            'risk_score': 85.7,
            'transactions': 5,
            'top_risk_factors': 'Multiple Users, Unusual Amount'
        },
        {
            'type': 'IP Address',
            'id': '192.168.4.4',
            'name': 'Nigeria, Lagos',
            'risk_score': 82.4,
            'transactions': 10,
            'top_risk_factors': 'High-Risk Country, Unusual Amount'
        },
        {
            'type': 'Device',
            'id': 'device_011',
            'name': 'Android Mobile',
            'risk_score': 85.7,
            'transactions': 5,
            'top_risk_factors': 'Multiple Users, Device Switching'
        },
        {
            'type': 'Country',
            'id': 'NG',
            'name': 'Nigeria',
            'risk_score': 80.2,
            'transactions': 150,
            'top_risk_factors': 'High Decline Rate, Fraud History'
        }
    ]
    
    context = {
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'avg_risk_score': avg_risk_score,
        'low_risk_percentage': low_risk_percentage,
        'medium_risk_percentage': medium_risk_percentage,
        'high_risk_percentage': high_risk_percentage,
        'risk_alerts': risk_alerts,
        'daily_risk_scores': daily_risk_scores,
        'entity_risk_distribution': entity_risk_distribution,
        'risk_distribution': risk_distribution,
        'risk_factors': risk_factors,
        'high_risk_entities': high_risk_entities
    }
    
    return render(request, 'reports/risk_analysis.html', context)


@login_required
def merchant_volume_api(request):
    """
    API endpoint for merchant volume data.
    """
    # Sample data
    data = {
        'start_date': (timezone.now() - timedelta(days=30)).isoformat(),
        'end_date': timezone.now().isoformat(),
        'daily_volume': [
            {
                'date': (timezone.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                'merchant_id': 'merchant_001',
                'merchant_name': 'Acme Corporation',
                'total': random.randint(100, 200),
                'volume': random.randint(10000, 20000),
                'approved': random.randint(90, 180),
                'declined': random.randint(5, 20)
            }
            for i in range(30)
        ]
    }
    
    return JsonResponse(data)


@login_required
def country_volume_api(request):
    """
    API endpoint for country volume data.
    """
    # Sample data
    data = {
        'start_date': (timezone.now() - timedelta(days=30)).isoformat(),
        'end_date': timezone.now().isoformat(),
        'country_metrics': [
            {
                'country_code': 'US',
                'total_transactions': 2500,
                'total_volume': 250000.00,
                'approved_transactions': 2350,
                'declined_transactions': 150,
                'approval_rate': 94.0,
                'avg_risk_score': 20.5
            },
            {
                'country_code': 'GB',
                'total_transactions': 1200,
                'total_volume': 120000.00,
                'approved_transactions': 1100,
                'declined_transactions': 100,
                'approval_rate': 91.7,
                'avg_risk_score': 25.8
            },
            {
                'country_code': 'CA',
                'total_transactions': 800,
                'total_volume': 80000.00,
                'approved_transactions': 750,
                'declined_transactions': 50,
                'approval_rate': 93.8,
                'avg_risk_score': 22.3
            }
        ]
    }
    
    return JsonResponse(data)


@login_required
def user_activity_api(request):
    """
    API endpoint for user activity data.
    """
    # Sample data
    data = {
        'start_date': (timezone.now() - timedelta(days=30)).isoformat(),
        'end_date': timezone.now().isoformat(),
        'daily_activity': [
            {
                'date': (timezone.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                'user_id': 'user_001',
                'username': 'johndoe',
                'total': random.randint(5, 15),
                'volume': random.randint(500, 1500),
                'approved': random.randint(4, 14),
                'declined': random.randint(0, 2),
                'flagged': random.randint(0, 1)
            }
            for i in range(30)
        ]
    }
    
    return JsonResponse(data)


@login_required
def device_distribution_api(request):
    """
    API endpoint for device distribution data.
    """
    # Sample data
    data = {
        'start_date': (timezone.now() - timedelta(days=30)).isoformat(),
        'end_date': timezone.now().isoformat(),
        'device_types': [
            {
                'type': 'mobile',
                'count': 2500,
                'percentage': 50.0
            },
            {
                'type': 'desktop',
                'count': 1500,
                'percentage': 30.0
            },
            {
                'type': 'tablet',
                'count': 1000,
                'percentage': 20.0
            }
        ],
        'os_distribution': [
            {
                'os': 'iOS',
                'count': 1500,
                'percentage': 30.0
            },
            {
                'os': 'Android',
                'count': 1000,
                'percentage': 20.0
            },
            {
                'os': 'Windows',
                'count': 1000,
                'percentage': 20.0
            },
            {
                'os': 'macOS',
                'count': 500,
                'percentage': 10.0
            },
            {
                'os': 'Linux',
                'count': 1000,
                'percentage': 20.0
            }
        ],
        'browser_distribution': [
            {
                'browser': 'Chrome',
                'count': 2000,
                'percentage': 40.0
            },
            {
                'browser': 'Safari',
                'count': 1500,
                'percentage': 30.0
            },
            {
                'browser': 'Firefox',
                'count': 500,
                'percentage': 10.0
            },
            {
                'browser': 'Edge',
                'count': 500,
                'percentage': 10.0
            },
            {
                'browser': 'Other',
                'count': 500,
                'percentage': 10.0
            }
        ]
    }
    
    return JsonResponse(data)


@login_required
def ip_risk_scores_api(request):
    """
    API endpoint for IP risk score data.
    """
    # Sample data
    data = {
        'start_date': (timezone.now() - timedelta(days=30)).isoformat(),
        'end_date': timezone.now().isoformat(),
        'ip_metrics': [
            {
                'ip_address': '192.168.1.1',
                'country': 'United States',
                'city': 'New York',
                'total_transactions': 100,
                'avg_risk_score': 25.5,
                'high_risk_transactions': 5,
                'high_risk_percentage': 5.0
            },
            {
                'ip_address': '10.0.0.1',
                'country': 'United Kingdom',
                'city': 'London',
                'total_transactions': 80,
                'avg_risk_score': 30.2,
                'high_risk_transactions': 8,
                'high_risk_percentage': 10.0
            },
            {
                'ip_address': '172.16.0.1',
                'country': 'Russia',
                'city': 'Moscow',
                'total_transactions': 50,
                'avg_risk_score': 75.8,
                'high_risk_transactions': 35,
                'high_risk_percentage': 70.0
            }
        ]
    }
    
    return JsonResponse(data)


@login_required
def transaction_report(request):
    """
    View for transaction reports.
    """
    form = ReportFilterForm(request.GET)
    
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Get transactions
    transactions = Transaction.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Apply additional filters
    if form.is_valid():
        data = form.cleaned_data
        
        if data.get('transaction_type'):
            transactions = transactions.filter(transaction_type=data['transaction_type'])
        
        if data.get('channel'):
            transactions = transactions.filter(channel=data['channel'])
        
        if data.get('status'):
            transactions = transactions.filter(status=data['status'])
        
        if data.get('is_flagged') is not None:
            transactions = transactions.filter(is_flagged=data['is_flagged'])
    
    # Get transaction counts by status
    transaction_status_counts = transactions.values('status').annotate(count=Count('id'))
    
    # Get transaction counts by channel
    transaction_channel_counts = transactions.values('channel').annotate(count=Count('id'))
    
    # Get transaction counts by type
    transaction_type_counts = transactions.values('transaction_type').annotate(count=Count('id'))
    
    # Get transaction volume by day
    from django.db.models.functions import TruncDay
    
    daily_volume = transactions.annotate(
        day=TruncDay('timestamp')
    ).values('day').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('day')
    
    context = {
        'form': form,
        'transaction_count': transactions.count(),
        'transaction_volume': transactions.aggregate(total=Sum('amount'))['total'] or 0,
        'transaction_status_counts': transaction_status_counts,
        'transaction_channel_counts': transaction_channel_counts,
        'transaction_type_counts': transaction_type_counts,
        'daily_volume': daily_volume,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'reports/transaction.html', context)


@login_required
def fraud_report(request):
    """
    View for fraud reports.
    """
    form = ReportFilterForm(request.GET)
    
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Get fraud detection results
    fraud_results = FraudDetectionResult.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Get fraud cases
    fraud_cases = FraudCase.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Get decision counts
    decision_counts = fraud_results.values('decision').annotate(count=Count('id'))
    
    # Get case status counts
    case_status_counts = fraud_cases.values('status').annotate(count=Count('id'))
    
    # Get case priority counts
    case_priority_counts = fraud_cases.values('priority').annotate(count=Count('id'))
    
    # Get fraud rate by day
    from django.db.models.functions import TruncDay
    
    daily_fraud_rate = fraud_results.annotate(
        day=TruncDay('created_at')
    ).values('day').annotate(
        total=Count('id'),
        fraudulent=Count('id', filter=Q(is_fraudulent=True))
    ).order_by('day')
    
    # Calculate fraud rate
    for day in daily_fraud_rate:
        day['rate'] = (day['fraudulent'] / day['total'] * 100) if day['total'] > 0 else 0
    
    # Detect unusual patterns or spikes in decline rates
    decline_alerts = []
    
    # Get daily decline rates for the past 7 days
    daily_decline_rates = []
    for i in range(7):
        day_start = end_date - timedelta(days=i+1)
        day_end = end_date - timedelta(days=i)
        
        day_transactions = Transaction.objects.filter(created_at__range=(day_start, day_end))
        day_total = day_transactions.count()
        day_declined = day_transactions.filter(status='rejected').count()
        
        if day_total > 0:
            decline_rate = (day_declined / day_total) * 100
            daily_decline_rates.append({
                'date': day_start,
                'rate': decline_rate,
                'total': day_total,
                'declined': day_declined
            })
    
    # Check for unusual spikes in decline rates
    if len(daily_decline_rates) >= 2:
        # Calculate average and standard deviation of decline rates
        rates = [day['rate'] for day in daily_decline_rates]
        avg_rate = sum(rates) / len(rates)
        std_dev = (sum((rate - avg_rate) ** 2 for rate in rates) / len(rates)) ** 0.5
        
        # Check the most recent day for unusual spike (more than 2 standard deviations)
        if daily_decline_rates and std_dev > 0:
            latest_rate = daily_decline_rates[0]['rate']
            if latest_rate > avg_rate + (2 * std_dev):
                decline_alerts.append({
                    'message': f"Unusual spike in decline rate detected: {latest_rate:.1f}% (average: {avg_rate:.1f}%)",
                    'date': daily_decline_rates[0]['date'],
                    'severity': 'high'
                })
            elif latest_rate > avg_rate + std_dev:
                decline_alerts.append({
                    'message': f"Elevated decline rate detected: {latest_rate:.1f}% (average: {avg_rate:.1f}%)",
                    'date': daily_decline_rates[0]['date'],
                    'severity': 'medium'
                })
    
    # Check for high decline rates by country
    country_decline_rates = []
    countries = Transaction.objects.filter(created_at__range=(start_date, end_date)).values_list('country_code', flat=True).distinct()
    
    for country in countries:
        if not country:  # Skip empty country values
            continue
            
        country_transactions = Transaction.objects.filter(created_at__range=(start_date, end_date), country_code=country)
        country_total = country_transactions.count()
        country_declined = country_transactions.filter(status='rejected').count()
        
        if country_total >= 10:  # Only consider countries with at least 10 transactions
            decline_rate = (country_declined / country_total) * 100
            country_decline_rates.append({
                'country': country,
                'rate': decline_rate,
                'total': country_total,
                'declined': country_declined
            })
    
    # Sort by decline rate (highest first) and get top 3
    country_decline_rates.sort(key=lambda x: x['rate'], reverse=True)
    high_decline_countries = country_decline_rates[:3]
    
    # Add alerts for countries with high decline rates (over 30%)
    for country in high_decline_countries:
        if country['rate'] > 30:
            decline_alerts.append({
                'message': f"High decline rate for country {country['country']}: {country['rate']:.1f}%",
                'country': country['country'],
                'severity': 'high' if country['rate'] > 50 else 'medium'
            })
    
    context = {
        'form': form,
        'fraud_result_count': fraud_results.count(),
        'fraud_count': fraud_results.filter(is_fraudulent=True).count(),
        'case_count': fraud_cases.count(),
        'avg_risk_score': fraud_results.aggregate(avg_score=Avg('risk_score'))['avg_score'] or 0,
        'decision_counts': decision_counts,
        'case_status_counts': case_status_counts,
        'case_priority_counts': case_priority_counts,
        'daily_fraud_rate': daily_fraud_rate,
        'start_date': start_date,
        'end_date': end_date,
        'decline_alerts': decline_alerts,
        'high_decline_countries': high_decline_countries
    }
    
    return render(request, 'reports/fraud.html', context)


@login_required
def aml_report(request):
    """
    View for AML reports.
    """
    form = ReportFilterForm(request.GET)
    
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Get AML alerts
    aml_alerts = AMLAlert.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Get alert counts by status
    alert_status_counts = aml_alerts.values('status').annotate(count=Count('id'))
    
    # Get alert counts by type
    alert_type_counts = aml_alerts.values('alert_type').annotate(count=Count('id'))
    
    # Get alert counts by day
    from django.db.models.functions import TruncDay
    
    daily_alert_counts = aml_alerts.annotate(
        day=TruncDay('created_at')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    context = {
        'form': form,
        'alert_count': aml_alerts.count(),
        'open_alert_count': aml_alerts.filter(status='open').count(),
        'alert_status_counts': alert_status_counts,
        'alert_type_counts': alert_type_counts,
        'daily_alert_counts': daily_alert_counts,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'reports/aml.html', context)


@login_required
def performance_report(request):
    """
    View for system performance reports.
    """
    form = ReportFilterForm(request.GET)
    
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Get fraud detection results
    fraud_results = FraudDetectionResult.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Get average processing time
    avg_processing_time = fraud_results.aggregate(avg_time=Avg('processing_time'))['avg_time'] or 0
    
    # Get processing time by day
    from django.db.models.functions import TruncDay
    
    daily_processing_time = fraud_results.annotate(
        day=TruncDay('created_at')
    ).values('day').annotate(
        avg_time=Avg('processing_time')
    ).order_by('day')
    
    context = {
        'form': form,
        'result_count': fraud_results.count(),
        'avg_processing_time': avg_processing_time,
        'daily_processing_time': daily_processing_time,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'reports/performance.html', context)


@login_required
def custom_report(request):
    """
    View for creating and viewing custom reports.
    """
    if request.method == 'POST':
        form = CustomReportForm(request.POST)
        if form.is_valid():
            # Create a new custom report
            report = CustomReport(
                name=form.cleaned_data['name'],
                report_type=form.cleaned_data['report_type'],
                description=form.cleaned_data['description'],
                output_format=form.cleaned_data['output_format'],
                created_by=request.user.username,
                parameters={
                    'start_date': form.cleaned_data['start_date'].isoformat(),
                    'end_date': form.cleaned_data['end_date'].isoformat(),
                    'metrics': form.cleaned_data['metrics'],
                    'dimensions': form.cleaned_data['dimensions'],
                }
            )
            report.save()
            
            messages.success(request, f'Custom report "{report.name}" created successfully.')
            
            # If output format is web, redirect to the appropriate report view
            if form.cleaned_data['output_format'] == 'web':
                return redirect(f"reporting:{form.cleaned_data['report_type']}")
            else:
                # For other formats, export the report
                return redirect('reporting:export', report_type=form.cleaned_data['report_type'])
    else:
        form = CustomReportForm()
    
    # Get saved custom reports
    custom_reports = CustomReport.objects.all().order_by('-created_at')
    
    context = {
        'form': form,
        'custom_reports': custom_reports,
    }
    
    return render(request, 'reports/custom.html', context)


@login_required
def scheduled_reports(request):
    """
    View for listing scheduled reports.
    """
    scheduled_reports = ScheduledReport.objects.all().order_by('-created_at')
    
    context = {
        'scheduled_reports': scheduled_reports,
    }
    
    return render(request, 'reports/scheduled_list.html', context)


@login_required
def create_scheduled_report(request):
    """
    View for creating a scheduled report.
    """
    if request.method == 'POST':
        form = ScheduledReportForm(request.POST)
        if form.is_valid():
            # Calculate next run time
            next_run = calculate_next_run(
                form.cleaned_data['frequency'],
                form.cleaned_data['time']
            )
            
            # Create a new scheduled report
            report = ScheduledReport(
                name=form.cleaned_data['name'],
                report_type=form.cleaned_data['report_type'],
                frequency=form.cleaned_data['frequency'],
                time=form.cleaned_data['time'],
                recipients=form.cleaned_data['recipients'],
                format=form.cleaned_data['format'],
                active=form.cleaned_data['active'],
                next_run=next_run,
                created_by=request.user.username,
                parameters={}
            )
            report.save()
            
            messages.success(request, f'Scheduled report "{report.name}" created successfully.')
            return redirect('reporting:scheduled')
    else:
        form = ScheduledReportForm()
    
    context = {
        'form': form,
        'action': 'Create',
    }
    
    return render(request, 'reports/scheduled_form.html', context)


@login_required
def edit_scheduled_report(request, report_id):
    """
    View for editing a scheduled report.
    """
    report = get_object_or_404(ScheduledReport, id=report_id)
    
    if request.method == 'POST':
        form = ScheduledReportForm(request.POST)
        if form.is_valid():
            # Calculate next run time
            next_run = calculate_next_run(
                form.cleaned_data['frequency'],
                form.cleaned_data['time']
            )
            
            # Update the scheduled report
            report.name = form.cleaned_data['name']
            report.report_type = form.cleaned_data['report_type']
            report.frequency = form.cleaned_data['frequency']
            report.time = form.cleaned_data['time']
            report.recipients = form.cleaned_data['recipients']
            report.format = form.cleaned_data['format']
            report.active = form.cleaned_data['active']
            report.next_run = next_run
            report.save()
            
            messages.success(request, f'Scheduled report "{report.name}" updated successfully.')
            return redirect('reporting:scheduled')
    else:
        form = ScheduledReportForm(initial={
            'name': report.name,
            'report_type': report.report_type,
            'frequency': report.frequency,
            'time': report.time,
            'recipients': report.recipients,
            'format': report.format,
            'active': report.active,
        })
    
    context = {
        'form': form,
        'report': report,
        'action': 'Edit',
    }
    
    return render(request, 'reports/scheduled_form.html', context)


@login_required
def delete_scheduled_report(request, report_id):
    """
    View for deleting a scheduled report.
    """
    report = get_object_or_404(ScheduledReport, id=report_id)
    
    if request.method == 'POST':
        report_name = report.name
        report.delete()
        messages.success(request, f'Scheduled report "{report_name}" deleted successfully.')
        return redirect('reporting:scheduled')
    
    context = {
        'report': report,
    }
    
    return render(request, 'reports/scheduled_confirm_delete.html', context)


def calculate_next_run(frequency, time):
    """
    Calculate the next run time based on frequency and time.
    """
    now = timezone.now()
    today = now.date()
    run_time = datetime.combine(today, time)
    run_time = timezone.make_aware(run_time)
    
    if run_time <= now:
        # If the time has already passed today, start from tomorrow
        if frequency == 'daily':
            run_time += timedelta(days=1)
        elif frequency == 'weekly':
            run_time += timedelta(days=7)
        elif frequency == 'monthly':
            # Add a month (approximately)
            if run_time.month == 12:
                run_time = run_time.replace(year=run_time.year + 1, month=1)
            else:
                run_time = run_time.replace(month=run_time.month + 1)
        elif frequency == 'quarterly':
            # Add three months (approximately)
            if run_time.month > 9:
                run_time = run_time.replace(year=run_time.year + 1, month=(run_time.month + 3) % 12)
            else:
                run_time = run_time.replace(month=run_time.month + 3)
    
    return run_time


@login_required
def decline_rates_report(request):
    """
    View for decline rates report.
    """
    form = ReportFilterForm(request.GET)
    
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Get transactions
    transactions = Transaction.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Apply additional filters
    if form.is_valid():
        data = form.cleaned_data
        
        if data.get('transaction_type'):
            transactions = transactions.filter(transaction_type=data['transaction_type'])
        
        if data.get('channel'):
            transactions = transactions.filter(channel=data['channel'])
        
        if data.get('country_code'):
            transactions = transactions.filter(country_code=data['country_code'])
    
    # Calculate decline rates by day
    daily_decline_rates = transactions.annotate(
        day=TruncDay('timestamp')
    ).values('day').annotate(
        total=Count('id'),
        declined=Count('id', filter=Q(status='rejected')),
        decline_rate=ExpressionWrapper(
            100.0 * Cast(Count('id', filter=Q(status='rejected')), FloatField()) / Cast(Count('id'), FloatField()),
            output_field=FloatField()
        )
    ).order_by('day')
    
    # Calculate decline rates by channel
    channel_decline_rates = transactions.values('channel').annotate(
        total=Count('id'),
        declined=Count('id', filter=Q(status='rejected')),
        decline_rate=ExpressionWrapper(
            100.0 * Cast(Count('id', filter=Q(status='rejected')), FloatField()) / Cast(Count('id'), FloatField()),
            output_field=FloatField()
        )
    ).order_by('-decline_rate')
    
    # Calculate decline rates by country
    country_decline_rates = transactions.values('country_code').annotate(
        total=Count('id'),
        declined=Count('id', filter=Q(status='rejected')),
        decline_rate=ExpressionWrapper(
            100.0 * Cast(Count('id', filter=Q(status='rejected')), FloatField()) / Cast(Count('id'), FloatField()),
            output_field=FloatField()
        )
    ).order_by('-decline_rate')[:10]  # Top 10 countries by decline rate
    
    # Calculate decline rates by hour of day
    hourly_decline_rates = transactions.annotate(
        hour=ExtractHour('timestamp')
    ).values('hour').annotate(
        total=Count('id'),
        declined=Count('id', filter=Q(status='rejected')),
        decline_rate=ExpressionWrapper(
            100.0 * Cast(Count('id', filter=Q(status='rejected')), FloatField()) / Cast(Count('id'), FloatField()),
            output_field=FloatField()
        )
    ).order_by('hour')
    
    # Calculate overall decline rate
    total_transactions = transactions.count()
    declined_transactions = transactions.filter(status='rejected').count()
    overall_decline_rate = (declined_transactions / total_transactions * 100) if total_transactions > 0 else 0
    
    # Calculate decline rate by reason
    decline_reasons = transactions.filter(status='rejected').values('flag_reason').annotate(
        count=Count('id'),
        percentage=ExpressionWrapper(
            100.0 * Cast(Count('id'), FloatField()) / Cast(declined_transactions, FloatField()),
            output_field=FloatField()
        )
    ).order_by('-count')
    
    # Detect anomalies in daily decline rates
    anomalies = []
    alerts = []
    if len(daily_decline_rates) > 5:
        rates = [day['decline_rate'] for day in daily_decline_rates if day['decline_rate'] is not None]
        if rates:
            mean_rate = np.mean(rates)
            std_rate = np.std(rates)
            threshold = 2.0  # Number of standard deviations for anomaly
            
            # Check for recent spikes in decline rates
            # Convert to list first to support negative indexing
            daily_rates_list = list(daily_decline_rates)
            recent_rates = [day['decline_rate'] for day in daily_rates_list[-3:] if day['decline_rate'] is not None]
            if recent_rates and len(recent_rates) >= 2:
                recent_mean = np.mean(recent_rates)
                if recent_mean > (mean_rate * 1.25):  # 25% higher than overall mean
                    alerts.append({
                        'title': 'Recent Spike in Decline Rates',
                        'message': f'Recent decline rates ({recent_mean:.1f}%) are significantly higher than the average ({mean_rate:.1f}%)',
                        'level': 'danger'
                    })
            
            # Check for unusual patterns in specific channels
            if channel_decline_rates:
                avg_channel_rate = np.mean([c['decline_rate'] for c in channel_decline_rates if c['decline_rate'] is not None])
                for channel in channel_decline_rates:
                    if channel['decline_rate'] is not None and channel['decline_rate'] > (avg_channel_rate * 1.5):
                        alerts.append({
                            'title': f'High Decline Rate in {channel["channel"]} Channel',
                            'message': f'The {channel["channel"]} channel has an unusually high decline rate of {channel["decline_rate"]:.1f}%',
                            'level': 'warning'
                        })
            
            # Check for unusual patterns in specific countries
            if country_decline_rates:
                avg_country_rate = np.mean([c['decline_rate'] for c in country_decline_rates if c['decline_rate'] is not None])
                for country in country_decline_rates:
                    if country['decline_rate'] is not None and country['decline_rate'] > (avg_country_rate * 1.75):
                        alerts.append({
                            'title': f'High Decline Rate in {country["country"]}',
                            'message': f'{country["country"]} has an unusually high decline rate of {country["decline_rate"]:.1f}%',
                            'level': 'warning'
                        })
            
            for day in daily_decline_rates:
                if day['decline_rate'] is not None:
                    z_score = abs(day['decline_rate'] - mean_rate) / std_rate if std_rate > 0 else 0
                    if z_score > threshold:
                        anomalies.append({
                            'date': day['day'],
                            'decline_rate': day['decline_rate'],
                            'z_score': z_score,
                            'mean_rate': mean_rate,
                            'std_rate': std_rate
                        })
    
    context = {
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
        'total_transactions': total_transactions,
        'declined_transactions': declined_transactions,
        'overall_decline_rate': overall_decline_rate,
        'daily_decline_rates': daily_decline_rates,
        'channel_decline_rates': channel_decline_rates,
        'country_decline_rates': country_decline_rates,
        'hourly_decline_rates': hourly_decline_rates,
        'decline_reasons': decline_reasons,
        'anomalies': anomalies,
        'alerts': alerts
    }
    
    return render(request, 'reports/decline_rates.html', context)


@login_required
def decline_rates_api(request):
    """
    API endpoint for decline rates data.
    """
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Get date range from request
    if request.GET.get('start_date'):
        start_date = datetime.fromisoformat(request.GET.get('start_date'))
    
    if request.GET.get('end_date'):
        end_date = datetime.fromisoformat(request.GET.get('end_date'))
    
    # Get transactions
    transactions = Transaction.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Apply additional filters
    if request.GET.get('transaction_type'):
        transactions = transactions.filter(transaction_type=request.GET.get('transaction_type'))
    
    if request.GET.get('channel'):
        transactions = transactions.filter(channel=request.GET.get('channel'))
    
    if request.GET.get('country_code'):
        transactions = transactions.filter(country_code=request.GET.get('country_code'))
    
    # Calculate decline rates by day
    daily_decline_rates = transactions.annotate(
        day=TruncDay('timestamp')
    ).values('day').annotate(
        total=Count('id'),
        declined=Count('id', filter=Q(status='rejected')),
        decline_rate=ExpressionWrapper(
            100.0 * Cast(Count('id', filter=Q(status='rejected')), FloatField()) / Cast(Count('id'), FloatField()),
            output_field=FloatField()
        )
    ).order_by('day')
    
    # Format data for API response
    data = {
        'labels': [day['day'].strftime('%Y-%m-%d') for day in daily_decline_rates],
        'total': [day['total'] for day in daily_decline_rates],
        'declined': [day['declined'] for day in daily_decline_rates],
        'decline_rate': [float(day['decline_rate']) if day['decline_rate'] is not None else 0 for day in daily_decline_rates]
    }
    
    return JsonResponse(data)


@login_required
def alerts_api(request):
    """
    API endpoint for alerts data.
    """
    # Get date range from request
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get transactions
    transactions = Transaction.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    # Calculate daily transaction counts and decline rates
    daily_data = transactions.annotate(
        day=TruncDay('timestamp')
    ).values('day').annotate(
        total=Count('id'),
        declined=Count('id', filter=Q(status='rejected')),
        decline_rate=ExpressionWrapper(
            100.0 * Cast(Count('id', filter=Q(status='rejected')), FloatField()) / Cast(Count('id'), FloatField()),
            output_field=FloatField()
        )
    ).order_by('day')
    
    # Detect anomalies
    anomalies = []
    if len(daily_data) > 5:
        # Analyze decline rates
        rates = [day['decline_rate'] for day in daily_data if day['decline_rate'] is not None]
        if rates:
            mean_rate = np.mean(rates)
            std_rate = np.std(rates)
            threshold = 2.0  # Number of standard deviations for anomaly
            
            for day in daily_data:
                if day['decline_rate'] is not None:
                    z_score = abs(day['decline_rate'] - mean_rate) / std_rate if std_rate > 0 else 0
                    if z_score > threshold:
                        anomalies.append({
                            'date': day['day'].strftime('%Y-%m-%d'),
                            'type': 'decline_rate',
                            'value': float(day['decline_rate']),
                            'expected': float(mean_rate),
                            'z_score': float(z_score),
                            'message': f"Unusual decline rate of {day['decline_rate']:.2f}% on {day['day'].strftime('%Y-%m-%d')} (expected around {mean_rate:.2f}%)"
                        })
        
        # Analyze transaction volume
        volumes = [day['total'] for day in daily_data]
        if volumes:
            mean_volume = np.mean(volumes)
            std_volume = np.std(volumes)
            threshold = 2.5  # Higher threshold for volume anomalies
            
            for day in daily_data:
                z_score = abs(day['total'] - mean_volume) / std_volume if std_volume > 0 else 0
                if z_score > threshold:
                    anomalies.append({
                        'date': day['day'].strftime('%Y-%m-%d'),
                        'type': 'volume',
                        'value': day['total'],
                        'expected': float(mean_volume),
                        'z_score': float(z_score),
                        'message': f"Unusual transaction volume of {day['total']} on {day['day'].strftime('%Y-%m-%d')} (expected around {mean_volume:.0f})"
                    })
    
    # Sort anomalies by date
    anomalies.sort(key=lambda x: x['date'], reverse=True)
    
    return JsonResponse({'alerts': anomalies})


@login_required
def export_report(request, report_type):
    """
    View for exporting reports as CSV.
    """
    # Default date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    form = ReportFilterForm(request.GET)
    if form.is_valid():
        # Apply filters from the form
        data = form.cleaned_data
        
        if data.get('start_date'):
            start_date = data['start_date']
        
        if data.get('end_date'):
            end_date = data['end_date']
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
    
    # Create CSV writer
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    
    if report_type == 'transaction':
        # Get transactions
        transactions = Transaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        # Apply additional filters
        if form.is_valid():
            data = form.cleaned_data
            
            if data.get('transaction_type'):
                transactions = transactions.filter(transaction_type=data['transaction_type'])
            
            if data.get('channel'):
                transactions = transactions.filter(channel=data['channel'])
            
            if data.get('status'):
                transactions = transactions.filter(status=data['status'])
            
            if data.get('is_flagged') is not None:
                transactions = transactions.filter(is_flagged=data['is_flagged'])
            
            if data.get('country_code'):
                transactions = transactions.filter(country_code=data['country_code'])
        
        # Write header
        writer.writerow([
            'Transaction ID',
            'Type',
            'Channel',
            'Amount',
            'Currency',
            'User ID',
            'Timestamp',
            'Status',
            'Is Flagged',
            'Risk Score',
            'Country Code',
            'Is High Risk Country',
            'Is High Risk Merchant',
        ])
        
        # Write data
        for tx in transactions:
            writer.writerow([
                tx.transaction_id,
                tx.transaction_type,
                tx.channel,
                tx.amount,
                tx.currency,
                tx.user_id,
                tx.timestamp,
                tx.status,
                tx.is_flagged,
                tx.risk_score,
                tx.country_code,
                tx.is_high_risk_country,
                tx.is_high_risk_merchant,
            ])
    
    elif report_type == 'fraud':
        # Get fraud detection results
        fraud_results = FraudDetectionResult.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Write header
        writer.writerow([
            'Transaction ID',
            'User ID',
            'Risk Score',
            'Is Fraudulent',
            'Decision',
            'Detection Type',
            'Risk Level',
            'Processing Time',
            'Created At',
        ])
        
        # Write data
        for result in fraud_results:
            writer.writerow([
                result.transaction_id,
                result.user_id,
                result.risk_score,
                result.is_fraudulent,
                result.decision,
                result.detection_type,
                result.risk_level,
                result.processing_time,
                result.created_at,
            ])
    
    elif report_type == 'aml':
        # Get AML alerts
        aml_alerts = AMLAlert.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Write header
        writer.writerow([
            'Alert ID',
            'User ID',
            'Alert Type',
            'Status',
            'Risk Score',
            'Created At',
        ])
        
        # Write data
        for alert in aml_alerts:
            writer.writerow([
                alert.alert_id,
                alert.user_id,
                alert.alert_type,
                alert.status,
                alert.risk_score,
                alert.created_at,
            ])
    
    elif report_type == 'performance':
        # Get fraud detection results for performance metrics
        fraud_results = FraudDetectionResult.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Write header
        writer.writerow([
            'Date',
            'Total Results',
            'Average Processing Time (ms)',
            'Min Processing Time (ms)',
            'Max Processing Time (ms)',
        ])
        
        # Group by day
        from django.db.models.functions import TruncDay
        
        daily_performance = fraud_results.annotate(
            day=TruncDay('created_at')
        ).values('day').annotate(
            total=Count('id'),
            avg_time=Avg('processing_time'),
            min_time=Min('processing_time'),
            max_time=Max('processing_time')
        ).order_by('day')
        
        # Write data
        for day in daily_performance:
            writer.writerow([
                day['day'].strftime('%Y-%m-%d'),
                day['total'],
                day['avg_time'],
                day['min_time'],
                day['max_time'],
            ])
    
    elif report_type == 'decline_rates':
        # Get transactions
        transactions = Transaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        # Apply additional filters
        if form.is_valid():
            data = form.cleaned_data
            
            if data.get('transaction_type'):
                transactions = transactions.filter(transaction_type=data['transaction_type'])
            
            if data.get('channel'):
                transactions = transactions.filter(channel=data['channel'])
            
            if data.get('country_code'):
                transactions = transactions.filter(country_code=data['country_code'])
        
        # Write header
        writer.writerow([
            'Date',
            'Total Transactions',
            'Declined Transactions',
            'Decline Rate (%)',
            'Decline Reason',
        ])
        
        # Calculate decline rates by day
        daily_decline_rates = transactions.annotate(
            day=TruncDay('timestamp')
        ).values('day').annotate(
            total=Count('id'),
            declined=Count('id', filter=Q(status='rejected')),
            decline_rate=ExpressionWrapper(
                100.0 * Cast(Count('id', filter=Q(status='rejected')), FloatField()) / Cast(Count('id'), FloatField()),
                output_field=FloatField()
            )
        ).order_by('day')
        
        # Get decline reasons
        decline_reasons = transactions.filter(status='rejected').values('flag_reason').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Create a mapping of days to reasons
        day_reasons = {}
        for reason in decline_reasons:
            reason_transactions = transactions.filter(
                status='rejected',
                flag_reason=reason['flag_reason']
            ).annotate(
                day=TruncDay('timestamp')
            ).values('day').annotate(
                count=Count('id')
            )
            
            for day_data in reason_transactions:
                day_key = day_data['day'].strftime('%Y-%m-%d')
                if day_key not in day_reasons:
                    day_reasons[day_key] = []
                
                day_reasons[day_key].append({
                    'reason': reason['flag_reason'] or 'Unknown',
                    'count': day_data['count']
                })
        
        # Write data
        for day in daily_decline_rates:
            day_key = day['day'].strftime('%Y-%m-%d')
            reasons = day_reasons.get(day_key, [])
            
            if reasons:
                # Write a row for each reason
                for reason_data in reasons:
                    writer.writerow([
                        day_key,
                        day['total'],
                        day['declined'],
                        day['decline_rate'] if day['decline_rate'] is not None else 0,
                        f"{reason_data['reason']} ({reason_data['count']})"
                    ])
            else:
                # Write a row with no specific reason
                writer.writerow([
                    day_key,
                    day['total'],
                    day['declined'],
                    day['decline_rate'] if day['decline_rate'] is not None else 0,
                    'N/A'
                ])
    
    # Write CSV to response
    response.write(csv_buffer.getvalue())
    
    return response