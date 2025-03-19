#!/bin/bash

# Exit on error
set -e

# Function to display help
show_help() {
    echo "Transaction Monitoring System Monitoring Script"
    echo ""
    echo "Usage: ./monitor.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -l, --logs                 Show logs for all services"
    echo "  -s, --service SERVICE      Show logs for a specific service (web, db, redis, celery, nginx)"
    echo "  -f, --follow               Follow log output"
    echo "  -t, --tail LINES           Number of lines to show (default: 100)"
    echo "  -d, --disk                 Show disk usage"
    echo "  -m, --memory               Show memory usage"
    echo "  -c, --cpu                  Show CPU usage"
    echo "  -a, --all                  Show all system information"
    echo "  -p, --processes            Show running processes"
    echo "  -n, --network              Show network connections"
    echo "  -r, --restart SERVICE      Restart a specific service"
    echo ""
    echo "Examples:"
    echo "  ./monitor.sh -l -f         Show and follow logs for all services"
    echo "  ./monitor.sh -s web -f     Show and follow logs for the web service"
    echo "  ./monitor.sh -a            Show all system information"
    echo "  ./monitor.sh -r web        Restart the web service"
}

# Default values
LOGS=false
SERVICE="all"
FOLLOW=false
TAIL=100
DISK=false
MEMORY=false
CPU=false
ALL=false
PROCESSES=false
NETWORK=false
RESTART=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -l|--logs)
            LOGS=true
            shift
            ;;
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -t|--tail)
            TAIL="$2"
            shift 2
            ;;
        -d|--disk)
            DISK=true
            shift
            ;;
        -m|--memory)
            MEMORY=true
            shift
            ;;
        -c|--cpu)
            CPU=true
            shift
            ;;
        -a|--all)
            ALL=true
            shift
            ;;
        -p|--processes)
            PROCESSES=true
            shift
            ;;
        -n|--network)
            NETWORK=true
            shift
            ;;
        -r|--restart)
            RESTART="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Show logs
if [ "$LOGS" = true ]; then
    if [ "$SERVICE" = "all" ]; then
        if [ "$FOLLOW" = true ]; then
            docker-compose logs --tail="$TAIL" -f
        else
            docker-compose logs --tail="$TAIL"
        fi
    else
        if [ "$FOLLOW" = true ]; then
            docker-compose logs "$SERVICE" --tail="$TAIL" -f
        else
            docker-compose logs "$SERVICE" --tail="$TAIL"
        fi
    fi
fi

# Show disk usage
if [ "$DISK" = true ] || [ "$ALL" = true ]; then
    echo "=== Disk Usage ==="
    df -h
    echo ""
    echo "=== Docker Disk Usage ==="
    docker system df
    echo ""
fi

# Show memory usage
if [ "$MEMORY" = true ] || [ "$ALL" = true ]; then
    echo "=== Memory Usage ==="
    free -h
    echo ""
    echo "=== Docker Memory Usage ==="
    docker stats --no-stream
    echo ""
fi

# Show CPU usage
if [ "$CPU" = true ] || [ "$ALL" = true ]; then
    echo "=== CPU Usage ==="
    top -bn1 | head -20
    echo ""
fi

# Show processes
if [ "$PROCESSES" = true ] || [ "$ALL" = true ]; then
    echo "=== Running Docker Containers ==="
    docker-compose ps
    echo ""
fi

# Show network connections
if [ "$NETWORK" = true ] || [ "$ALL" = true ]; then
    echo "=== Network Connections ==="
    netstat -tuln
    echo ""
    echo "=== Docker Networks ==="
    docker network ls
    echo ""
fi

# Restart service
if [ -n "$RESTART" ]; then
    echo "=== Restarting $RESTART service ==="
    docker-compose restart "$RESTART"
    echo ""
fi