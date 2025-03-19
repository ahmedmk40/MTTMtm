#!/bin/bash

# Exit on error
set -e

# Function to display help
show_help() {
    echo "Transaction Monitoring System Development Setup Script"
    echo ""
    echo "Usage: ./setup_dev.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -v, --venv                 Create a virtual environment"
    echo "  -d, --dependencies         Install dependencies"
    echo "  -m, --migrate              Run database migrations"
    echo "  -s, --superuser            Create a superuser"
    echo "  -i, --initialize           Initialize rules and ML models"
    echo "  -a, --all                  Perform all setup steps"
    echo "  -c, --clean                Clean existing environment before setup"
    echo "  -p, --python PYTHON        Python executable to use (default: python3)"
    echo ""
    echo "Examples:"
    echo "  ./setup_dev.sh -a                  Perform all setup steps"
    echo "  ./setup_dev.sh -v -d -m            Create virtual environment, install dependencies, and run migrations"
    echo "  ./setup_dev.sh -c -a -p python3.9  Clean environment and perform all setup steps with Python 3.9"
}

# Default values
VENV=false
DEPENDENCIES=false
MIGRATE=false
SUPERUSER=false
INITIALIZE=false
ALL=false
CLEAN=false
PYTHON="python3"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--venv)
            VENV=true
            shift
            ;;
        -d|--dependencies)
            DEPENDENCIES=true
            shift
            ;;
        -m|--migrate)
            MIGRATE=true
            shift
            ;;
        -s|--superuser)
            SUPERUSER=true
            shift
            ;;
        -i|--initialize)
            INITIALIZE=true
            shift
            ;;
        -a|--all)
            ALL=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -p|--python)
            PYTHON="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Set all options if --all is specified
if [ "$ALL" = true ]; then
    VENV=true
    DEPENDENCIES=true
    MIGRATE=true
    SUPERUSER=true
    INITIALIZE=true
fi

# Clean environment
if [ "$CLEAN" = true ]; then
    echo "Cleaning environment..."
    
    # Remove virtual environment
    if [ -d "venv" ]; then
        echo "Removing virtual environment..."
        rm -rf venv
    fi
    
    # Remove database
    if [ -f "db.sqlite3" ]; then
        echo "Removing database..."
        rm db.sqlite3
    fi
    
    # Remove migrations
    echo "Removing migrations..."
    find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
    find . -path "*/migrations/*.pyc" -delete
    
    # Remove cache
    echo "Removing cache..."
    find . -name "__pycache__" -type d -exec rm -rf {} +
    find . -name "*.pyc" -delete
    
    # Remove static files
    if [ -d "staticfiles" ]; then
        echo "Removing static files..."
        rm -rf staticfiles
    fi
    
    # Remove media files
    if [ -d "media" ]; then
        echo "Removing media files..."
        rm -rf media
    fi
    
    # Remove logs
    if [ -d "logs" ]; then
        echo "Removing logs..."
        rm -rf logs
    fi
fi

# Create virtual environment
if [ "$VENV" = true ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
fi

# Install dependencies
if [ "$DEPENDENCIES" = true ]; then
    echo "Installing dependencies..."
    
    # Check if virtual environment is activated
    if [ -z "$VIRTUAL_ENV" ] && [ "$VENV" = true ]; then
        source venv/bin/activate
    fi
    
    # Install dependencies
    pip install -r requirements.txt
    
    # Install development dependencies if they exist
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
    fi
fi

# Run migrations
if [ "$MIGRATE" = true ]; then
    echo "Running migrations..."
    
    # Check if virtual environment is activated
    if [ -z "$VIRTUAL_ENV" ] && [ "$VENV" = true ]; then
        source venv/bin/activate
    fi
    
    # Make migrations
    python manage.py makemigrations
    
    # Run migrations
    python manage.py migrate
fi

# Create superuser
if [ "$SUPERUSER" = true ]; then
    echo "Creating superuser..."
    
    # Check if virtual environment is activated
    if [ -z "$VIRTUAL_ENV" ] && [ "$VENV" = true ]; then
        source venv/bin/activate
    fi
    
    # Create superuser
    python manage.py createsuperuser
fi

# Initialize rules and ML models
if [ "$INITIALIZE" = true ]; then
    echo "Initializing rules and ML models..."
    
    # Check if virtual environment is activated
    if [ -z "$VIRTUAL_ENV" ] && [ "$VENV" = true ]; then
        source venv/bin/activate
    fi
    
    # Initialize rules
    python manage.py initialize_rules
    
    # Initialize ML models
    python manage.py initialize_ml_models
fi

echo "Development environment setup completed successfully!"
if [ "$VENV" = true ]; then
    echo "To activate the virtual environment, run: source venv/bin/activate"
fi