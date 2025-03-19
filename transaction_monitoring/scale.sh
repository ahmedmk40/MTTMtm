#!/bin/bash

# Exit on error
set -e

# Function to display help
show_help() {
    echo "Transaction Monitoring System Scaling Script"
    echo ""
    echo "Usage: ./scale.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -s, --service SERVICE      Service to scale (web, celery)"
    echo "  -n, --num-instances NUM    Number of instances to scale to"
    echo "  -u, --up                   Scale up by one instance"
    echo "  -d, --down                 Scale down by one instance"
    echo "  -l, --list                 List current scaling"
    echo ""
    echo "Examples:"
    echo "  ./scale.sh -s web -n 3     Scale web service to 3 instances"
    echo "  ./scale.sh -s celery -u    Scale up celery service by one instance"
    echo "  ./scale.sh -s celery -d    Scale down celery service by one instance"
    echo "  ./scale.sh -l              List current scaling for all services"
}

# Default values
SERVICE=""
NUM_INSTANCES=0
SCALE_UP=false
SCALE_DOWN=false
LIST=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -n|--num-instances)
            NUM_INSTANCES="$2"
            shift 2
            ;;
        -u|--up)
            SCALE_UP=true
            shift
            ;;
        -d|--down)
            SCALE_DOWN=true
            shift
            ;;
        -l|--list)
            LIST=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# List current scaling
if [ "$LIST" = true ]; then
    echo "=== Current Scaling ==="
    docker-compose ps
    exit 0
fi

# Check if service is specified
if [ -z "$SERVICE" ]; then
    echo "Error: Service must be specified with -s or --service"
    show_help
    exit 1
fi

# Check if service is valid
if [ "$SERVICE" != "web" ] && [ "$SERVICE" != "celery" ]; then
    echo "Error: Service must be 'web' or 'celery'"
    show_help
    exit 1
fi

# Get current number of instances
CURRENT_INSTANCES=$(docker-compose ps "$SERVICE" | grep -c "$SERVICE")

# Scale up
if [ "$SCALE_UP" = true ]; then
    NEW_INSTANCES=$((CURRENT_INSTANCES + 1))
    echo "Scaling $SERVICE from $CURRENT_INSTANCES to $NEW_INSTANCES instances..."
    docker-compose up -d --scale "$SERVICE=$NEW_INSTANCES"
    exit 0
fi

# Scale down
if [ "$SCALE_DOWN" = true ]; then
    if [ "$CURRENT_INSTANCES" -le 1 ]; then
        echo "Error: Cannot scale down below 1 instance"
        exit 1
    fi
    NEW_INSTANCES=$((CURRENT_INSTANCES - 1))
    echo "Scaling $SERVICE from $CURRENT_INSTANCES to $NEW_INSTANCES instances..."
    docker-compose up -d --scale "$SERVICE=$NEW_INSTANCES"
    exit 0
fi

# Scale to specific number
if [ "$NUM_INSTANCES" -gt 0 ]; then
    echo "Scaling $SERVICE from $CURRENT_INSTANCES to $NUM_INSTANCES instances..."
    docker-compose up -d --scale "$SERVICE=$NUM_INSTANCES"
    exit 0
fi

# If we get here, no valid action was specified
echo "Error: No valid action specified"
show_help
exit 1