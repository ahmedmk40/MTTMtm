#!/bin/bash

# Exit on error
set -e

# Function to display help
show_help() {
    echo "Transaction Monitoring System Sample Data Generator"
    echo ""
    echo "Usage: ./generate_sample_data.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -t, --transactions NUM     Number of transactions to generate (default: 100)"
    echo "  -u, --users NUM            Number of users to generate (default: 10)"
    echo "  -m, --merchants NUM        Number of merchants to generate (default: 5)"
    echo "  -f, --fraud PERCENT        Percentage of fraudulent transactions (default: 5)"
    echo "  -d, --days NUM             Number of days in the past to generate data for (default: 30)"
    echo "  -c, --clean                Clean existing data before generating new data"
    echo "  -o, --docker               Run in Docker container"
    echo ""
    echo "Examples:"
    echo "  ./generate_sample_data.sh -t 1000 -u 50 -m 20  Generate 1000 transactions for 50 users and 20 merchants"
    echo "  ./generate_sample_data.sh -f 10 -d 60          Generate transactions with 10% fraud rate over 60 days"
    echo "  ./generate_sample_data.sh -c -t 500            Clean existing data and generate 500 transactions"
}

# Default values
TRANSACTIONS=100
USERS=10
MERCHANTS=5
FRAUD=5
DAYS=30
CLEAN=false
DOCKER=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--transactions)
            TRANSACTIONS="$2"
            shift 2
            ;;
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -m|--merchants)
            MERCHANTS="$2"
            shift 2
            ;;
        -f|--fraud)
            FRAUD="$2"
            shift 2
            ;;
        -d|--days)
            DAYS="$2"
            shift 2
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -o|--docker)
            DOCKER=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Build command
CMD=""

if [ "$CLEAN" = true ]; then
    CMD="python manage.py cleanup_transactions && "
fi

CMD="${CMD}python manage.py create_multiple_users --num_users=$USERS && "
CMD="${CMD}python manage.py create_multiple_merchants --num_merchants=$MERCHANTS && "
CMD="${CMD}python manage.py generate_transactions --num_transactions=$TRANSACTIONS --fraud_percentage=$FRAUD --days_back=$DAYS"

# Run command
echo "Generating sample data with the following parameters:"
echo "- Transactions: $TRANSACTIONS"
echo "- Users: $USERS"
echo "- Merchants: $MERCHANTS"
echo "- Fraud percentage: $FRAUD%"
echo "- Days back: $DAYS"
if [ "$CLEAN" = true ]; then
    echo "- Clean existing data: Yes"
fi

if [ "$DOCKER" = true ]; then
    echo "Running in Docker container..."
    docker-compose exec web bash -c "$CMD"
else
    echo "Running locally..."
    eval "$CMD"
fi

echo "Sample data generation completed successfully!"