# 🎮 JIRA Automation - Operations Guide

**Private Guide for System Operations**

---

## 📋 Quick Reference

### Your VPS Details
- **IP Address**: 31.97.231.244
- **SSH Access**: `ssh root@31.97.231.244`
- **Application URL**: http://31.97.231.244:5000
- **Slack Interactive URL**: http://31.97.231.244:5000/slack/interactive

---

## 🚀 Service Management

### Check Service Status
```bash
ssh root@31.97.231.244
supervisorctl status
```

**Expected Output:**
```
jira-automation-flask        RUNNING   pid 12345, uptime 1:23:45
jira-automation-scheduler    RUNNING   pid 12346, uptime 1:23:45
```

### Stop Services
```bash
# Stop scheduler (stops automatic hourly runs)
supervisorctl stop jira-automation-scheduler

# Stop Flask app (stops Slack interactive buttons)
supervisorctl stop jira-automation-flask

# Stop both
supervisorctl stop all
```

### Start Services
```bash
# Start scheduler
supervisorctl start jira-automation-scheduler

# Start Flask app
supervisorctl start jira-automation-flask

# Start both
supervisorctl start all
```

### Restart Services
```bash
# Restart after code changes or configuration updates
supervisorctl restart all
```

---

## ⏰ Scheduler Configuration

### Current Schedule
- **Frequency**: Every 1 hour
- **Max Tickets**: 10 per run
- **First Run**: Immediately on startup
- **Timeout**: 5 minutes per run

### Change Schedule Frequency

**Edit the scheduler:**
```bash
ssh root@31.97.231.244
nano /home/jirabot/jira-automation/jira-automation/scheduler.py
```

**Find line 87 and change:**
```python
# Current: Every hour
schedule.every().hour.do(run_automation)

# Options:
schedule.every(30).minutes.do(run_automation)  # Every 30 minutes
schedule.every(2).hours.do(run_automation)     # Every 2 hours
schedule.every().day.at("09:00").do(run_automation)  # Daily at 9 AM
```

**After editing, restart:**
```bash
supervisorctl restart jira-automation-scheduler
```

### Change Max Tickets Per Run

**Edit line 39 in scheduler.py:**
```python
["python", "main.py", "--max-tickets", "20"]  # Change 10 to 20
```

---

## 🔧 Manual Operations

### Run Automation Manually (One-Time)
```bash
# SSH to VPS
ssh root@31.97.231.244

# Switch to app user
su - jirabot

# Navigate to app
cd jira-automation/jira-automation

# Activate virtual environment
source venv/bin/activate

# Run automation (process 5 tickets)
python main.py --max-tickets 5

# Dry run (test without making changes)
python main.py --max-tickets 5 --dry-run
```

### Trigger via Web API
```bash
# Using curl
curl -X POST http://31.97.231.244:5000/trigger

# With authentication (if SECRET_TOKEN is set)
curl -X POST http://31.97.231.244:5000/trigger \
  -H "X-Secret-Token: your-secret-token"
```

---

## 📊 Monitoring & Logs

### View Real-Time Logs
```bash
# Scheduler logs
tail -f /var/log/jira-automation-scheduler.out.log

# Flask app logs
tail -f /var/log/jira-automation-flask.out.log

# Error logs
tail -f /var/log/jira-automation-scheduler.err.log
tail -f /var/log/jira-automation-flask.err.log
```

### View Last 50 Lines
```bash
tail -50 /var/log/jira-automation-scheduler.out.log
```

### Search Logs for Specific Ticket
```bash
grep "ITSD-12345" /var/log/jira-automation-scheduler.out.log
```

---

## 🔄 Update Application

### Pull Latest Code from GitHub
```bash
ssh root@31.97.231.244
cd /home/jirabot/jira-automation
sudo -u jirabot git pull origin master
supervisorctl restart all
```

### Update Dependencies
```bash
cd /home/jirabot/jira-automation/jira-automation
sudo -u jirabot venv/bin/pip install -r requirements.txt --upgrade
supervisorctl restart all
```

---

## ⚙️ Configuration Changes

### Update Environment Variables
```bash
ssh root@31.97.231.244
nano /home/jirabot/jira-automation/jira-automation/.env
```

**After editing .env, restart services:**
```bash
supervisorctl restart all
```

### Update Team Configuration
```bash
nano /home/jirabot/jira-automation/jira-automation/config/team.json
supervisorctl restart all
```

---

## 🐛 Troubleshooting

### Services Not Running
```bash
# Check detailed error
supervisorctl tail jira-automation-scheduler stderr
supervisorctl tail jira-automation-flask stderr

# Restart supervisor
systemctl restart supervisor
supervisorctl reread
supervisorctl update
supervisorctl start all
```

### Check Service Health
```bash
# Via web
curl http://31.97.231.244:5000/health

# Check connections
curl http://31.97.231.244:5000/status
```

### Clear Logs (If Too Large)
```bash
# Backup first
cp /var/log/jira-automation-scheduler.out.log /var/log/jira-automation-scheduler.out.log.backup

# Clear
> /var/log/jira-automation-scheduler.out.log
> /var/log/jira-automation-flask.out.log
```

---

## 🎯 Common Operations

### Pause Automation Temporarily
```bash
# Stop scheduler, keep Flask running for Slack buttons
supervisorctl stop jira-automation-scheduler
```

### Resume Automation
```bash
supervisorctl start jira-automation-scheduler
```

### Process Tickets Immediately
```bash
# Trigger via web (doesn't wait for hourly schedule)
curl -X POST http://31.97.231.244:5000/trigger
```

### Check Team Workload
```bash
curl http://31.97.231.244:5000/status
```

---

## 📱 Slack Integration

### Update Slack Interactive URL
1. Go to https://api.slack.com/apps
2. Select your app
3. Click "Interactivity & Shortcuts"
4. Set Request URL: `http://31.97.231.244:5000/slack/interactive`
5. Save Changes

### Test Slack Integration
- Send a test ticket notification
- Click "Get Deep Analysis" button
- Check Flask logs: `tail -f /var/log/jira-automation-flask.out.log`

---

## 🔐 Security Notes

### Change Webhook Secret (Optional)
```bash
# Edit .env
nano /home/jirabot/jira-automation/jira-automation/.env

# Add or update
WEBHOOK_SECRET=your-secure-random-token-here

# Restart
supervisorctl restart all
```

### Firewall Status
```bash
ufw status
```

**Open Ports:**
- 22 (SSH)
- 5000 (Flask App)

---

## 📞 Emergency Commands

### Stop Everything
```bash
supervisorctl stop all
```

### Restart Everything
```bash
supervisorctl restart all
systemctl restart supervisor
```

### Check System Resources
```bash
# CPU and Memory
top

# Disk space
df -h

# Process list
ps aux | grep python
```

---

## 📝 Notes

- **Scheduler runs every hour** - processes up to 10 tickets
- **Flask app** handles Slack interactive buttons
- **Logs rotate automatically** - old logs are archived
- **Services auto-restart** on failure (managed by Supervisor)
- **GitHub repo** is your source of truth for code

---

**Last Updated**: 2026-06-12  
**System Status**: ✅ Operational

---

*This guide is for operational reference. Keep it updated as you make changes to the system.*