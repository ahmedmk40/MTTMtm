"""
Management command to test API performance.
"""

import time
import json
import statistics
import concurrent.futures
from django.core.management.base import BaseCommand
from django.test.client import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    """
    Command to test API performance.
    """
    
    help = 'Test API performance'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--iterations',
            type=int,
            default=10,
            help='Number of iterations to run each test'
        )
        parser.add_argument(
            '--concurrent',
            type=int,
            default=1,
            help='Number of concurrent requests'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file for results'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )
    
    def handle(self, *args, **options):
        iterations = options['iterations']
        concurrent = options['concurrent']
        output_file = options.get('output')
        verbose = options.get('verbose')
        
        self.stdout.write(self.style.NOTICE(f"Testing API performance with {iterations} iterations and {concurrent} concurrent requests"))
        
        # Create a test user if needed
        user = self.get_or_create_test_user()
        
        # Run the API tests
        results = self.run_api_tests(user, iterations, concurrent, verbose)
        
        # Print results
        self.print_results(results)
        
        # Save results to file if specified
        if output_file:
            self.save_results(results, output_file)
    
    def get_or_create_test_user(self):
        """Get or create a test user for API testing."""
        username = 'api_test_user'
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email='api_test@example.com',
                password='testpassword123',
                first_name='API',
                last_name='Test',
                role='compliance_officer'
            )
        
        return user
    
    def run_api_tests(self, user, iterations, concurrent, verbose):
        """Run performance tests on various API endpoints."""
        # Define test cases
        test_cases = [
            {
                'name': 'API Health Check',
                'url': reverse('api:health_check'),
                'method': 'GET',
                'data': None,
                'auth': False,
            },
            {
                'name': 'Transaction List API',
                'url': reverse('api:transaction-list'),
                'method': 'GET',
                'data': None,
                'auth': True,
            },
            {
                'name': 'POS Transaction List API',
                'url': reverse('api:postransaction-list'),
                'method': 'GET',
                'data': None,
                'auth': True,
            },
            {
                'name': 'E-commerce Transaction List API',
                'url': reverse('api:ecommercetransaction-list'),
                'method': 'GET',
                'data': None,
                'auth': True,
            },
            {
                'name': 'Wallet Transaction List API',
                'url': reverse('api:wallettransaction-list'),
                'method': 'GET',
                'data': None,
                'auth': True,
            },
        ]
        
        results = {}
        
        for test_case in test_cases:
            self.stdout.write(f"Testing {test_case['name']}...")
            
            test_results = self.run_test_case(user, test_case, iterations, concurrent, verbose)
            results[test_case['name']] = test_results
        
        return results
    
    def run_test_case(self, user, test_case, iterations, concurrent, verbose):
        """Run a single test case multiple times and collect metrics."""
        name = test_case['name']
        url = test_case['url']
        method = test_case['method']
        data = test_case['data']
        auth = test_case['auth']
        
        # Create tasks for concurrent execution
        tasks = []
        for i in range(iterations):
            tasks.append((user, url, method, data, auth))
        
        # Run tasks in parallel
        all_response_times = []
        all_status_codes = []
        errors = []
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [executor.submit(self.make_request, *task) for task in tasks]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                
                all_response_times.append(result['response_time'])
                all_status_codes.append(result['status_code'])
                
                if result['error']:
                    errors.append(result['error'])
                
                if verbose:
                    self.stdout.write(f"  Request: {result['response_time']:.2f} ms, status {result['status_code']}")
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        if all_response_times:
            avg_response_time = statistics.mean(all_response_times)
            min_response_time = min(all_response_times)
            max_response_time = max(all_response_times)
            median_response_time = statistics.median(all_response_times)
            p95_response_time = sorted(all_response_times)[int(len(all_response_times) * 0.95)]
        else:
            avg_response_time = min_response_time = max_response_time = median_response_time = p95_response_time = 0
        
        # Count status codes
        status_counts = {}
        for status in all_status_codes:
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_time': total_time,
            'total_requests': len(all_response_times),
            'requests_per_second': len(all_response_times) / total_time if total_time > 0 else 0,
            'response_times': {
                'avg': avg_response_time,
                'min': min_response_time,
                'max': max_response_time,
                'median': median_response_time,
                'p95': p95_response_time,
            },
            'status_counts': status_counts,
            'errors': errors,
        }
    
    def make_request(self, user, url, method, data, auth):
        """Make a single API request and return metrics."""
        client = Client()
        
        # Login if authentication is required
        if auth:
            client.force_login(user)
        
        try:
            start_time = time.time()
            
            if method == 'GET':
                response = client.get(url, HTTP_ACCEPT='application/json')
            elif method == 'POST':
                response = client.post(url, data=data or {}, content_type='application/json', HTTP_ACCEPT='application/json')
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            return {
                'response_time': response_time,
                'status_code': response.status_code,
                'error': None,
            }
        
        except Exception as e:
            return {
                'response_time': 0,
                'status_code': 500,
                'error': str(e),
            }
    
    def print_results(self, results):
        """Print the API test results."""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("API PERFORMANCE TEST RESULTS"))
        self.stdout.write("=" * 50)
        
        for name, result in results.items():
            self.stdout.write(f"\n{name}:")
            
            self.stdout.write(f"  Total time: {result['total_time']:.2f} seconds")
            self.stdout.write(f"  Total requests: {result['total_requests']}")
            self.stdout.write(f"  Requests per second: {result['requests_per_second']:.2f}")
            
            self.stdout.write("  Response Time:")
            self.stdout.write(f"    Average: {result['response_times']['avg']:.2f} ms")
            self.stdout.write(f"    Minimum: {result['response_times']['min']:.2f} ms")
            self.stdout.write(f"    Maximum: {result['response_times']['max']:.2f} ms")
            self.stdout.write(f"    Median: {result['response_times']['median']:.2f} ms")
            self.stdout.write(f"    95th Percentile: {result['response_times']['p95']:.2f} ms")
            
            self.stdout.write("  Status Code Distribution:")
            for status, count in sorted(result['status_counts'].items()):
                percentage = (count / result['total_requests']) * 100
                self.stdout.write(f"    {status}: {count} ({percentage:.2f}%)")
            
            if result['errors']:
                self.stdout.write("  Errors:")
                for error in result['errors'][:5]:  # Show only first 5 errors
                    self.stdout.write(f"    - {error}")
                
                if len(result['errors']) > 5:
                    self.stdout.write(f"    ... and {len(result['errors']) - 5} more errors")
        
        self.stdout.write("\n" + "=" * 50)
    
    def save_results(self, results, output_file):
        """Save the API test results to a file."""
        from django.utils import timezone
        
        # Add timestamp to results
        data = {
            'timestamp': timezone.now().isoformat(),
            'results': results,
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.stdout.write(self.style.SUCCESS(f"Results saved to {output_file}"))