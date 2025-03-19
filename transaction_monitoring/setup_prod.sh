#!/bin/bash

# Exit on error
set -e

# Function to display help
show_help() {
    echo "Transaction Monitoring System Production Setup Script"
    echo ""
    echo "Usage: ./setup_prod.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -d, --domain DOMAIN        Domain name for the application (required)"
    echo "  -e, --email EMAIL          Email address for Let's Encrypt (required)"
    echo "  -s, --server-setup         Run server setup script"
    echo "  -c, --clone                Clone repository"
    echo "  -b, --branch BRANCH        Branch to clone (default: main)"
    echo "  -l, --letsencrypt          Set up Let's Encrypt SSL certificates"
    echo "  -f, --firewall             Configure firewall"
    echo "  -a, --all                  Perform all setup steps"
    echo ""
    echo "Examples:"
    echo "  ./setup_prod.sh -d example.com -e admin@example.com -a  Perform all setup steps for example.com"
    echo "  ./setup_prod.sh -d example.com -e admin@example.com -s -c -l  Set up server, clone repository, and set up SSL"
}

# Default values
DOMAIN=""
EMAIL=""
SERVER_SETUP=false
CLONE=false
BRANCH="main"
LETSENCRYPT=false
FIREWALL=false
ALL=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -e|--email)
            EMAIL="$2"
            shift 2
            ;;
        -s|--server-setup)
            SERVER_SETUP=true
            shift
            ;;
        -c|--clone)
            CLONE=true
            shift
            ;;
        -b|--branch)
            BRANCH="$2"
            shift 2
            ;;
        -l|--letsencrypt)
            LETSENCRYPT=true
            shift
            ;;
        -f|--firewall)
            FIREWALL=true
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

# Check if domain is specified
if [ -z "$DOMAIN" ]; then
    echo "Error: Domain must be specified with -d or --domain"
    show_help
    exit 1
fi

# Check if email is specified
if [ -z "$EMAIL" ]; then
    echo "Error: Email must be specified with -e or --email"
    show_help
    exit 1
fi

# Set all options if --all is specified
if [ "$ALL" = true ]; then
    SERVER_SETUP=true
    CLONE=true
    LETSENCRYPT=true
    FIREWALL=true
fi

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root or with sudo."
    exit 1
fi

# Create app directory
APP_DIR="/opt/transaction-monitoring"
echo "Creating application directory: $APP_DIR"
mkdir -p "$APP_DIR"

# Run server setup
if [ "$SERVER_SETUP" = true ]; then
    echo "Running server setup..."
    
    # Update system packages
    apt-get update
    apt-get upgrade -y
    
    # Install dependencies
    apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release git
    
    # Set up Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    # Set hostname
    hostnamectl set-hostname "$DOMAIN"
    echo "127.0.0.1 $DOMAIN" >> /etc/hosts
    
    # Create swap file if needed
    if [ "$(free -m | awk '/^Swap:/ {print $2}')" -eq 0 ]; then
        echo "Creating swap file..."
        fallocate -l 2G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo "/swapfile none swap sw 0 0" >> /etc/fstab
        echo "vm.swappiness=10" >> /etc/sysctl.conf
        echo "vm.vfs_cache_pressure=50" >> /etc/sysctl.conf
        sysctl -p
    fi
fi

# Clone repository
if [ "$CLONE" = true ]; then
    echo "Cloning repository..."
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        echo "Git is not installed. Installing..."
        apt-get update
        apt-get install -y git
    fi
    
    # Clone repository
    cd "$APP_DIR"
    git clone -b "$BRANCH" https://github.com/your-username/transaction-monitoring.git .
fi

# Configure firewall
if [ "$FIREWALL" = true ]; then
    echo "Configuring firewall..."
    
    # Install UFW if not already installed
    apt-get install -y ufw
    
    # Configure UFW
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Enable UFW
    echo "y" | ufw enable
fi

# Set up Let's Encrypt
if [ "$LETSENCRYPT" = true ]; then
    echo "Setting up Let's Encrypt SSL certificates..."
    
    # Install certbot
    apt-get install -y certbot
    
    # Create nginx directory
    mkdir -p "$APP_DIR/nginx/ssl"
    
    # Get certificates
    certbot certonly --standalone -d "$DOMAIN" -d "www.$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive
    
    # Copy certificates
    cp /etc/letsencrypt/live/"$DOMAIN"/fullchain.pem "$APP_DIR/nginx/ssl/server.crt"
    cp /etc/letsencrypt/live/"$DOMAIN"/privkey.pem "$APP_DIR/nginx/ssl/server.key"
    
    # Set proper permissions
    chmod 644 "$APP_DIR/nginx/ssl/server.crt"
    chmod 600 "$APP_DIR/nginx/ssl/server.key"
    
    # Set up auto-renewal
    echo "0 0 * * * certbot renew --quiet && cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $APP_DIR/nginx/ssl/server.crt && cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $APP_DIR/nginx/ssl/server.key" | crontab -
fi

# Create .env file
echo "Creating .env file..."
cat > "$APP_DIR/.env" << EOF
# Django settings
SECRET_KEY=$(openssl rand -base64 32)
DEBUG=False
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN

# Database settings
DB_NAME=transaction_monitoring
DB_USER=postgres
DB_PASSWORD=$(openssl rand -base64 12)
DB_HOST=db
DB_PORT=5432

# Redis settings
REDIS_URL=redis://redis:6379/0

# Email settings
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=noreply@$DOMAIN

# Superuser settings
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=$(openssl rand -base64 12)
DJANGO_SUPERUSER_EMAIL=$EMAIL

# Initialization flags
INITIALIZE_RULES=true
INITIALIZE_ML_MODELS=true

# Gunicorn settings
GUNICORN_WORKERS=4
GUNICORN_WORKER_CLASS=sync
GUNICORN_TIMEOUT=120
EOF

# Update Nginx configuration
echo "Updating Nginx configuration..."
cat > "$APP_DIR/nginx/conf.d/default.conf" << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirect all HTTP requests to HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name $DOMAIN www.$DOMAIN;
    
    # SSL configuration
    ssl_certificate /etc/nginx/ssl/server.crt;
    ssl_certificate_key /etc/nginx/ssl/server.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Static files
    location /static/ {
        alias /var/www/html/static/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # Media files
    location /media/ {
        alias /var/www/html/media/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # Proxy requests to Django
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
    
    # Deny access to .htaccess files
    location ~ /\.ht {
        deny all;
    }
    
    # Deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

# Start the application
echo "Starting the application..."
cd "$APP_DIR"
docker-compose up -d

echo "Production setup completed successfully!"
echo "Your Transaction Monitoring System is now running at https://$DOMAIN"
echo "Admin username: admin"
echo "Admin password: $(grep DJANGO_SUPERUSER_PASSWORD "$APP_DIR/.env" | cut -d= -f2)"
echo ""
echo "Please make sure to:"
echo "1. Update the email settings in .env file"
echo "2. Change the admin password after first login"
echo "3. Set up regular backups"
echo ""
echo "For more information, see the documentation at https://github.com/your-username/transaction-monitoring"