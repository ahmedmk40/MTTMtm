#!/usr/bin/env python
"""
Security assessment script for the Transaction Monitoring and Fraud Detection System.

This script performs various security checks on the codebase, including:
1. Static code analysis using Bandit
2. Dependency vulnerability scanning using Safety
3. Django-specific security checks
4. Custom security checks for sensitive data handling

Usage:
    python scripts/security_assessment.py [--output-file FILENAME]
"""

import os
import sys
import json
import subprocess
import argparse
import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Set up argument parser
parser = argparse.ArgumentParser(description='Run security assessment on the codebase')
parser.add_argument('--output-file', type=str, help='Output file for the security report')
args = parser.parse_args()

# Output file setup
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = args.output_file or f'security_report_{timestamp}.json'
output_path = project_root / 'reports' / output_file

# Create reports directory if it doesn't exist
os.makedirs(project_root / 'reports', exist_ok=True)

# Initialize the report
report = {
    'timestamp': datetime.datetime.now().isoformat(),
    'project': 'Transaction Monitoring and Fraud Detection System',
    'summary': {
        'total_issues': 0,
        'high_severity': 0,
        'medium_severity': 0,
        'low_severity': 0,
    },
    'sections': [],
}


def run_command(command, shell=False):
    """Run a command and return its output."""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return '', str(e), 1


def add_section(title, issues, severity_counts):
    """Add a section to the report."""
    report['sections'].append({
        'title': title,
        'issues': issues,
        'severity_counts': severity_counts,
    })
    
    # Update summary counts
    report['summary']['total_issues'] += sum(severity_counts.values())
    report['summary']['high_severity'] += severity_counts.get('high', 0)
    report['summary']['medium_severity'] += severity_counts.get('medium', 0)
    report['summary']['low_severity'] += severity_counts.get('low', 0)


def run_bandit():
    """Run Bandit static code analysis."""
    print("Running Bandit static code analysis...")
    
    # Run Bandit on the project
    stdout, stderr, returncode = run_command([
        'bandit',
        '-r',
        str(project_root / 'apps'),
        '-f',
        'json',
        '-o',
        str(project_root / 'reports' / 'bandit_report.json'),
    ])
    
    # Parse the results
    try:
        with open(project_root / 'reports' / 'bandit_report.json', 'r') as f:
            bandit_results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        bandit_results = {'results': []}
    
    # Extract issues
    issues = []
    severity_counts = {'high': 0, 'medium': 0, 'low': 0}
    
    for result in bandit_results.get('results', []):
        severity = result.get('issue_severity', 'low').lower()
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        issues.append({
            'file': result.get('filename', ''),
            'line': result.get('line_number', 0),
            'issue': result.get('issue_text', ''),
            'severity': severity,
            'confidence': result.get('issue_confidence', ''),
            'cwe': result.get('cwe', ''),
        })
    
    add_section('Bandit Static Code Analysis', issues, severity_counts)
    
    print(f"Bandit found {len(issues)} issues.")
    return issues


def run_safety():
    """Run Safety dependency vulnerability scanning."""
    print("Running Safety dependency vulnerability scanning...")
    
    # Generate requirements.txt if it doesn't exist
    if not os.path.exists(project_root / 'requirements.txt'):
        stdout, stderr, returncode = run_command([
            'pip',
            'freeze',
        ])
        with open(project_root / 'requirements.txt', 'w') as f:
            f.write(stdout)
    
    # Run Safety
    stdout, stderr, returncode = run_command([
        'safety',
        'check',
        '--file',
        str(project_root / 'requirements.txt'),
        '--output',
        'json',
    ])
    
    # Parse the results
    try:
        safety_results = json.loads(stdout)
    except json.JSONDecodeError:
        safety_results = {'vulnerabilities': []}
    
    # Extract issues
    issues = []
    severity_counts = {'high': 0, 'medium': 0, 'low': 0}
    
    for vuln in safety_results.get('vulnerabilities', []):
        # Map Safety severity to our categories
        severity_mapping = {
            'critical': 'high',
            'high': 'high',
            'medium': 'medium',
            'low': 'low',
        }
        severity = severity_mapping.get(vuln.get('severity', '').lower(), 'low')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        issues.append({
            'package': vuln.get('package_name', ''),
            'installed_version': vuln.get('analyzed_version', ''),
            'vulnerable_version': vuln.get('vulnerable_spec', ''),
            'description': vuln.get('advisory', ''),
            'severity': severity,
            'cve': vuln.get('cve', ''),
        })
    
    add_section('Safety Dependency Vulnerability Scanning', issues, severity_counts)
    
    print(f"Safety found {len(issues)} vulnerabilities.")
    return issues


def run_django_checks():
    """Run Django security checks."""
    print("Running Django security checks...")
    
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    
    try:
        import django
        django.setup()
        
        from django.core.management import call_command
        from io import StringIO
        
        # Capture output from check command
        output = StringIO()
        call_command('check', '--deploy', stdout=output)
        
        # Parse the results
        check_output = output.getvalue()
        
        # Extract issues
        issues = []
        severity_counts = {'high': 0, 'medium': 0, 'low': 0}
        
        for line in check_output.split('\n'):
            if any(warning in line for warning in ['error:', 'warning:']):
                severity = 'high' if 'error:' in line else 'medium'
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                issues.append({
                    'issue': line.strip(),
                    'severity': severity,
                    'type': 'Django Security Check',
                })
        
        add_section('Django Security Checks', issues, severity_counts)
        
        print(f"Django checks found {len(issues)} issues.")
        return issues
    
    except Exception as e:
        print(f"Error running Django checks: {e}")
        return []


def check_sensitive_data_handling():
    """Check for sensitive data handling issues."""
    print("Checking sensitive data handling...")
    
    # Patterns to look for
    sensitive_patterns = [
        ('Hardcoded Secret', r'(password|secret|key|token)\s*=\s*["\'][^"\']+["\']', 'high'),
        ('Potential PII', r'(ssn|social_security|credit_card|passport)', 'high'),
        ('Insecure Hash', r'hashlib\.md5|hashlib\.sha1', 'medium'),
        ('Insecure Cipher', r'Crypto\.Cipher\.(DES|Blowfish|ARC2|ARC4)', 'medium'),
        ('Debug Setting', r'DEBUG\s*=\s*True', 'medium'),
        ('Insecure Protocol', r'http://', 'low'),
    ]
    
    # Files to exclude
    exclude_dirs = [
        'venv',
        'env',
        '.git',
        'node_modules',
        'migrations',
        'tests',
        'reports',
    ]
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk(project_root):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    # Check each file
    issues = []
    severity_counts = {'high': 0, 'medium': 0, 'low': 0}
    
    for file_path in python_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
                for issue_type, pattern, severity in sensitive_patterns:
                    import re
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    
                    for match in matches:
                        # Skip if in a comment
                        line_start = content.rfind('\n', 0, match.start()) + 1
                        line = content[line_start:content.find('\n', match.start())]
                        if line.strip().startswith('#'):
                            continue
                        
                        # Get line number
                        line_number = content[:match.start()].count('\n') + 1
                        
                        severity_counts[severity] = severity_counts.get(severity, 0) + 1
                        
                        issues.append({
                            'file': os.path.relpath(file_path, project_root),
                            'line': line_number,
                            'issue': f"{issue_type}: {match.group(0)}",
                            'severity': severity,
                            'type': 'Sensitive Data Handling',
                        })
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    
    add_section('Sensitive Data Handling', issues, severity_counts)
    
    print(f"Sensitive data check found {len(issues)} issues.")
    return issues


def check_csrf_protection():
    """Check for CSRF protection issues."""
    print("Checking CSRF protection...")
    
    # Find all view files
    view_files = []
    for root, dirs, files in os.walk(project_root / 'apps'):
        for file in files:
            if file == 'views.py':
                view_files.append(os.path.join(root, file))
    
    # Check each file
    issues = []
    severity_counts = {'high': 0, 'medium': 0, 'low': 0}
    
    for file_path in view_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
                # Check for csrf_exempt
                if '@csrf_exempt' in content:
                    severity_counts['high'] = severity_counts.get('high', 0) + 1
                    
                    # Get line number
                    line_number = content.find('@csrf_exempt')
                    line_number = content[:line_number].count('\n') + 1
                    
                    issues.append({
                        'file': os.path.relpath(file_path, project_root),
                        'line': line_number,
                        'issue': "CSRF protection disabled with @csrf_exempt",
                        'severity': 'high',
                        'type': 'CSRF Protection',
                    })
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    
    add_section('CSRF Protection', issues, severity_counts)
    
    print(f"CSRF protection check found {len(issues)} issues.")
    return issues


def check_sql_injection():
    """Check for potential SQL injection vulnerabilities."""
    print("Checking for SQL injection vulnerabilities...")
    
    # Patterns to look for
    sql_patterns = [
        r'raw\s*\(\s*["\'].+?%s.+?["\']\s*,.+?\)',
        r'execute\s*\(\s*["\'].+?%s.+?["\']\s*,.+?\)',
        r'executemany\s*\(\s*["\'].+?%s.+?["\']\s*,.+?\)',
        r'cursor\.execute\s*\(\s*["\'].+?%s.+?["\']\s*,.+?\)',
        r'cursor\.executemany\s*\(\s*["\'].+?%s.+?["\']\s*,.+?\)',
        r'connection\.execute\s*\(\s*["\'].+?%s.+?["\']\s*,.+?\)',
    ]
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk(project_root / 'apps'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    # Check each file
    issues = []
    severity_counts = {'high': 0, 'medium': 0, 'low': 0}
    
    for file_path in python_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
                for pattern in sql_patterns:
                    import re
                    matches = re.finditer(pattern, content)
                    
                    for match in matches:
                        # Skip if in a comment
                        line_start = content.rfind('\n', 0, match.start()) + 1
                        line = content[line_start:content.find('\n', match.start())]
                        if line.strip().startswith('#'):
                            continue
                        
                        # Get line number
                        line_number = content[:match.start()].count('\n') + 1
                        
                        severity_counts['high'] = severity_counts.get('high', 0) + 1
                        
                        issues.append({
                            'file': os.path.relpath(file_path, project_root),
                            'line': line_number,
                            'issue': f"Potential SQL injection: {match.group(0)}",
                            'severity': 'high',
                            'type': 'SQL Injection',
                        })
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    
    add_section('SQL Injection', issues, severity_counts)
    
    print(f"SQL injection check found {len(issues)} issues.")
    return issues


def main():
    """Run all security checks and generate a report."""
    print(f"Starting security assessment for {report['project']}...")
    print(f"Report will be saved to {output_path}")
    
    # Run all checks
    run_bandit()
    run_safety()
    run_django_checks()
    check_sensitive_data_handling()
    check_csrf_protection()
    check_sql_injection()
    
    # Add recommendations based on findings
    recommendations = []
    
    if report['summary']['high_severity'] > 0:
        recommendations.append({
            'priority': 'Critical',
            'description': 'Address all high severity issues immediately as they pose significant security risks.',
        })
    
    if any(section['title'] == 'Safety Dependency Vulnerability Scanning' and section['issues'] for section in report['sections']):
        recommendations.append({
            'priority': 'High',
            'description': 'Update vulnerable dependencies to their latest secure versions.',
        })
    
    if any(section['title'] == 'Sensitive Data Handling' and section['issues'] for section in report['sections']):
        recommendations.append({
            'priority': 'High',
            'description': 'Review and secure all instances of sensitive data handling, especially hardcoded secrets.',
        })
    
    if any(section['title'] == 'CSRF Protection' and section['issues'] for section in report['sections']):
        recommendations.append({
            'priority': 'High',
            'description': 'Ensure CSRF protection is enabled for all views that modify data.',
        })
    
    if any(section['title'] == 'SQL Injection' and section['issues'] for section in report['sections']):
        recommendations.append({
            'priority': 'High',
            'description': 'Replace raw SQL queries with Django ORM or parameterized queries.',
        })
    
    # Add general recommendations
    recommendations.extend([
        {
            'priority': 'Medium',
            'description': 'Implement regular security scanning as part of the CI/CD pipeline.',
        },
        {
            'priority': 'Medium',
            'description': 'Conduct a thorough code review focusing on security aspects.',
        },
        {
            'priority': 'Medium',
            'description': 'Ensure all forms have proper validation to prevent injection attacks.',
        },
        {
            'priority': 'Low',
            'description': 'Document security practices and create a security incident response plan.',
        },
    ])
    
    report['recommendations'] = recommendations
    
    # Save the report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\nSecurity Assessment Summary:")
    print(f"Total Issues: {report['summary']['total_issues']}")
    print(f"High Severity: {report['summary']['high_severity']}")
    print(f"Medium Severity: {report['summary']['medium_severity']}")
    print(f"Low Severity: {report['summary']['low_severity']}")
    print(f"\nFull report saved to {output_path}")


if __name__ == '__main__':
    main()