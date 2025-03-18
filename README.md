# Transaction Monitoring System

A comprehensive transaction monitoring system for financial institutions to detect and prevent fraud, money laundering, and other financial crimes.

## Features

- **Real-time Transaction Monitoring**: Monitor transactions as they occur to detect suspicious activity.
- **Rule-based Detection**: Configure rules to detect specific patterns of suspicious activity.
- **Merchant-specific Rules**: Apply different rules to different merchants based on risk profiles.
- **AML Pattern Detection**: Advanced pattern detection for Anti-Money Laundering compliance.
- **Case Management**: Track and manage investigations of suspicious activity.
- **Reporting**: Generate reports for regulatory compliance.

## Components

- **Rule Engine**: Configurable rules for transaction monitoring.
- **AML Module**: Anti-Money Laundering detection and compliance.
- **Fraud Engine**: Fraud detection and prevention.
- **Velocity Engine**: Monitor transaction velocity and patterns.
- **ML Engine**: Machine learning models for advanced detection.

## Getting Started

### Prerequisites

- Python 3.8+
- Django 4.2+
- Redis (for Celery)
- PostgreSQL (recommended for production)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/transaction-monitoring.git
   cd transaction-monitoring
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. Initialize rules:
   ```bash
   python manage.py initialize_rules
   ```

5. Run the development server:
   ```bash
   python manage.py runserver
   ```

### Production Deployment

For production deployment, additional steps are required:

1. Configure environment variables for production settings.
2. Use a production-ready database like PostgreSQL.
3. Set up a proper web server (Nginx, Apache) with WSGI.
4. Configure Celery with Redis for background tasks.
5. Set up SSL/TLS for secure connections.

## Usage

### Creating Merchant-specific Rules

You can assign rules to specific merchants using the management command:

```bash
# Assign a rule to a specific merchant
python manage.py assign_merchant_rule <rule_id> <merchant_id>

# Exclude a merchant from a rule
python manage.py assign_merchant_rule <rule_id> <merchant_id> --exclude

# Remove a merchant from a rule's inclusion/exclusion list
python manage.py assign_merchant_rule <rule_id> <merchant_id> --remove
```

### Testing Rules

You can test rules with the following command:

```bash
python manage.py test_merchant_rules --rule_id=<rule_id> --merchant_id=<merchant_id> --amount=<amount>
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.