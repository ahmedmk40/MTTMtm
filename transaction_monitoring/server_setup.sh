#!/bin/bash

# Exit on error
set -e

# Function to display help
show_help() {
    echo "Transaction Monitoring System Server Setup Script"
    echo ""
    echo "Usage: ./server_setup.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -u, --update               Update system packages"
    echo "  -d, --docker               Install Docker and Docker Compose"
    echo "  -f, --firewall             Configure firewall"
    echo "  -s, --swap SIZE            Create swap file (e.g., 2G)"
    echo "  -t, --timezone ZONE        Set timezone (e.g., UTC)"
    echo "  -a, --all                  Perform all setup steps"
    echo "  -n, --hostname NAME        Set hostname"
    echo ""
    echo "Examples:"
    echo "  ./server_setup.sh -a                  Perform all setup steps"
    echo "  ./server_setup.sh -u -d -f            Update system, install Docker, and configure firewall"
    echo "  ./server_setup.sh -s 4G -t America/New_York  Create 4GB swap and set timezone to America/New_York"
}

# Default values
UPDATE=false
DOCKER=false
FIREWALL=false
SWAP=""
TIMEZONE=""
ALL=false
HOSTNAME=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -u|--update)
            UPDATE=true
            shift
            ;;
        -d|--docker)
            DOCKER=true
            shift
            ;;
        -f|--firewall)
            FIREWALL=true
            shift
            ;;
        -s|--swap)
            SWAP="$2"
            shift 2
            ;;
        -t|--timezone)
            TIMEZONE="$2"
            shift 2
            ;;
        -a|--all)
            ALL=true
            shift
            ;;
        -n|--hostname)
            HOSTNAME="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root or with sudo."
    exit 1
fi

# Set all options if --all is specified
if [ "$ALL" = true ]; then
    UPDATE=true
    DOCKER=true
    FIREWALL=true
    [ -z "$SWAP" ] && SWAP="2G"
    [ -z "$TIMEZONE" ] && TIMEZONE="UTC"
fi

# Set hostname
if [ -n "$HOSTNAME" ]; then
    echo "Setting hostname to $HOSTNAME..."
    hostnamectl set-hostname "$HOSTNAME"
    echo "127.0.0.1 $HOSTNAME" >> /etc/hosts
fi

# Update system packages
if [ "$UPDATE" = true ]; then
    echo "Updating system packages..."
    apt-get update
    apt-get upgrade -y
    apt-get autoremove -y
    apt-get clean
fi

# Install Docker and Docker Compose
if [ "$DOCKER" = true ]; then
    echo "Installing Docker and Docker Compose..."
    
    # Install prerequisites
    apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Set up the stable repository
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    # Add current user to docker group
    if [ -n "$SUDO_USER" ]; then
        usermod -aG docker "$SUDO_USER"
        echo "Added user $SUDO_USER to the docker group. Please log out and log back in for this to take effect."
    fi
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

# Create swap file
if [ -n "$SWAP" ]; then
    echo "Creating swap file of size $SWAP..."
    
    # Check if swap already exists
    if [ "$(swapon --show | wc -l)" -gt 0 ]; then
        echo "Swap already exists. Skipping swap creation."
    else
        # Create swap file
        fallocate -l "$SWAP" /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        
        # Make swap permanent
        echo "/swapfile none swap sw 0 0" >> /etc/fstab
        
        # Configure swappiness
        echo "vm.swappiness=10" >> /etc/sysctl.conf
        echo "vm.vfs_cache_pressure=50" >> /etc/sysctl.conf
        sysctl -p
    fi
fi

# Set timezone
if [ -n "$TIMEZONE" ]; then
    echo "Setting timezone to $TIMEZONE..."
    timedatectl set-timezone "$TIMEZONE"
fi

echo "Server setup completed successfully!"