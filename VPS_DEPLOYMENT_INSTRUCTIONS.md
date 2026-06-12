# 🚀 Quick VPS Deployment Instructions

## Your Setup
- **VPS IP**: 31.97.231.244
- **GitHub Repo**: https://github.com/surac95/jira-studio-lab
- **OS**: Ubuntu 24.04

---

## Option 1: Automated Deployment (Recommended) ⭐

### For Windows (PowerShell):

1. **Open PowerShell** in your project directory:
   ```powershell
   cd c:\Users\SurendranC\Documents\jira-studio-lab
   ```

2. **Run the deployment script**:
   ```powershell
   .\deploy-to-vps.ps1
   ```

3. **Enter your VPS root password** when prompted

4. **Wait for deployment** (5-10 minutes)

### For Linux/Mac (Bash):

1. **Make script executable**:
   ```bash
   chmod +x deploy-to-vps.sh
   ```

2. **Run the deployment script**:
   ```bash
   ./deploy-to-vps.sh
   ```

3. **Enter your VPS root password** when prompted

---

## Option 2: Manual Deployment

### Step 1: Connect to VPS
```bash
ssh root@31.97.231.244
```

### Step 2: Run Quick Setup
```bash
# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3.11 python3.11-venv python3-pip git supervisor nginx ufw

# Create app user
adduser jirabot --disabled-password --gecos ""

# Clone repository
cd /home/jirabot
sudo -u jirabot git clone https://github.com/surac95/jira-studio-lab.git jira-automation
cd jira-automation/jira-automation

# Setup Python environment
sudo -u jirabot python3.11 -m venv venv
sudo -u jirabot venv/bin/pip install -r requirements.txt
sudo -u jirabot venv/bin/pip install schedule==1.2.0

# Create .env file
sudo -u jirabot cp .env.example .env
```

### Step 3: Configure Environment Variables
```bash
nano /home/jirabot/jira-automation/jira-automation/.env
```

Add your credentials:
```env
JIRA_URL=https://jira.issworld.com
JIRA_PAT_TOKEN=your_actual_token_here
JIRA_PROJECT_KEY=ITSD
JIRA_QUEUE_JQL=resolution = Unresolved AND "Resolver Group" = "FMS AMS Level 4 Integrations" and assignee is EMPTY ORDER BY created DESC

MISTRAL_API_KEY=your_actual_mistral_key_here

SLACK_BOT_TOKEN=xoxb-your-actual-token-here
SLACK_CHANNEL_ID=C07XXXXXXXXX

LOG_LEVEL=INFO
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

### Step 4: Setup Supervisor
```bash
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

supervisorctl reread
supervisorctl update
supervisorctl start all
```

### Step 5: Setup Nginx
```bash
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
systemctl reload nginx
```

### Step 6: Configure Firewall
```bash
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
```

---

## Post-Deployment Steps

### 1. Verify Services are Running
```bash
ssh root@31.97.231.244
supervisorctl status
```

Expected output:
```
jira-automation-scheduler    RUNNING   pid 12345, uptime 0:00:05
jira-automation-flask        RUNNING   pid 12346, uptime 0:00:05
```

### 2. Check Logs
```bash
# Scheduler logs
tail -f /var/log/jira-automation-scheduler.out.log

# Flask app logs
tail -f /var/log/jira-automation-flask.out.log

# Error logs
tail -f /var/log/jira-automation-scheduler.err.log
```

### 3. Test Flask App
Open browser: http://31.97.231.244

You should see the Flask app homepage.

### 4. Configure Slack Interactive URL
1. Go to https://api.slack.com/apps
2. Select your app
3. Go to **Interactivity & Shortcuts**
4. Enable Interactivity
5. Set Request URL: `http://31.97.231.244/slack/interactive`
6. Save changes

### 5. Test the System
```bash
# SSH to VPS
ssh root@31.97.231.244

# Switch to app user
su - jirabot

# Navigate to app
cd jira-automation/jira-automation

# Activate virtual environment
source venv/bin/activate

# Run a test
python main.py --max-tickets 1
```

---

## Management Commands

### View Service Status
```bash
supervisorctl status
```

### Restart Services
```bash
supervisorctl restart jira-automation-scheduler
supervisorctl restart jira-automation-flask
# Or restart all:
supervisorctl restart all
```

### Stop Services
```bash
supervisorctl stop all
```

### Update Application
```bash
# SSH to VPS
ssh root@31.97.231.244

# Switch to app user
su - jirabot
cd jira-automation

# Pull latest changes
git pull origin master

# Install any new dependencies
source jira-automation/venv/bin/activate
pip install -r jira-automation/requirements.txt

# Exit and restart services
exit
supervisorctl restart all
```

### View Logs in Real-Time
```bash
# Scheduler
tail -f /var/log/jira-automation-scheduler.out.log

# Flask
tail -f /var/log/jira-automation-flask.out.log

# All errors
tail -f /var/log/jira-automation-*.err.log
```

---

## Troubleshooting

### Services Not Starting
```bash
# Check detailed logs
supervisorctl tail jira-automation-scheduler stderr
supervisorctl tail jira-automation-flask stderr

# Restart supervisor
systemctl restart supervisor
```

### Can't Access Flask App
```bash
# Check nginx status
systemctl status nginx

# Check nginx logs
tail -f /var/log/nginx/error.log

# Restart nginx
systemctl restart nginx
```

### Environment Variables Not Loading
```bash
# Verify .env file exists and has correct permissions
ls -la /home/jirabot/jira-automation/jira-automation/.env
cat /home/jirabot/jira-automation/jira-automation/.env

# Restart services after editing .env
supervisorctl restart all
```

---

## What Happens After Deployment?

✅ **Scheduler runs every hour** - Automatically processes JIRA tickets
✅ **Flask app runs 24/7** - Handles Slack interactive buttons
✅ **Auto-restart on failure** - Supervisor ensures services stay running
✅ **Logs everything** - Easy debugging and monitoring
✅ **Secure setup** - Firewall configured, dedicated user

---

## Quick Reference

| Component | Location | Command |
|-----------|----------|---------|
| Application | `/home/jirabot/jira-automation/jira-automation/` | `cd /home/jirabot/jira-automation/jira-automation` |
| Virtual Env | `/home/jirabot/jira-automation/jira-automation/venv/` | `source venv/bin/activate` |
| Logs | `/var/log/jira-automation-*.log` | `tail -f /var/log/jira-automation-*.log` |
| Services | Supervisor | `supervisorctl status` |
| Flask App | http://31.97.231.244 | Browser |
| Slack URL | http://31.97.231.244/slack/interactive | Slack App Settings |

---

## Need Help?

1. Check logs first: `tail -f /var/log/jira-automation-*.log`
2. Verify services: `supervisorctl status`
3. Test manually: `python main.py --max-tickets 1`
4. Review the detailed guide: `jira-automation/HOSTINGER_VPS_DEPLOYMENT.md`

---

**Your JIRA automation is ready to deploy! 🚀**

Choose automated deployment for easiest setup, or follow manual steps for more control.