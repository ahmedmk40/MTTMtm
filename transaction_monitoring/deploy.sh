#!/bin/bash

# Exit on error
set -e

# Function to display help
show_help() {
    echo "Transaction Monitoring System Deployment Script"
    echo ""
    echo "Usage: ./deploy.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -e, --env-file FILE        Specify the environment file (default: .env)"
    echo "  -b, --build                Build the Docker images"
    echo "  -s, --ssl                  Generate self-signed SSL certificates"
    echo "  -c, --collect-static       Collect static files"
    echo "  -m, --migrate              Run database migrations"
    echo "  -i, --initialize           Initialize rules and ML models"
    echo "  -r, --restart              Restart all services"
    echo "  -d, --down                 Stop all services"
    echo "  -u, --up                   Start all services"
    echo "  -l, --logs                 Show logs"
    echo "  -p, --production           Deploy in production mode"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh -p -b -s       Deploy in production mode, build images, and generate SSL certs"
    echo "  ./deploy.sh -u -m -i       Start services, run migrations, and initialize data"
    echo "  ./deploy.sh -r             Restart all services"
    echo "  ./deploy.sh -l             Show logs"
}

# Default values
ENV_FILE=".env"
BUILD=false
SSL=false
COLLECT_STATIC=false
MIGRATE=false
INITIALIZE=false
RESTART=false
DOWN=false
UP=false
LOGS=false
PRODUCTION=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -e|--env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -s|--ssl)
            SSL=true
            shift
            ;;
        -c|--collect-static)
            COLLECT_STATIC=true
            shift
            ;;
        -m|--migrate)
            MIGRATE=true
            shift
            ;;
        -i|--initialize)
            INITIALIZE=true
            shift
            ;;
        -r|--restart)
            RESTART=true
            shift
            ;;
        -d|--down)
            DOWN=true
            shift
            ;;
        -u|--up)
            UP=true
            shift
            ;;
        -l|--logs)
            LOGS=true
            shift
            ;;
        -p|--production)
            PRODUCTION=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if .env file exists
if [ ! -f "$ENV_FILE" ] && [ "$ENV_FILE" != ".env.example" ]; then
    echo "Environment file $ENV_FILE not found."
    echo "Creating from .env.example..."
    cp .env.example "$ENV_FILE"
fi

# Set environment variables
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

# Generate SSL certificates if requested
if [ "$SSL" = true ]; then
    echo "Generating SSL certificates..."
    mkdir -p nginx/ssl
    ./nginx/generate-ssl-certs.sh
fi

# Build Docker images if requested
if [ "$BUILD" = true ]; then
    echo "Building Docker images..."
    docker-compose build
fi

# Stop services if requested
if [ "$DOWN" = true ]; then
    echo "Stopping services..."
    docker-compose down
fi

# Start services if requested
if [ "$UP" = true ]; then
    echo "Starting services..."
    if [ "$PRODUCTION" = true ]; then
        docker-compose up -d
    else
        docker-compose up -d
    fi
fi

# Restart services if requested
if [ "$RESTART" = true ]; then
    echo "Restarting services..."
    docker-compose restart
fi

# Run migrations if requested
if [ "$MIGRATE" = true ]; then
    echo "Running migrations..."
    docker-compose exec web python manage.py migrate
fi

# Collect static files if requested
if [ "$COLLECT_STATIC" = true ]; then
    echo "Collecting static files..."
    docker-compose exec web python manage.py collectstatic --noinput
fi

# Initialize data if requested
if [ "$INITIALIZE" = true ]; then
    echo "Initializing rules..."
    docker-compose exec web python manage.py initialize_rules
    
    echo "Initializing ML models..."
    docker-compose exec web python manage.py initialize_ml_models
fi

# Show logs if requested
if [ "$LOGS" = true ]; then
    echo "Showing logs..."
    docker-compose logs -f
fi

echo "Deployment completed successfully!"