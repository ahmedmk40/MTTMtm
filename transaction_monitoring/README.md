# Transaction Monitoring and Fraud Detection System

A robust transaction monitoring and fraud detection system capable of processing and analyzing various payment transactions in real-time. The system identifies potentially fraudulent activities across multiple channels (POS, e-commerce, and digital wallets) while maintaining high throughput and low latency.

## Features

- **Real-time Transaction Processing**: Process transactions with sub-500ms response times
- **Multi-channel Support**: Handle POS, e-commerce, and wallet transactions
- **Comprehensive Fraud Detection**:
  - Transaction velocity monitoring
  - Amount pattern analysis
  - Location-based risk assessment
  - Card testing detection
  - Device intelligence
  - Behavioral pattern analysis
- **Advanced AML Capabilities**:
  - Transaction syndication detection
  - Circular flow analysis
  - Party connection analysis
  - Layering and structuring detection
- **Case Management**:
  - Create and manage fraud investigation cases
  - Link transactions to cases for investigation
  - Add notes and attachments to cases
  - Track case activities and status changes
  - Assign cases to users for investigation
- **Machine Learning Models**:
  - Anomaly detection
  - Classification models
  - Behavioral analysis
- **Role-based Access Control**:
  - Compliance officers
  - Fraud analysts
  - Risk managers
  - System administrators
  - Data analysts
  - Executive users

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │━━━▶│ Transaction API │━━━▶│  Fraud Engine   │━━━▶│   Response      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                    ┃ ┃ ┃
          ┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━┻━┻━┻━━━━━━━━━━━━━━━━━━┓
          ▼                  ▼                  ▼                          ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    ┌─────────────────┐
│  Block Check    │  │   Rule Engine   │  │ Velocity Engine │    │    ML Engine    │
└─────────────────┘  └─────────────────┘  └─────────────────┘    └─────────────────┘
          ┃                  ┃                  ┃                          ┃
          ┗━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                                                    ┃
          ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━┓
          ▼                                                              ▼
┌─────────────────┐                                              ┌─────────────────┐
│  Database Layer │                                              │  Webhook Layer  │
└─────────────────┘                                              └─────────────────┘
```

## Technology Stack

- **Backend**: Python, Django, Django REST Framework
- **Database**: PostgreSQL (configurable)
- **Caching**: Redis
- **Task Queue**: Celery
- **Machine Learning**: Scikit-learn, TensorFlow/PyTorch
- **Frontend**: Bootstrap, Chart.js, jQuery

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL or SQLite
- Redis

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/transaction-monitoring.git
   cd transaction-monitoring
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements/dev.txt
   ```

4. Set up the database:
   ```bash
   python manage.py migrate
   ```

5. Initialize the system:
   ```bash
   python manage.py initialize_rules
   python manage.py initialize_velocity_rules
   python manage.py initialize_ml_models
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver 0.0.0.0:59781
   ```

8. Start Redis (message broker for Celery):
   ```bash
   ./start_redis.sh
   ```

9. Start Celery worker:
   ```bash
   ./start_celery.sh
   ```

### Using Docker Compose (Recommended)

You can also use Docker Compose to run the entire stack:

```bash
docker-compose up
```

This will start:
- Django web application
- Redis (message broker)
- Celery worker
- Celery beat (for scheduled tasks)

## Usage

### API Endpoints

- **Process Transaction**: `POST /api/process-transaction/`
- **Transaction List**: `GET /api/transactions/`
- **Transaction Detail**: `GET /api/transactions/{transaction_id}/`
- **Case List**: `GET /api/cases/`
- **Case Detail**: `GET /api/cases/{case_id}/`
- **Case Transactions**: `GET /api/cases/{case_id}/transactions/`
- **Case Notes**: `GET /api/cases/{case_id}/notes/`

### Web Interface

- **Admin Dashboard**: `/admin/`
- **Transaction List**: `/transactions/`
- **Flagged Transactions**: `/transactions/flagged/`
- **Case Management**: `/cases/`
- **User Dashboard**: `/dashboard/`

## Development

### Project Structure

```
transaction_monitoring/             # Main project directory
│
├── config/                         # Project configuration
│   ├── settings/                   # Settings module
│   ├── urls.py                     # Main URL routing
│   ├── wsgi.py                     # WSGI configuration
│   └── asgi.py                     # ASGI configuration
│
├── apps/                           # Application modules
│   ├── api/                        # API app
│   ├── core/                       # Core app with shared functionality
│   ├── accounts/                   # User authentication and management
│   ├── transactions/               # Transaction processing
│   ├── fraud_engine/               # Fraud detection engine
│   ├── rule_engine/                # Rule processing engine
│   ├── velocity_engine/            # Velocity monitoring
│   ├── ml_engine/                  # Machine learning engine
│   ├── aml/                        # Anti-Money Laundering
│   ├── cases/                      # Case management
│   ├── dashboard/                  # User dashboards
│   ├── reporting/                  # Reporting functionality
│   └── notifications/              # Alert notifications
│
├── templates/                      # HTML templates
├── static/                         # Static files
├── media/                          # User-uploaded files
├── docs/                           # Documentation
├── tests/                          # Project-level tests
├── scripts/                        # Utility scripts
├── requirements/                   # Requirements files
└── docker/                         # Docker configuration
```

### Running Tests

```bash
python manage.py test
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Django and Django REST Framework communities
- Scikit-learn and TensorFlow/PyTorch communities
- Bootstrap and Chart.js communities