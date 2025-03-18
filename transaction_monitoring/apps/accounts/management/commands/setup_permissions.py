"""
Management command to set up permissions for the Transaction Monitoring and Fraud Detection System.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from apps.accounts.permissions import setup_role_permissions

User = get_user_model()


class Command(BaseCommand):
    """
    Command to set up permissions for the system.
    """
    
    help = 'Set up role-based permissions for the system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-users',
            action='store_true',
            help='Create test users for each role'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Setting up role-based permissions...'))
        
        # Set up role permissions
        groups = setup_role_permissions()
        
        # Print the groups and their permissions
        for role, group in groups.items():
            self.stdout.write(self.style.SUCCESS(f'Role: {role}'))
            self.stdout.write('Permissions:')
            for perm in group.permissions.all():
                self.stdout.write(f'  - {perm.content_type.app_label}.{perm.codename}')
            self.stdout.write('')
        
        # Create test users if requested
        if options['create_test_users']:
            self.create_test_users(groups)
        
        self.stdout.write(self.style.SUCCESS('Successfully set up role-based permissions'))
    
    def create_test_users(self, groups):
        """Create test users for each role."""
        self.stdout.write(self.style.NOTICE('Creating test users...'))
        
        # Define test users
        test_users = [
            {
                'username': 'compliance_officer',
                'email': 'compliance@example.com',
                'password': 'securepassword123',
                'first_name': 'Compliance',
                'last_name': 'Officer',
                'role': 'compliance_officer',
                'group': groups['compliance_officer'],
            },
            {
                'username': 'fraud_analyst',
                'email': 'fraud@example.com',
                'password': 'securepassword123',
                'first_name': 'Fraud',
                'last_name': 'Analyst',
                'role': 'fraud_analyst',
                'group': groups['fraud_analyst'],
            },
            {
                'username': 'risk_manager',
                'email': 'risk@example.com',
                'password': 'securepassword123',
                'first_name': 'Risk',
                'last_name': 'Manager',
                'role': 'risk_manager',
                'group': groups['risk_manager'],
            },
            {
                'username': 'data_analyst',
                'email': 'data@example.com',
                'password': 'securepassword123',
                'first_name': 'Data',
                'last_name': 'Analyst',
                'role': 'data_analyst',
                'group': groups['data_analyst'],
            },
            {
                'username': 'executive',
                'email': 'executive@example.com',
                'password': 'securepassword123',
                'first_name': 'Executive',
                'last_name': 'User',
                'role': 'executive',
                'group': groups['executive'],
            },
        ]
        
        # Create users
        for user_data in test_users:
            group = user_data.pop('group')
            
            # Check if user already exists
            if User.objects.filter(username=user_data['username']).exists():
                user = User.objects.get(username=user_data['username'])
                self.stdout.write(f"User {user_data['username']} already exists, updating...")
            else:
                # Create new user
                user = User.objects.create_user(**user_data)
                self.stdout.write(f"Created user: {user_data['username']}")
            
            # Add user to group
            user.groups.add(group)
            user.save()
            
            self.stdout.write(f"Added {user_data['username']} to group: {group.name}")
        
        self.stdout.write(self.style.SUCCESS('Successfully created test users'))