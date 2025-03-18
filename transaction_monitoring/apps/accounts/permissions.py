"""
Custom permissions for the Transaction Monitoring and Fraud Detection System.
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework import permissions
from apps.transactions.models import Transaction, POSTransaction, EcommerceTransaction, WalletTransaction
from apps.fraud_engine.models import FraudCase
from apps.aml.models import AMLAlert, SuspiciousActivityReport


class IsComplianceOfficer(permissions.BasePermission):
    """
    Permission to check if the user is a compliance officer.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'compliance_officer'


class IsFraudAnalyst(permissions.BasePermission):
    """
    Permission to check if the user is a fraud analyst.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'fraud_analyst'


class IsRiskManager(permissions.BasePermission):
    """
    Permission to check if the user is a risk manager.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'risk_manager'


class IsDataAnalyst(permissions.BasePermission):
    """
    Permission to check if the user is a data analyst.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'data_analyst'


class IsExecutive(permissions.BasePermission):
    """
    Permission to check if the user is an executive.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'executive'


class CanViewTransactions(permissions.BasePermission):
    """
    Permission to check if the user can view transactions.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if the user has the 'view_transaction' permission
        return request.user.has_perm('transactions.view_transaction')


class CanManageFraudCases(permissions.BasePermission):
    """
    Permission to check if the user can manage fraud cases.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if the user has the 'change_fraudcase' permission
        return request.user.has_perm('fraud_engine.change_fraudcase')
    
    def has_object_permission(self, request, view, obj):
        # Allow if the user has global permission
        if request.user.has_perm('fraud_engine.change_fraudcase'):
            return True
        
        # Allow if the user is assigned to the case
        if hasattr(obj, 'assigned_to') and obj.assigned_to == request.user:
            return True
        
        return False


class CanManageAMLAlerts(permissions.BasePermission):
    """
    Permission to check if the user can manage AML alerts.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if the user has the 'change_amlalert' permission
        return request.user.has_perm('aml.change_amlalert')


class CanGenerateReports(permissions.BasePermission):
    """
    Permission to check if the user can generate reports.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if the user has the 'generate_report' permission
        return request.user.has_perm('reporting.generate_report')


class CanManageRules(permissions.BasePermission):
    """
    Permission to check if the user can manage rules.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if the user has the 'change_rule' permission
        return request.user.has_perm('rule_engine.change_rule')


def setup_role_permissions():
    """
    Set up role-based permissions for the system.
    
    This function creates the necessary groups and assigns permissions to them.
    It should be run during system initialization or when updating permissions.
    """
    # Create groups if they don't exist
    compliance_officer_group, _ = Group.objects.get_or_create(name='Compliance Officer')
    fraud_analyst_group, _ = Group.objects.get_or_create(name='Fraud Analyst')
    risk_manager_group, _ = Group.objects.get_or_create(name='Risk Manager')
    data_analyst_group, _ = Group.objects.get_or_create(name='Data Analyst')
    executive_group, _ = Group.objects.get_or_create(name='Executive')
    
    # Get content types for models
    transaction_ct = ContentType.objects.get_for_model(Transaction)
    pos_transaction_ct = ContentType.objects.get_for_model(POSTransaction)
    ecommerce_transaction_ct = ContentType.objects.get_for_model(EcommerceTransaction)
    wallet_transaction_ct = ContentType.objects.get_for_model(WalletTransaction)
    fraud_case_ct = ContentType.objects.get_for_model(FraudCase)
    aml_alert_ct = ContentType.objects.get_for_model(AMLAlert)
    sar_ct = ContentType.objects.get_for_model(SuspiciousActivityReport)
    
    # Clear existing permissions for groups
    compliance_officer_group.permissions.clear()
    fraud_analyst_group.permissions.clear()
    risk_manager_group.permissions.clear()
    data_analyst_group.permissions.clear()
    executive_group.permissions.clear()
    
    # Get permissions
    # Transaction permissions
    view_transaction = Permission.objects.get(content_type=transaction_ct, codename='view_transaction')
    change_transaction = Permission.objects.get(content_type=transaction_ct, codename='change_transaction')
    
    # POS Transaction permissions
    view_pos_transaction = Permission.objects.get(content_type=pos_transaction_ct, codename='view_postransaction')
    
    # E-commerce Transaction permissions
    view_ecommerce_transaction = Permission.objects.get(content_type=ecommerce_transaction_ct, codename='view_ecommercetransaction')
    
    # Wallet Transaction permissions
    view_wallet_transaction = Permission.objects.get(content_type=wallet_transaction_ct, codename='view_wallettransaction')
    
    # Fraud Case permissions
    view_fraud_case = Permission.objects.get(content_type=fraud_case_ct, codename='view_fraudcase')
    add_fraud_case = Permission.objects.get(content_type=fraud_case_ct, codename='add_fraudcase')
    change_fraud_case = Permission.objects.get(content_type=fraud_case_ct, codename='change_fraudcase')
    
    # AML Alert permissions
    view_aml_alert = Permission.objects.get(content_type=aml_alert_ct, codename='view_amlalert')
    add_aml_alert = Permission.objects.get(content_type=aml_alert_ct, codename='add_amlalert')
    change_aml_alert = Permission.objects.get(content_type=aml_alert_ct, codename='change_amlalert')
    
    # SAR permissions
    view_sar = Permission.objects.get(content_type=sar_ct, codename='view_suspiciousactivityreport')
    add_sar = Permission.objects.get(content_type=sar_ct, codename='add_suspiciousactivityreport')
    change_sar = Permission.objects.get(content_type=sar_ct, codename='change_suspiciousactivityreport')
    
    # Assign permissions to Compliance Officer group
    compliance_officer_group.permissions.add(
        view_transaction,
        view_pos_transaction,
        view_ecommerce_transaction,
        view_wallet_transaction,
        view_aml_alert,
        change_aml_alert,
        view_sar,
        add_sar,
        change_sar
    )
    
    # Assign permissions to Fraud Analyst group
    fraud_analyst_group.permissions.add(
        view_transaction,
        view_pos_transaction,
        view_ecommerce_transaction,
        view_wallet_transaction,
        view_fraud_case,
        add_fraud_case,
        change_fraud_case
    )
    
    # Assign permissions to Risk Manager group
    risk_manager_group.permissions.add(
        view_transaction,
        view_pos_transaction,
        view_ecommerce_transaction,
        view_wallet_transaction,
        view_fraud_case,
        view_aml_alert,
        view_sar
    )
    
    # Assign permissions to Data Analyst group
    data_analyst_group.permissions.add(
        view_transaction,
        view_pos_transaction,
        view_ecommerce_transaction,
        view_wallet_transaction
    )
    
    # Assign permissions to Executive group
    executive_group.permissions.add(
        view_transaction,
        view_fraud_case,
        view_aml_alert,
        view_sar
    )
    
    return {
        'compliance_officer': compliance_officer_group,
        'fraud_analyst': fraud_analyst_group,
        'risk_manager': risk_manager_group,
        'data_analyst': data_analyst_group,
        'executive': executive_group
    }