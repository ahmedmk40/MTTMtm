#!/bin/bash

# Create SSL directory if it doesn't exist
mkdir -p /workspace/transaction_monitoring/nginx/ssl

# Generate a self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /workspace/transaction_monitoring/nginx/ssl/server.key \
  -out /workspace/transaction_monitoring/nginx/ssl/server.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Set proper permissions
chmod 600 /workspace/transaction_monitoring/nginx/ssl/server.key

echo "Self-signed SSL certificate generated successfully."