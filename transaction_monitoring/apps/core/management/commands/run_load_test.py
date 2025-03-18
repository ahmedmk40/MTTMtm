"""
Management command to run load tests on the application.
"""

import time
import random
import statistics
import concurrent.futures
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.test.client import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    """
    Command to run load tests on the application.
    """
    
    help = 'Run load tests on the application'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of concurrent users to simulate'
        )
        parser.add_argument(
            '--requests',
            type=int,
            default=100,
            help='Number of requests per user'
        )
        parser.add_argument(
            '--endpoint',
            type=str,
            default='dashboard:index',
            help='Endpoint to test (URL name)'
        )
        parser.add_argument(
            '--method',
            type=str,
            default='GET',
            choices=['GET', 'POST'],
            help='HTTP method to use'
        )
        parser.add_argument(
            '--data',
            type=str,
            help='JSON data to send with POST requests'
        )
        parser.add_argument(
            '--auth',
            action='store_true',
            help='Authenticate requests'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file for results'
        )
    
    def handle(self, *args, **options):
        num_users = options['users']
        num_requests = options['requests']
        endpoint = options['endpoint']
        method = options['method']
        data = options.get('data')
        auth = options.get('auth')
        output_file = options.get('output')
        
        self.stdout.write(self.style.NOTICE(f"Running load test with {num_users} users, {num_requests} requests per user"))
        self.stdout.write(f"Endpoint: {endpoint}, Method: {method}")
        
        # Create test users if needed
        if auth:
            self.create_test_users(num_users)
        
        # Run the load test
        results = self.run_load_test(num_users, num_requests, endpoint, method, data, auth)
        
        # Print results
        self.print_results(results)
        
        # Save results to file if specified
        if output_file:
            self.save_results(results, output_file)
    
    def create_test_users(self, num_users):
        """Create test users for load testing."""
        self.stdout.write("Creating test users...")
        
        existing_count = User.objects.filter(username__startswith='loadtest_').count()
        
        if existing_count >= num_users:
            self.stdout.write(f"Using {num_users} existing test users")
            return
        
        # Create additional users if needed
        for i in range(existing_count, num_users):
            username = f"loadtest_{i}"
            email = f"loadtest_{i}@example.com"
            
            # Check if user already exists
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    email=email,
                    password='testpassword123',
                    first_name=f'Load',
                    last_name=f'Test {i}',
                    role=random.choice(['compliance_officer', 'fraud_analyst', 'risk_manager', 'data_analyst'])
                )
        
        self.stdout.write(self.style.SUCCESS(f"Created test users"))
    
    def run_load_test(self, num_users, num_requests, endpoint, method, data, auth):
        """Run the load test with multiple concurrent users."""
        # Get the URL for the endpoint
        url = reverse(endpoint)
        
        # Get test users if authentication is required
        users = []
        if auth:
            users = list(User.objects.filter(username__startswith='loadtest_')[:num_users])
        
        # Create a list of tasks
        tasks = []
        for i in range(num_users):
            user = users[i] if auth and i < len(users) else None
            tasks.append((i, user, url, num_requests, method, data))
        
        # Run tasks in parallel
        results = []
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(self.simulate_user, *task) for task in tasks]
            
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        
        total_time = time.time() - start_time
        
        # Aggregate results
        all_response_times = []
        status_counts = {}
        errors = []
        
        for result in results:
            all_response_times.extend(result['response_times'])
            
            for status, count in result['status_counts'].items():
                status_counts[status] = status_counts.get(status, 0) + count
            
            errors.extend(result['errors'])
        
        # Calculate statistics
        total_requests = sum(status_counts.values())
        requests_per_second = total_requests / total_time if total_time > 0 else 0
        
        if all_response_times:
            avg_response_time = statistics.mean(all_response_times)
            min_response_time = min(all_response_times)
            max_response_time = max(all_response_times)
            median_response_time = statistics.median(all_response_times)
            p95_response_time = sorted(all_response_times)[int(len(all_response_times) * 0.95)]
        else:
            avg_response_time = min_response_time = max_response_time = median_response_time = p95_response_time = 0
        
        return {
            'total_time': total_time,
            'total_requests': total_requests,
            'requests_per_second': requests_per_second,
            'avg_response_time': avg_response_time,
            'min_response_time': min_response_time,
            'max_response_time': max_response_time,
            'median_response_time': median_response_time,
            'p95_response_time': p95_response_time,
            'status_counts': status_counts,
            'errors': errors,
            'response_times': all_response_times,
        }
    
    def simulate_user(self, user_id, user, url, num_requests, method, data):
        """Simulate a user making requests."""
        client = Client()
        
        # Login if user is provided
        if user:
            client.force_login(user)
        
        response_times = []
        status_counts = {}
        errors = []
        
        for i in range(num_requests):
            try:
                start_time = time.time()
                
                if method == 'GET':
                    response = client.get(url)
                elif method == 'POST':
                    response = client.post(url, data=data or {})
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                response_times.append(response_time)
                status_counts[response.status_code] = status_counts.get(response.status_code, 0) + 1
                
                # Add a small delay to simulate real user behavior
                time.sleep(random.uniform(0.1, 0.5))
            
            except Exception as e:
                errors.append(str(e))
        
        return {
            'user_id': user_id,
            'response_times': response_times,
            'status_counts': status_counts,
            'errors': errors,
        }
    
    def print_results(self, results):
        """Print the load test results."""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("LOAD TEST RESULTS"))
        self.stdout.write("=" * 50)
        
        self.stdout.write(f"\nTotal time: {results['total_time']:.2f} seconds")
        self.stdout.write(f"Total requests: {results['total_requests']}")
        self.stdout.write(f"Requests per second: {results['requests_per_second']:.2f}")
        
        self.stdout.write("\nResponse Time Statistics:")
        self.stdout.write(f"  Average: {results['avg_response_time']:.2f} ms")
        self.stdout.write(f"  Minimum: {results['min_response_time']:.2f} ms")
        self.stdout.write(f"  Maximum: {results['max_response_time']:.2f} ms")
        self.stdout.write(f"  Median: {results['median_response_time']:.2f} ms")
        self.stdout.write(f"  95th Percentile: {results['p95_response_time']:.2f} ms")
        
        self.stdout.write("\nStatus Code Distribution:")
        for status, count in sorted(results['status_counts'].items()):
            percentage = (count / results['total_requests']) * 100
            self.stdout.write(f"  {status}: {count} ({percentage:.2f}%)")
        
        if results['errors']:
            self.stdout.write("\nErrors:")
            for error in results['errors'][:10]:  # Show only first 10 errors
                self.stdout.write(f"  - {error}")
            
            if len(results['errors']) > 10:
                self.stdout.write(f"  ... and {len(results['errors']) - 10} more errors")
        
        self.stdout.write("\n" + "=" * 50)
    
    def save_results(self, results, output_file):
        """Save the load test results to a file."""
        import json
        from django.utils import timezone
        
        # Add timestamp to results
        results['timestamp'] = timezone.now().isoformat()
        
        # Convert response times to list for JSON serialization
        results['response_times'] = list(results['response_times'])
        
        # Convert status counts to strings for JSON serialization
        results['status_counts'] = {str(k): v for k, v in results['status_counts'].items()}
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.stdout.write(self.style.SUCCESS(f"Results saved to {output_file}"))