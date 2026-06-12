# PowerShell Deployment Script for Hostinger VPS
# This script deploys the JIRA automation system to your VPS at 31.97.231.244

$VPS_IP = "31.97.231.244"
$VPS_USER = "root"
$GITHUB_REPO = "https://github.com/surac95/jira-studio-lab.git"

Write-Host "========================================" -ForegroundColor Green
Write-Host "JIRA Automation - VPS Deployment Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Function to print status
function Print-Status {
    param($Message)
    Write-Host ">>> $Message" -ForegroundColor Yellow
}

function Print-Success {
    param($Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Print-Error {
    param($Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

# Check if SSH is available
Print-Status "Checking SSH availability..."
$sshCheck = Get-Command ssh -ErrorAction SilentlyContinue
if (-not $sshCheck) {
    Print-Error "SSH command not found. Please install OpenSSH client."
    Write-Host "Install from: Settings > Apps > Optional Features > OpenSSH Client"
    exit 1
}

Print-Status "Testing SSH connection to ${VPS_IP}..."
Write-Host "You may be prompted for the VPS root password..." -ForegroundColor Cyan
Write-Host ""

# Create deployment script content
$deployScript = @'
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

ln -sf /etc/nginx/sites-available/jira-automation /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

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
echo ""
echo "4. Access Flask app:"
echo "   http://31.97.231.244"
echo ""
echo "5. Configure Slack Interactive URL:"
echo "   http://31.97.231.244/slack/interactive"
echo ""
'@

# Execute deployment
Print-Status "Starting deployment to ${VPS_IP}..."
Write-Host ""

try {
    $deployScript | ssh "${VPS_USER}@${VPS_IP}" "bash -s"
    
    Print-Success "Deployment completed successfully!"
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "NEXT STEPS:" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Configure your environment variables:"
    Write-Host "   ssh ${VPS_USER}@${VPS_IP}"
    Write-Host "   nano /home/jirabot/jira-automation/jira-automation/.env"
    Write-Host ""
    Write-Host "2. Add your credentials to .env file:" -ForegroundColor Cyan
    Write-Host "   - JIRA_URL"
    Write-Host "   - JIRA_PAT_TOKEN"
    Write-Host "   - MISTRAL_API_KEY"
    Write-Host "   - SLACK_BOT_TOKEN"
    Write-Host "   - SLACK_CHANNEL_ID"
    Write-Host ""
    Write-Host "3. Restart services after editing .env:"
    Write-Host "   supervisorctl restart all"
    Write-Host ""
    Write-Host "4. Monitor the application:"
    Write-Host "   supervisorctl status"
    Write-Host "   tail -f /var/log/jira-automation-scheduler.out.log"
    Write-Host ""
    Write-Host "5. Access your Flask app at:"
    Write-Host "   http://${VPS_IP}" -ForegroundColor Green
    Write-Host ""
    Write-Host "Deployment script finished!" -ForegroundColor Green
}
catch {
    Print-Error "Deployment failed: $_"
    Write-Host ""
    Write-Host "Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "1. Ensure you can SSH to the VPS: ssh ${VPS_USER}@${VPS_IP}"
    Write-Host "2. Check if the VPS is running"
    Write-Host "3. Verify your SSH credentials"
    exit 1
}

# Made with Bob
