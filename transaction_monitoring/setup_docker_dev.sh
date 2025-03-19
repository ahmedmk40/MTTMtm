#!/bin/bash

# Exit on error
set -e

# Function to display help
show_help() {
    echo "Transaction Monitoring System Docker Development Setup Script"
    echo ""
    echo "Usage: ./setup_docker_dev.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -b, --build                Build Docker images"
    echo "  -u, --up                   Start Docker containers"
    echo "  -d, --down                 Stop Docker containers"
    echo "  -m, --migrate              Run database migrations"
    echo "  -s, --superuser            Create a superuser"
    echo "  -i, --initialize           Initialize rules and ML models"
    echo "  -c, --clean                Clean Docker environment (remove containers, volumes, etc.)"
    echo "  -l, --logs                 Show logs"
    echo "  -a, --all                  Perform all setup steps"
    echo ""
    echo "Examples:"
    echo "  ./setup_docker_dev.sh -a                  Perform all setup steps"
    echo "  ./setup_docker_dev.sh -b -u -m            Build images, start containers, and run migrations"
    echo "  ./setup_docker_dev.sh -c -a               Clean environment and perform all setup steps"
}

# Default values
BUILD=false
UP=false
DOWN=false
MIGRATE=false
SUPERUSER=false
INITIALIZE=false
CLEAN=false
LOGS=false
ALL=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -u|--up)
            UP=true
            shift
            ;;
        -d|--down)
            DOWN=true
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
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -l|--logs)
            LOGS=true
            shift
            ;;
        -a|--all)
            ALL=true
            shift
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
    BUILD=true
    UP=true
    MIGRATE=true
    SUPERUSER=true
    INITIALIZE=true
    LOGS=true
fi

# Clean Docker environment
if [ "$CLEAN" = true ]; then
    echo "Cleaning Docker environment..."
    
    # Stop containers
    docker-compose down
    
    # Remove volumes
    docker-compose down -v
    
    # Remove images
    docker-compose down --rmi all
    
    # Remove orphaned containers
    docker-compose down --remove-orphans
    
    # Remove unused volumes
    docker volume prune -f
    
    # Remove unused networks
    docker network prune -f
    
    # Remove unused images
    docker image prune -f
fi

# Build Docker images
if [ "$BUILD" = true ]; then
    echo "Building Docker images..."
    docker-compose build
fi

# Stop Docker containers
if [ "$DOWN" = true ]; then
    echo "Stopping Docker containers..."
    docker-compose down
fi

# Start Docker containers
if [ "$UP" = true ]; then
    echo "Starting Docker containers..."
    docker-compose up -d
fi

# Run database migrations
if [ "$MIGRATE" = true ]; then
    echo "Running database migrations..."
    docker-compose exec web python manage.py migrate
fi

# Create superuser
if [ "$SUPERUSER" = true ]; then
    echo "Creating superuser..."
    docker-compose exec web python manage.py createsuperuser
fi

# Initialize rules and ML models
if [ "$INITIALIZE" = true ]; then
    echo "Initializing rules..."
    docker-compose exec web python manage.py initialize_rules
    
    echo "Initializing ML models..."
    docker-compose exec web python manage.py initialize_ml_models
fi

# Show logs
if [ "$LOGS" = true ]; then
    echo "Showing logs..."
    docker-compose logs -f
fi

if [ "$LOGS" = false ]; then
    echo "Docker development environment setup completed successfully!"
    echo "To view logs, run: docker-compose logs -f"
    echo "To access the application, go to: http://localhost:8000"
fi