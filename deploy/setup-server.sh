#!/bin/bash
# Renty Dynamic Pricing System - Server Setup Script
# Run on Ubuntu 22.04+ server

set -e

echo "=========================================="
echo "  Renty Dynamic Pricing System Setup"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Configuration
APP_DIR="/opt/renty-pricing"
LOG_DIR="/var/log/renty"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Installing system dependencies...${NC}"
apt update
apt install -y python3 python3-pip python3-venv nodejs npm nginx certbot

echo -e "${GREEN}Step 2: Creating directories...${NC}"
mkdir -p $APP_DIR
mkdir -p $LOG_DIR
mkdir -p /etc/nginx/ssl

echo -e "${GREEN}Step 3: Setting up Python environment...${NC}"
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}Step 4: Building frontend...${NC}"
cd $APP_DIR/frontend_prototype
npm install
npm run build

echo -e "${GREEN}Step 5: Setting up systemd service...${NC}"
cp $APP_DIR/deploy/renty-api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable renty-api

echo -e "${GREEN}Step 6: Configuring Nginx...${NC}"
cp $APP_DIR/deploy/nginx.conf /etc/nginx/sites-available/renty
ln -sf /etc/nginx/sites-available/renty /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

echo -e "${GREEN}Step 7: Setting permissions...${NC}"
chown -R www-data:www-data $APP_DIR
chown -R www-data:www-data $LOG_DIR
chmod -R 755 $APP_DIR

echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Copy your SSL certificate (cert.pem and key.pem) to /etc/nginx/ssl/"
echo "2. Update the domain in /etc/nginx/sites-available/renty"
echo "3. Update database connection in config.py"
echo "4. Start the services:"
echo "   sudo systemctl start renty-api"
echo "   sudo nginx -t && sudo systemctl reload nginx"
echo ""
echo "Access the dashboard at: https://your-domain.com"

