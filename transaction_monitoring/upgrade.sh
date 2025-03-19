#!/bin/bash

# Exit on error
set -e

# Function to display help
show_help() {
    echo "Transaction Monitoring System Upgrade Script"
    echo ""
    echo "Usage: ./upgrade.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -b, --backup               Create a backup before upgrading"
    echo "  -p, --pull                 Pull latest code from repository"
    echo "  -r, --rebuild              Rebuild Docker images"
    echo "  -m, --migrate              Run database migrations"
    echo "  -c, --collect-static       Collect static files"
    echo "  -i, --initialize           Initialize rules and ML models"
    echo "  -a, --all                  Perform all upgrade steps"
    echo "  -f, --force                Force upgrade without confirmation"
    echo ""
    echo "Examples:"
    echo "  ./upgrade.sh -a            Perform all upgrade steps with confirmation"
    echo "  ./upgrade.sh -a -f         Perform all upgrade steps without confirmation"
    echo "  ./upgrade.sh -b -p -r      Backup, pull latest code, and rebuild images"
}

# Default values
BACKUP=false
PULL=false
REBUILD=false
MIGRATE=false
COLLECT_STATIC=false
INITIALIZE=false
ALL=false
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -b|--backup)
            BACKUP=true
            shift
            ;;
        -p|--pull)
            PULL=true
            shift
            ;;
        -r|--rebuild)
            REBUILD=true
            shift
            ;;
        -m|--migrate)
            MIGRATE=true
            shift
            ;;
        -c|--collect-static)
            COLLECT_STATIC=true
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
        -f|--force)
            FORCE=true
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
    BACKUP=true
    PULL=true
    REBUILD=true
    MIGRATE=true
    COLLECT_STATIC=true
    INITIALIZE=true
fi

# Confirm upgrade
if [ "$FORCE" = false ]; then
    echo "You are about to upgrade the Transaction Monitoring System with the following options:"
    [ "$BACKUP" = true ] && echo "- Create a backup"
    [ "$PULL" = true ] && echo "- Pull latest code"
    [ "$REBUILD" = true ] && echo "- Rebuild Docker images"
    [ "$MIGRATE" = true ] && echo "- Run database migrations"
    [ "$COLLECT_STATIC" = true ] && echo "- Collect static files"
    [ "$INITIALIZE" = true ] && echo "- Initialize rules and ML models"
    
    read -p "Do you want to continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Upgrade cancelled."
        exit 0
    fi
fi

# Create a backup
if [ "$BACKUP" = true ]; then
    echo "Creating backup..."
    ./backup.sh
fi

# Pull latest code
if [ "$PULL" = true ]; then
    echo "Pulling latest code..."
    git pull
fi

# Rebuild Docker images
if [ "$REBUILD" = true ]; then
    echo "Rebuilding Docker images..."
    docker-compose build
fi

# Stop services
echo "Stopping services..."
docker-compose down

# Start services
echo "Starting services..."
docker-compose up -d

# Run database migrations
if [ "$MIGRATE" = true ]; then
    echo "Running database migrations..."
    docker-compose exec web python manage.py migrate
fi

# Collect static files
if [ "$COLLECT_STATIC" = true ]; then
    echo "Collecting static files..."
    docker-compose exec web python manage.py collectstatic --noinput
fi

# Initialize rules and ML models
if [ "$INITIALIZE" = true ]; then
    echo "Initializing rules..."
    docker-compose exec web python manage.py initialize_rules
    
    echo "Initializing ML models..."
    docker-compose exec web python manage.py initialize_ml_models
fi

echo "Upgrade completed successfully!"