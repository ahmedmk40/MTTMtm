#!/bin/bash

# Exit on error
set -e

# Function to display help
show_help() {
    echo "Transaction Monitoring System Test Script"
    echo ""
    echo "Usage: ./run_tests.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -a, --all                  Run all tests"
    echo "  -u, --unit                 Run unit tests"
    echo "  -i, --integration          Run integration tests"
    echo "  -p, --performance          Run performance tests"
    echo "  -c, --coverage             Generate coverage report"
    echo "  -v, --verbose              Run tests in verbose mode"
    echo "  -k, --keyword KEYWORD      Run tests matching keyword"
    echo "  -m, --module MODULE        Run tests for specific module"
    echo "  -d, --docker               Run tests in Docker container"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh -a                  Run all tests"
    echo "  ./run_tests.sh -u -c               Run unit tests with coverage report"
    echo "  ./run_tests.sh -m transactions     Run tests for transactions module"
    echo "  ./run_tests.sh -k fraud -v         Run tests matching 'fraud' in verbose mode"
}

# Default values
ALL=false
UNIT=false
INTEGRATION=false
PERFORMANCE=false
COVERAGE=false
VERBOSE=false
KEYWORD=""
MODULE=""
DOCKER=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -a|--all)
            ALL=true
            shift
            ;;
        -u|--unit)
            UNIT=true
            shift
            ;;
        -i|--integration)
            INTEGRATION=true
            shift
            ;;
        -p|--performance)
            PERFORMANCE=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -k|--keyword)
            KEYWORD="$2"
            shift 2
            ;;
        -m|--module)
            MODULE="$2"
            shift 2
            ;;
        -d|--docker)
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

# Set default if no test type is specified
if [ "$ALL" = false ] && [ "$UNIT" = false ] && [ "$INTEGRATION" = false ] && [ "$PERFORMANCE" = false ]; then
    ALL=true
fi

# Build test command
TEST_CMD="python manage.py test"

# Add verbosity
if [ "$VERBOSE" = true ]; then
    TEST_CMD="$TEST_CMD -v 2"
else
    TEST_CMD="$TEST_CMD -v 1"
fi

# Add coverage
if [ "$COVERAGE" = true ]; then
    TEST_CMD="coverage run --source='.' $TEST_CMD"
fi

# Add module
if [ -n "$MODULE" ]; then
    TEST_CMD="$TEST_CMD apps.$MODULE"
fi

# Add keyword
if [ -n "$KEYWORD" ]; then
    TEST_CMD="$TEST_CMD -k $KEYWORD"
fi

# Add test types
if [ "$ALL" = true ]; then
    # Run all tests
    :
elif [ "$UNIT" = true ] && [ "$INTEGRATION" = true ] && [ "$PERFORMANCE" = true ]; then
    # Run all tests
    :
elif [ "$UNIT" = true ] && [ "$INTEGRATION" = true ]; then
    # Exclude performance tests
    TEST_CMD="$TEST_CMD --exclude-tag=performance"
elif [ "$UNIT" = true ] && [ "$PERFORMANCE" = true ]; then
    # Exclude integration tests
    TEST_CMD="$TEST_CMD --exclude-tag=integration"
elif [ "$INTEGRATION" = true ] && [ "$PERFORMANCE" = true ]; then
    # Exclude unit tests
    TEST_CMD="$TEST_CMD --exclude-tag=unit"
elif [ "$UNIT" = true ]; then
    # Only unit tests
    TEST_CMD="$TEST_CMD --tag=unit"
elif [ "$INTEGRATION" = true ]; then
    # Only integration tests
    TEST_CMD="$TEST_CMD --tag=integration"
elif [ "$PERFORMANCE" = true ]; then
    # Only performance tests
    TEST_CMD="$TEST_CMD --tag=performance"
fi

# Run tests
echo "Running tests with command: $TEST_CMD"

if [ "$DOCKER" = true ]; then
    # Run tests in Docker container
    docker-compose exec web bash -c "$TEST_CMD"
else
    # Run tests locally
    eval "$TEST_CMD"
fi

# Generate coverage report
if [ "$COVERAGE" = true ]; then
    echo "Generating coverage report..."
    if [ "$DOCKER" = true ]; then
        docker-compose exec web bash -c "coverage report"
        docker-compose exec web bash -c "coverage html"
    else
        coverage report
        coverage html
    fi
    echo "HTML coverage report generated in htmlcov/ directory"
fi