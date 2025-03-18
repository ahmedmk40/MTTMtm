"""
Management command to test sequential account generation detection.
"""

import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.aml.services.pattern_detection_service import detect_sequential_account_generation

User = get_user_model()


class Command(BaseCommand):
    """
    Command to test sequential account generation detection.
    """
    
    help = 'Test sequential account generation detection'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--pattern',
            type=str,
            choices=['numeric', 'email', 'both'],
            default='both',
            help='Pattern type to test'
        )
        
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of accounts to create'
        )
    
    def handle(self, *args, **options):
        pattern = options['pattern']
        count = options['count']
        
        self.stdout.write(self.style.NOTICE(f'Testing sequential account generation detection with {pattern} pattern...'))
        
        # Generate a unique IP address and device ID for this test
        ip_address = f"192.168.1.{uuid.uuid4().hex[:2]}"
        device_id = f"device_{uuid.uuid4().hex[:8]}"
        
        self.stdout.write(f"Using IP address: {ip_address}")
        self.stdout.write(f"Using device ID: {device_id}")
        
        # Create sequential accounts
        if pattern == 'numeric' or pattern == 'both':
            self.create_numeric_sequence_accounts(count, ip_address, device_id)
        
        if pattern == 'email' or pattern == 'both':
            self.create_email_pattern_accounts(count, ip_address, device_id)
        
        # Test detection
        result = detect_sequential_account_generation(ip_address, device_id)
        
        if result['is_suspicious']:
            self.stdout.write(self.style.SUCCESS(
                f"Sequential account generation detected: {result['account_count']} accounts"
            ))
            
            for pattern in result.get('sequential_patterns', []):
                self.stdout.write(f"  - {pattern['type']}: {pattern['description']}")
        else:
            self.stdout.write(self.style.WARNING("Sequential account generation not detected"))
        
        self.stdout.write(self.style.SUCCESS('Test completed'))
    
    def create_numeric_sequence_accounts(self, count, ip_address, device_id):
        """
        Create accounts with sequential numeric usernames.
        """
        self.stdout.write("Creating accounts with sequential numeric usernames...")
        
        base_name = f"testuser{uuid.uuid4().hex[:4]}"
        
        for i in range(1, count + 1):
            username = f"{base_name}{i}"
            email = f"{username}@example.com"
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password="password123"
            )
            
            # Set last login IP and device ID
            user.last_login_ip = ip_address
            user.last_login_device_id = device_id
            user.save()
            
            self.stdout.write(f"Created user {username} with email {email}")
    
    def create_email_pattern_accounts(self, count, ip_address, device_id):
        """
        Create accounts with patterned email addresses.
        """
        self.stdout.write("Creating accounts with patterned email addresses...")
        
        base_name = f"testmail{uuid.uuid4().hex[:4]}"
        
        for i in range(1, count + 1):
            username = f"user{uuid.uuid4().hex[:6]}"
            email = f"{base_name}{i}@suspicious-domain.com"
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password="password123"
            )
            
            # Set last login IP and device ID
            user.last_login_ip = ip_address
            user.last_login_device_id = device_id
            user.save()
            
            self.stdout.write(f"Created user {username} with email {email}")