# Quick Deployment to Hostinger VPS

Fast deployment guide using your GitHub account: https://github.com/surac95

## Prerequisites
- ✅ Hostinger VPS running (31.97.231.244)
- ✅ GitHub account (surac95)
- ✅ Code ready to push to GitHub

---

## Step 1: Push Code to GitHub (From Your Local Machine)

```bash
# Navigate to your project
cd c:/Users/SurendranC/Documents/jira-studio-lab/jira-automation

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - JIRA automation system"

# Add your GitHub repository as remote
git remote add origin https://github.com/surac95/jira-automation.git

# Push to GitHub
git push -u origin main
```

**Note**: If the repository doesn't exist yet:
1. Go to https://github.com/surac95
2. Click "New repository"
3. Name it: `jira-automation`
4. Make it **Private** (contains sensitive config)
5. Don't initialize with README
6. Create repository
7. Then run the commands above

---

## Step 2: One-Command Deployment Script

I'll create an automated deployment script for you!

### On Your Local Machine

Create `deploy.sh`:

```bash
#!/bin/bash

# Hostinger VPS Deployment Script
# This script automates the entire deployment process

VPS_IP="31.97.231.244"
VPS_USER="root"
APP_USER="jirabot"
APP_DIR="/home/$APP_USER/jira-automation"
GITHUB_REPO="https://github.com/surac95/jira-automation.git"

echo "=========================================="
echo "JIRA Automation - Hostinger VPS Deployment"
echo "=========================================="
echo ""

# SSH into VPS and run deployment commands
ssh $VPS_USER@$VPS_IP << 'ENDSSH'

echo "Step 1: Updating system..."
apt update && apt upgrade -y

echo "Step 2: Installing dependencies..."
apt install -y python3.11 python3.11-venv python3-pip git supervisor nginx ufw

echo "Step 3: Creating application user..."
if ! id "jirabot" &>/dev/null; then
    adduser jirabot --disabled-password --gecos ""
fi

echo "Step 4: Cloning repository..."
su - jirabot << 'ENDSU'
cd ~
if [ -d "jira-automation" ]; then
    cd jira-automation
    git pull origin main
else
    git clone https://github.com/surac95/jira-automation.git
    cd jira-automation
fi

echo "Step 5: Setting up Python environment..."
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install schedule==1.2.0

echo "Step 6: Environment file setup..."
echo "Please create .env file manually with your credentials"

ENDSU

echo "Step 7: Configuring Supervisor..."
cat > /etc/supervisor/conf.d/jira-automation.conf << 'EOF'
[program:jira-automation-scheduler]
command=/home/jirabot/jira-automation/venv/bin/python /home/jirabot/jira-automation/scheduler.py
directory=/home/jirabot/jira-automation
user=jirabot
autostart=true
autorestart=true
stderr_logfile=/var/log/jira-automation-scheduler.err.log
stdout_logfile=/var/log/jira-automation-scheduler.out.log
environment=PATH="/home/jirabot/jira-automation/venv/bin"

[program:jira-automation-flask]
command=/home/jirabot/jira-automation/venv/bin/python /home/jirabot/jira-automation/flask_app.py
directory=/home/jirabot/jira-automation
user=jirabot
autostart=true
autorestart=true
stderr_logfile=/var/log/jira-automation-flask.err.log
stdout_logfile=/var/log/jira-automation-flask.out.log
environment=PATH="/home/jirabot/jira-automation/venv/bin"
EOF

echo "Step 8: Configuring Nginx..."
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
nginx -t && systemctl reload nginx

echo "Step 9: Configuring Firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
echo "y" | ufw enable

echo "Step 10: Starting services..."
supervisorctl reread
supervisorctl update

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. SSH to VPS: ssh root@31.97.231.244"
echo "2. Switch to jirabot: su - jirabot"
echo "3. Create .env file: cd jira-automation && nano .env"
echo "4. Start services: exit && supervisorctl start all"
echo "5. Check status: supervisorctl status"
echo ""
echo "Flask app will be available at: http://31.97.231.244"
echo "=========================================="

ENDSSH

echo ""
echo "Deployment script completed!"
echo "Please follow the next steps shown above."
```

---

## Step 3: Run Deployment (Choose One Method)

### Method A: Automated Script (Recommended)

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### Method B: Manual Deployment

```bash
# SSH to your VPS
ssh root@31.97.231.244

# Run these commands one by one:
apt update && apt upgrade -y
apt install -y python3.11 python3.11-venv python3-pip git supervisor nginx

# Create user
adduser jirabot --disabled-password --gecos ""

# Switch to jirabot user
su - jirabot

# Clone repository
git clone https://github.com/surac95/jira-automation.git
cd jira-automation

# Set up Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install schedule==1.2.0

# Exit back to root
exit

# Follow HOSTINGER_VPS_DEPLOYMENT.md for the rest
```

---

## Step 4: Configure Environment Variables

```bash
# SSH to VPS
ssh root@31.97.231.244

# Switch to jirabot
su - jirabot

# Navigate to app
cd jira-automation

# Create .env file
nano .env
```

Paste your configuration:
```env
JIRA_URL=https://jira.issworld.com
JIRA_PAT_TOKEN=your_token_here
JIRA_PROJECT_KEY=ITSD
JIRA_QUEUE_JQL=resolution = Unresolved AND "Resolver Group" = "FMS AMS Level 4 Integrations" and assignee is EMPTY ORDER BY created DESC
MISTRAL_API_KEY=your_key_here
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_CHANNEL_ID=C07XXXXXXXXX
LOG_LEVEL=INFO
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

```bash
# Secure the file
chmod 600 .env

# Exit back to root
exit
```

---

## Step 5: Start Services

```bash
# Reload supervisor
supervisorctl reread
supervisorctl update

# Start services
supervisorctl start jira-automation-scheduler
supervisorctl start jira-automation-flask

# Check status
supervisorctl status
```

You should see:
```
jira-automation-scheduler    RUNNING   pid 12345, uptime 0:00:05
jira-automation-flask        RUNNING   pid 12346, uptime 0:00:05
```

---

## Step 6: Verify Deployment

### Test Flask App
```bash
# From VPS
curl http://localhost:5000/health

# From your browser
http://31.97.231.244/health
```

### Test Automation
```bash
# Switch to jirabot
su - jirabot
cd jira-automation
source venv/bin/activate

# Run manually
python main.py --max-tickets 1

# Exit
exit
```

### View Logs
```bash
# Scheduler logs
tail -f /var/log/jira-automation-scheduler.out.log

# Flask logs
tail -f /var/log/jira-automation-flask.out.log
```

---

## Step 7: Update Slack Interactive URL

Your Flask app is now at:
```
http://31.97.231.244/slack/interactive
```

1. Go to https://api.slack.com/apps
2. Select your app
3. Go to **Interactivity & Shortcuts**
4. Set Request URL: `http://31.97.231.244/slack/interactive`
5. Save

---

## Quick Commands Reference

```bash
# SSH to VPS
ssh root@31.97.231.244

# Check service status
supervisorctl status

# View logs
tail -f /var/log/jira-automation-scheduler.out.log

# Restart services
supervisorctl restart all

# Update code
su - jirabot
cd jira-automation
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
exit
supervisorctl restart all

# Stop services
supervisorctl stop all

# Start services
supervisorctl start all
```

---

## Updating Your Application

When you make changes locally:

```bash
# On your local machine
cd c:/Users/SurendranC/Documents/jira-studio-lab/jira-automation
git add .
git commit -m "Your update message"
git push origin main

# On VPS
ssh root@31.97.231.244
su - jirabot
cd jira-automation
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
exit
supervisorctl restart all
```

---

## Troubleshooting

### Services Won't Start
```bash
# Check logs
supervisorctl tail jira-automation-scheduler stderr
supervisorctl tail jira-automation-flask stderr

# Restart supervisor
systemctl restart supervisor
```

### Can't Access Flask App
```bash
# Check if nginx is running
systemctl status nginx

# Check if Flask is running
supervisorctl status jira-automation-flask

# Check nginx logs
tail -f /var/log/nginx/error.log
```

### Git Authentication Issues
```bash
# Use personal access token
# On GitHub: Settings > Developer settings > Personal access tokens
# Generate token with repo access
# Use: https://TOKEN@github.com/surac95/jira-automation.git
```

---

## Security Notes

1. **Never commit .env file** - It's in .gitignore
2. **Make repository private** - Contains sensitive code
3. **Use SSH keys** - For passwordless authentication
4. **Enable firewall** - Already done in deployment script
5. **Regular updates** - Keep system and packages updated

---

## Success Checklist

- [ ] Code pushed to GitHub
- [ ] VPS deployment completed
- [ ] .env file configured
- [ ] Services running (supervisorctl status)
- [ ] Flask app accessible (http://31.97.231.244)
- [ ] Slack interactive URL updated
- [ ] Test automation run successful
- [ ] Logs showing activity

---

## Your System is Now:

✅ **Running 24/7** on your Hostinger VPS
✅ **Automatically processing** tickets every hour
✅ **Sending Slack notifications** with interactive buttons
✅ **Self-healing** - restarts if it crashes
✅ **Fully logged** - easy to monitor and debug
✅ **Secure** - firewall enabled, services isolated
✅ **Easy to update** - just git push and restart

**Total deployment time: ~15-20 minutes** ⚡

---

Made with ❤️ for seamless automation