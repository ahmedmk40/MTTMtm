"""
Tests for the permissions module.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.test import Client
from apps.accounts.permissions import setup_role_permissions
from apps.transactions.models import Transaction

User = get_user_model()


class PermissionsSetupTests(TestCase):
    """Tests for the permissions setup function."""
    
    def test_setup_role_permissions(self):
        """Test that setup_role_permissions creates the expected groups and permissions."""
        # Run the setup function
        groups = setup_role_permissions()
        
        # Check that all expected groups were created
        self.assertIn('compliance_officer', groups)
        self.assertIn('fraud_analyst', groups)
        self.assertIn('risk_manager', groups)
        self.assertIn('data_analyst', groups)
        self.assertIn('executive', groups)
        
        # Check that each group has the expected permissions
        compliance_officer_group = groups['compliance_officer']
        self.assertTrue(compliance_officer_group.permissions.filter(codename='view_transaction').exists())
        self.assertTrue(compliance_officer_group.permissions.filter(codename='view_amlalert').exists())
        
        fraud_analyst_group = groups['fraud_analyst']
        self.assertTrue(fraud_analyst_group.permissions.filter(codename='view_transaction').exists())
        self.assertTrue(fraud_analyst_group.permissions.filter(codename='view_fraudcase').exists())
        
        risk_manager_group = groups['risk_manager']
        self.assertTrue(risk_manager_group.permissions.filter(codename='view_transaction').exists())
        self.assertTrue(risk_manager_group.permissions.filter(codename='view_fraudcase').exists())
        self.assertTrue(risk_manager_group.permissions.filter(codename='view_amlalert').exists())


class UserRoleTests(TestCase):
    """Tests for user roles and permissions."""
    
    def setUp(self):
        """Set up test data."""
        # Run the permissions setup
        self.groups = setup_role_permissions()
        
        # Create test users
        self.compliance_officer = User.objects.create_user(
            username='compliance_officer',
            email='compliance@example.com',
            password='password123',
            role='compliance_officer'
        )
        
        self.fraud_analyst = User.objects.create_user(
            username='fraud_analyst',
            email='fraud@example.com',
            password='password123',
            role='fraud_analyst'
        )
        
        self.risk_manager = User.objects.create_user(
            username='risk_manager',
            email='risk@example.com',
            password='password123',
            role='risk_manager'
        )
        
        # Add users to groups
        self.compliance_officer.groups.add(self.groups['compliance_officer'])
        self.fraud_analyst.groups.add(self.groups['fraud_analyst'])
        self.risk_manager.groups.add(self.groups['risk_manager'])
    
    def test_user_role_methods(self):
        """Test the user role methods."""
        self.assertTrue(self.compliance_officer.is_compliance_officer())
        self.assertFalse(self.compliance_officer.is_fraud_analyst())
        
        self.assertTrue(self.fraud_analyst.is_fraud_analyst())
        self.assertFalse(self.fraud_analyst.is_compliance_officer())
        
        self.assertTrue(self.risk_manager.is_risk_manager())
        self.assertFalse(self.risk_manager.is_fraud_analyst())
    
    def test_user_permissions(self):
        """Test that users have the expected permissions."""
        # Compliance officer permissions
        self.assertTrue(self.compliance_officer.has_perm('transactions.view_transaction'))
        self.assertTrue(self.compliance_officer.has_perm('aml.view_amlalert'))
        self.assertTrue(self.compliance_officer.has_perm('aml.change_amlalert'))
        self.assertFalse(self.compliance_officer.has_perm('fraud_engine.change_fraudcase'))
        
        # Fraud analyst permissions
        self.assertTrue(self.fraud_analyst.has_perm('transactions.view_transaction'))
        self.assertTrue(self.fraud_analyst.has_perm('fraud_engine.view_fraudcase'))
        self.assertTrue(self.fraud_analyst.has_perm('fraud_engine.change_fraudcase'))
        self.assertFalse(self.fraud_analyst.has_perm('aml.change_amlalert'))
        
        # Risk manager permissions
        self.assertTrue(self.risk_manager.has_perm('transactions.view_transaction'))
        self.assertTrue(self.risk_manager.has_perm('fraud_engine.view_fraudcase'))
        self.assertTrue(self.risk_manager.has_perm('aml.view_amlalert'))
        self.assertFalse(self.risk_manager.has_perm('fraud_engine.change_fraudcase'))
    
    def test_update_role_groups(self):
        """Test that update_role_groups updates the user's group membership."""
        # Change the user's role
        self.compliance_officer.role = 'fraud_analyst'
        self.compliance_officer.save()
        
        # Check that the user is now in the fraud analyst group
        self.assertFalse(self.compliance_officer.groups.filter(name='Compliance Officer').exists())
        self.assertTrue(self.compliance_officer.groups.filter(name='Fraud Analyst').exists())
        
        # Check that the user now has fraud analyst permissions
        self.assertTrue(self.compliance_officer.has_perm('fraud_engine.change_fraudcase'))
        self.assertFalse(self.compliance_officer.has_perm('aml.change_amlalert'))