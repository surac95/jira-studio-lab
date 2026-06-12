#!/bin/bash

# Automated Deployment Script for Hostinger VPS
# This script deploys the JIRA automation system to your VPS at 31.97.231.244

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# VPS Configuration
VPS_IP="31.97.231.244"
VPS_USER="root"
APP_USER="jirabot"
APP_DIR="/home/jirabot/jira-automation"
GITHUB_REPO="https://github.com/surac95/jira-studio-lab.git"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}JIRA Automation - VPS Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${YELLOW}>>> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if SSH key exists
print_status "Checking SSH connection..."
if ssh -o BatchMode=yes -o ConnectTimeout=5 ${VPS_USER}@${VPS_IP} echo "OK" 2>&1 | grep -q "OK"; then
    print_success "SSH connection successful"
else
    print_error "Cannot connect to VPS. Please ensure:"
    echo "  1. VPS is running"
    echo "  2. You have SSH access (password or key)"
    echo "  3. IP address is correct: ${VPS_IP}"
    exit 1
fi

# Deploy to VPS
print_status "Starting deployment to ${VPS_IP}..."

ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
set -e

echo ">>> Updating system packages..."
apt update && apt upgrade -y

echo ">>> Installing dependencies..."
apt install -y python3.11 python3.11-venv python3-pip git supervisor nginx ufw

echo ">>> Creating application user (jirabot)..."
if ! id -u jirabot > /dev/null 2>&1; then
    adduser jirabot --disabled-password --gecos ""
    echo "✓ User jirabot created"
else
    echo "✓ User jirabot already exists"
fi

echo ">>> Cloning repository..."
if [ -d "/home/jirabot/jira-automation" ]; then
    echo "Directory exists, pulling latest changes..."
    cd /home/jirabot/jira-automation
    sudo -u jirabot git pull origin master || sudo -u jirabot git pull origin main
else
    cd /home/jirabot
    sudo -u jirabot git clone https://github.com/surac95/jira-studio-lab.git jira-automation
fi

cd /home/jirabot/jira-automation/jira-automation

echo ">>> Setting up Python virtual environment..."
sudo -u jirabot python3.11 -m venv venv
sudo -u jirabot venv/bin/pip install --upgrade pip
sudo -u jirabot venv/bin/pip install -r requirements.txt
sudo -u jirabot venv/bin/pip install schedule==1.2.0

echo ">>> Creating .env file template..."
if [ ! -f ".env" ]; then
    sudo -u jirabot cp .env.example .env
    echo "✓ .env file created from template"
    echo "⚠ IMPORTANT: You need to edit /home/jirabot/jira-automation/jira-automation/.env with your credentials"
else
    echo "✓ .env file already exists"
fi

echo ">>> Setting up Supervisor configuration..."
cat > /etc/supervisor/conf.d/jira-automation.conf << 'EOF'
[program:jira-automation-scheduler]
command=/home/jirabot/jira-automation/jira-automation/venv/bin/python /home/jirabot/jira-automation/jira-automation/scheduler.py
directory=/home/jirabot/jira-automation/jira-automation
user=jirabot
autostart=true
autorestart=true
stderr_logfile=/var/log/jira-automation-scheduler.err.log
stdout_logfile=/var/log/jira-automation-scheduler.out.log
environment=PATH="/home/jirabot/jira-automation/jira-automation/venv/bin"

[program:jira-automation-flask]
command=/home/jirabot/jira-automation/jira-automation/venv/bin/python /home/jirabot/jira-automation/jira-automation/flask_app.py
directory=/home/jirabot/jira-automation/jira-automation
user=jirabot
autostart=true
autorestart=true
stderr_logfile=/var/log/jira-automation-flask.err.log
stdout_logfile=/var/log/jira-automation-flask.out.log
environment=PATH="/home/jirabot/jira-automation/jira-automation/venv/bin"
EOF

echo ">>> Setting up Nginx configuration..."
cat > /etc/nginx/sites-available/jira-automation << 'EOF'
server {
    listen 80;
    server_name 31.97.231.244;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable nginx site
ln -sf /etc/nginx/sites-available/jira-automation /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

echo ">>> Configuring firewall..."
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp

echo ">>> Reloading services..."
supervisorctl reread
supervisorctl update
systemctl reload nginx

echo ">>> Checking service status..."
sleep 3
supervisorctl status

echo ""
echo "========================================="
echo "✓ Deployment Complete!"
echo "========================================="
echo ""
echo "IMPORTANT NEXT STEPS:"
echo "1. Edit the .env file with your credentials:"
echo "   ssh root@31.97.231.244"
echo "   nano /home/jirabot/jira-automation/jira-automation/.env"
echo ""
echo "2. After editing .env, restart services:"
echo "   supervisorctl restart all"
echo ""
echo "3. View logs:"
echo "   tail -f /var/log/jira-automation-scheduler.out.log"
echo "   tail -f /var/log/jira-automation-flask.out.log"
echo ""
echo "4. Access Flask app:"
echo "   http://31.97.231.244"
echo ""
echo "5. Configure Slack Interactive URL:"
echo "   http://31.97.231.244/slack/interactive"
echo ""
ENDSSH

print_success "Deployment completed successfully!"
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}NEXT STEPS:${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "1. Configure your environment variables:"
echo "   ssh ${VPS_USER}@${VPS_IP}"
echo "   nano ${APP_DIR}/jira-automation/.env"
echo ""
echo "2. Add your credentials to .env file:"
echo "   - JIRA_URL"
echo "   - JIRA_PAT_TOKEN"
echo "   - MISTRAL_API_KEY"
echo "   - SLACK_BOT_TOKEN"
echo "   - SLACK_CHANNEL_ID"
echo ""
echo "3. Restart services after editing .env:"
echo "   supervisorctl restart all"
echo ""
echo "4. Monitor the application:"
echo "   supervisorctl status"
echo "   tail -f /var/log/jira-automation-scheduler.out.log"
echo ""
echo "5. Access your Flask app at:"
echo "   http://${VPS_IP}"
echo ""
echo -e "${GREEN}Deployment script finished!${NC}"

# Made with Bob
