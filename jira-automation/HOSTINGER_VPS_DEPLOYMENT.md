# Hostinger VPS Deployment Guide

Complete guide to deploy the JIRA automation system on your Hostinger VPS (Ubuntu 24.04).

## Your VPS Details
- **OS**: Ubuntu 24.04
- **Type**: KVM 2
- **SSH Access**: `ssh root@31.97.231.244`
- **Resources**: 100 GB disk, plenty for this application

---

## Step 1: Connect to Your VPS

```bash
# From your local machine
ssh root@31.97.231.244

# Enter your root password when prompted
```

---

## Step 2: Update System & Install Dependencies

```bash
# Update package list
apt update && apt upgrade -y

# Install Python 3.11 and pip
apt install python3.11 python3.11-venv python3-pip git -y

# Install supervisor (for process management)
apt install supervisor -y

# Install nginx (for Flask app - optional)
apt install nginx -y
```

---

## Step 3: Create Application User (Security Best Practice)

```bash
# Create a dedicated user for the application
adduser jirabot --disabled-password --gecos ""

# Switch to the new user
su - jirabot
```

---

## Step 4: Clone Your Repository

```bash
# If you have the code in GitHub
git clone https://github.com/YOUR_USERNAME/jira-automation.git
cd jira-automation

# OR upload your local code using SCP from your local machine:
# scp -r jira-automation root@31.97.231.244:/home/jirabot/
```

---

## Step 5: Set Up Python Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Add schedule package for scheduler
pip install schedule==1.2.0
```

---

## Step 6: Configure Environment Variables

```bash
# Create .env file
nano .env

# Paste your configuration (from local .env):
```

```env
# JIRA Configuration
JIRA_URL=https://jira.issworld.com
JIRA_PAT_TOKEN=your_token_here
JIRA_PROJECT_KEY=ITSD
JIRA_QUEUE_JQL=resolution = Unresolved AND "Resolver Group" = "FMS AMS Level 4 Integrations" and assignee is EMPTY ORDER BY created DESC

# Mistral AI Configuration
MISTRAL_API_KEY=your_mistral_key_here

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_CHANNEL_ID=C07XXXXXXXXX

# Logging
LOG_LEVEL=INFO
```

```bash
# Save: Ctrl+O, Enter, Ctrl+X

# Secure the file
chmod 600 .env
```

---

## Step 7: Test the Application

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Test a single run
python main.py --max-tickets 1

# If successful, you should see:
# - Tickets fetched
# - AI analysis
# - Assignment
# - Slack notification
```

---

## Step 8: Set Up Supervisor (Process Manager)

Exit from jirabot user back to root:
```bash
exit  # Back to root user
```

Create supervisor configuration:
```bash
nano /etc/supervisor/conf.d/jira-automation.conf
```

Add this configuration:
```ini
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
```

Update supervisor and start services:
```bash
# Reload supervisor configuration
supervisorctl reread
supervisorctl update

# Start the services
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

## Step 9: Set Up Nginx (For Flask App)

Create nginx configuration:
```bash
nano /etc/nginx/sites-available/jira-automation
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name 31.97.231.244;  # Your VPS IP

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
# Create symbolic link
ln -s /etc/nginx/sites-available/jira-automation /etc/nginx/sites-enabled/

# Test nginx configuration
nginx -t

# Reload nginx
systemctl reload nginx
```

---

## Step 10: Configure Slack Interactive URL

Your Flask app is now accessible at:
```
http://31.97.231.244/slack/interactive
```

Add this URL to your Slack App settings:
1. Go to https://api.slack.com/apps
2. Select your app
3. Go to **Interactivity & Shortcuts**
4. Enable Interactivity
5. Set Request URL: `http://31.97.231.244/slack/interactive`
6. Save changes

---

## Step 11: Set Up SSL (Optional but Recommended)

Install Certbot for free SSL:
```bash
# Install certbot
apt install certbot python3-certbot-nginx -y

# Get SSL certificate (requires a domain name)
# If you have a domain pointing to your VPS:
certbot --nginx -d yourdomain.com

# Follow the prompts
```

If you don't have a domain, you can:
1. Use Hostinger's domain services
2. Use a free service like DuckDNS
3. Continue with HTTP (less secure)

---

## Management Commands

### View Logs
```bash
# Scheduler logs
tail -f /var/log/jira-automation-scheduler.out.log

# Flask app logs
tail -f /var/log/jira-automation-flask.out.log

# Error logs
tail -f /var/log/jira-automation-scheduler.err.log
tail -f /var/log/jira-automation-flask.err.log
```

### Control Services
```bash
# Stop services
supervisorctl stop jira-automation-scheduler
supervisorctl stop jira-automation-flask

# Start services
supervisorctl start jira-automation-scheduler
supervisorctl start jira-automation-flask

# Restart services
supervisorctl restart jira-automation-scheduler
supervisorctl restart jira-automation-flask

# View status
supervisorctl status
```

### Update Application
```bash
# Switch to jirabot user
su - jirabot

# Navigate to app directory
cd jira-automation

# Activate virtual environment
source venv/bin/activate

# Pull latest changes (if using git)
git pull origin main

# Install any new dependencies
pip install -r requirements.txt

# Exit back to root
exit

# Restart services
supervisorctl restart jira-automation-scheduler
supervisorctl restart jira-automation-flask
```

---

## Monitoring & Maintenance

### Set Up Cron for Health Checks (Optional)
```bash
# Edit crontab
crontab -e

# Add health check (runs every 5 minutes)
*/5 * * * * supervisorctl status | grep -q "RUNNING" || supervisorctl restart all
```

### Monitor Resource Usage
```bash
# Check CPU and memory
htop

# Check disk usage
df -h

# Check running processes
ps aux | grep python
```

### Backup Configuration
```bash
# Backup .env file
cp /home/jirabot/jira-automation/.env /home/jirabot/jira-automation/.env.backup

# Backup supervisor config
cp /etc/supervisor/conf.d/jira-automation.conf /root/jira-automation.conf.backup
```

---

## Troubleshooting

### Services Not Starting
```bash
# Check supervisor logs
supervisorctl tail jira-automation-scheduler
supervisorctl tail jira-automation-flask

# Check if port 5000 is in use
netstat -tulpn | grep 5000

# Restart supervisor
systemctl restart supervisor
```

### Flask App Not Accessible
```bash
# Check nginx status
systemctl status nginx

# Check nginx error logs
tail -f /var/log/nginx/error.log

# Test nginx configuration
nginx -t

# Restart nginx
systemctl restart nginx
```

### Python Dependencies Issues
```bash
# Reinstall dependencies
su - jirabot
cd jira-automation
source venv/bin/activate
pip install --force-reinstall -r requirements.txt
```

### Scheduler Not Running
```bash
# Check if schedule package is installed
su - jirabot
cd jira-automation
source venv/bin/activate
pip list | grep schedule

# If not installed:
pip install schedule==1.2.0

# Restart scheduler
exit
supervisorctl restart jira-automation-scheduler
```

---

## Security Best Practices

### 1. Firewall Configuration
```bash
# Install UFW (Uncomplicated Firewall)
apt install ufw -y

# Allow SSH
ufw allow 22/tcp

# Allow HTTP
ufw allow 80/tcp

# Allow HTTPS (if using SSL)
ufw allow 443/tcp

# Enable firewall
ufw enable

# Check status
ufw status
```

### 2. Secure SSH
```bash
# Edit SSH config
nano /etc/ssh/sshd_config

# Change these settings:
PermitRootLogin no  # Disable root login
PasswordAuthentication no  # Use SSH keys only
Port 2222  # Change default port (optional)

# Restart SSH
systemctl restart sshd
```

### 3. Regular Updates
```bash
# Set up automatic security updates
apt install unattended-upgrades -y
dpkg-reconfigure --priority=low unattended-upgrades
```

### 4. Monitor Failed Login Attempts
```bash
# Install fail2ban
apt install fail2ban -y

# Start and enable
systemctl start fail2ban
systemctl enable fail2ban
```

---

## Performance Optimization

### 1. Adjust Scheduler Frequency
Edit `scheduler.py` to change run frequency:
```python
# Run every 2 hours instead of every hour
schedule.every(2).hours.do(run_automation)

# Or run at specific times
schedule.every().day.at("09:00").do(run_automation)
schedule.every().day.at("14:00").do(run_automation)
schedule.every().day.at("18:00").do(run_automation)
```

### 2. Limit Tickets Per Run
```bash
# In scheduler.py, change max-tickets parameter
["python", "main.py", "--max-tickets", "5"]  # Process 5 instead of 10
```

### 3. Monitor Resource Usage
```bash
# Install monitoring tools
apt install htop iotop nethogs -y

# Check real-time usage
htop
```

---

## Quick Reference

### Important Paths
- Application: `/home/jirabot/jira-automation/`
- Virtual Environment: `/home/jirabot/jira-automation/venv/`
- Logs: `/var/log/jira-automation-*.log`
- Nginx Config: `/etc/nginx/sites-available/jira-automation`
- Supervisor Config: `/etc/supervisor/conf.d/jira-automation.conf`

### Important Commands
```bash
# View all services
supervisorctl status

# Restart all services
supervisorctl restart all

# View logs
tail -f /var/log/jira-automation-scheduler.out.log

# Update application
su - jirabot && cd jira-automation && git pull && exit
supervisorctl restart all

# Check system resources
htop
df -h
free -h
```

---

## Cost & Resources

### Your VPS Specifications
- **CPU**: Shared (KVM 2)
- **RAM**: ~2GB (estimated)
- **Disk**: 100 GB
- **Bandwidth**: 8 TB

### Application Resource Usage
- **CPU**: <5% (mostly idle, spikes during runs)
- **RAM**: ~200-300 MB
- **Disk**: ~500 MB (including dependencies)
- **Network**: Minimal (API calls only)

**Your VPS is more than sufficient for this application!**

---

## Next Steps

1. ✅ Connect to VPS
2. ✅ Install dependencies
3. ✅ Set up application
4. ✅ Configure supervisor
5. ✅ Set up nginx
6. ✅ Configure Slack
7. ✅ Test everything
8. ✅ Set up monitoring
9. ✅ Secure the server
10. ✅ Enjoy automated ticket management!

---

## Support

If you encounter any issues:
1. Check the logs first
2. Verify environment variables
3. Test components individually
4. Review this guide
5. Check Hostinger documentation

---

**Your JIRA automation is now running 24/7 on your Hostinger VPS!** 🎉

The system will:
- Run every hour automatically
- Process up to 10 tickets per run
- Send Slack notifications with interactive buttons
- Handle errors gracefully
- Restart automatically if it crashes
- Log everything for debugging

Made with ❤️ for seamless automation