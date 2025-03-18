#!/bin/bash

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo "Redis is not installed. Installing Redis..."
    sudo apt-get update
    sudo apt-get install -y redis-server
fi

# Start Redis server
redis-server