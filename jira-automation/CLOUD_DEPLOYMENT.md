# Cloud Deployment Guide - Free Tier Options

This guide covers deploying the JIRA automation system to free cloud platforms for 24/7 operation.

## Table of Contents
1. [PythonAnywhere (Recommended for Beginners)](#pythonanywhere)
2. [Heroku (Best for Scalability)](#heroku)
3. [Railway (Modern & Easy)](#railway)
4. [Render (Simple & Reliable)](#render)
5. [GitHub Actions (Scheduled Runs)](#github-actions)

---

## Option 1: PythonAnywhere (Recommended) ⭐

**Best for**: Beginners, scheduled tasks, simple deployment
**Free Tier**: 1 web app, 1 scheduled task, 512MB storage

### Step 1: Sign Up
1. Go to https://www.pythonanywhere.com
2. Create a free account
3. Verify your email

### Step 2: Upload Code
```bash
# On PythonAnywhere Bash console
git clone https://github.com/YOUR_USERNAME/jira-automation.git
cd jira-automation
```

### Step 3: Install Dependencies
```bash
# Create virtual environment
mkvirtualenv --python=/usr/bin/python3.10 jira-env

# Install packages
pip install -r requirements.txt
```

### Step 4: Configure Environment
```bash
# Create .env file
nano .env

# Add your credentials (paste from local .env)
# Save: Ctrl+O, Enter, Ctrl+X
```

### Step 5: Set Up Scheduled Task
1. Go to **Tasks** tab
2. Click **Create a new scheduled task**
3. Set schedule: `Daily at 09:00 UTC` (or your preferred time)
4. Command: `/home/YOUR_USERNAME/.virtualenvs/jira-env/bin/python /home/YOUR_USERNAME/jira-automation/main.py --max-tickets 10`
5. Click **Create**

### Step 6: Set Up Flask App (for Slack buttons)
1. Go to **Web** tab
2. Click **Add a new web app**
3. Choose **Flask**
4. Python version: **3.10**
5. Path: `/home/YOUR_USERNAME/jira-automation/flask_app.py`
6. Edit WSGI file:
```python
import sys
path = '/home/YOUR_USERNAME/jira-automation'
if path not in sys.path:
    sys.path.append(path)

from flask_app import app as application
```
7. Click **Reload** to start the app

### Step 7: Configure Slack Interactive URL
1. Your Flask app URL: `https://YOUR_USERNAME.pythonanywhere.com/slack/interactive`
2. Add this to Slack App settings (see SLACK_INTERACTIVE_SETUP.md)

**Pros:**
- ✅ Very easy to set up
- ✅ Free scheduled tasks
- ✅ Persistent storage
- ✅ Good for learning

**Cons:**
- ❌ Limited to 1 scheduled task on free tier
- ❌ CPU time limits (100 seconds/day)
- ❌ No always-on web apps on free tier

---

## Option 2: Heroku (Best for Production)

**Best for**: Production apps, always-on services
**Free Tier**: 550-1000 dyno hours/month (with credit card verification)

### Step 1: Install Heroku CLI
```bash
# Windows (PowerShell as Admin)
winget install Heroku.HerokuCLI

# Mac
brew tap heroku/brew && brew install heroku

# Linux
curl https://cli-assets.heroku.com/install.sh | sh
```

### Step 2: Login and Create App
```bash
heroku login
cd jira-automation
heroku create jira-automation-YOUR_NAME
```

### Step 3: Add Buildpack
```bash
heroku buildpacks:set heroku/python
```

### Step 4: Create Procfile
```bash
# Create Procfile in jira-automation directory
echo "web: python flask_app.py" > Procfile
echo "worker: python scheduler.py" >> Procfile
```

### Step 5: Create scheduler.py
```python
"""Scheduler for running automation periodically."""
import schedule
import time
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_automation():
    """Run the JIRA automation."""
    logger.info("Starting scheduled automation run...")
    try:
        result = subprocess.run(
            ["python", "main.py", "--max-tickets", "10"],
            capture_output=True,
            text=True
        )
        logger.info(f"Automation completed: {result.stdout}")
        if result.returncode != 0:
            logger.error(f"Automation failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error running automation: {e}")

# Schedule to run every hour
schedule.every().hour.do(run_automation)

# Run immediately on start
run_automation()

# Keep running
logger.info("Scheduler started. Running every hour...")
while True:
    schedule.run_pending()
    time.sleep(60)
```

### Step 6: Update requirements.txt
```bash
echo "schedule==1.2.0" >> requirements.txt
```

### Step 7: Set Environment Variables
```bash
heroku config:set JIRA_URL="your_jira_url"
heroku config:set JIRA_PAT_TOKEN="your_token"
heroku config:set MISTRAL_API_KEY="your_key"
heroku config:set SLACK_BOT_TOKEN="your_token"
heroku config:set SLACK_CHANNEL_ID="your_channel"
# ... add all other env vars
```

### Step 8: Deploy
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### Step 9: Scale Dynos
```bash
# Start web dyno (for Flask app)
heroku ps:scale web=1

# Start worker dyno (for scheduled automation)
heroku ps:scale worker=1
```

### Step 10: View Logs
```bash
heroku logs --tail
```

**Pros:**
- ✅ Always-on web apps
- ✅ Easy deployment with Git
- ✅ Good free tier
- ✅ Professional-grade platform

**Cons:**
- ❌ Requires credit card for verification
- ❌ Dyno sleeps after 30 min inactivity (free tier)
- ❌ Limited to 550 hours/month without card, 1000 with card

---

## Option 3: Railway (Modern & Easy) 🚂

**Best for**: Modern deployment, generous free tier
**Free Tier**: $5 credit/month, no credit card required

### Step 1: Sign Up
1. Go to https://railway.app
2. Sign up with GitHub
3. Connect your repository

### Step 2: Create New Project
1. Click **New Project**
2. Select **Deploy from GitHub repo**
3. Choose your jira-automation repository

### Step 3: Add Environment Variables
1. Go to **Variables** tab
2. Add all environment variables from your .env file
3. Click **Add Variable** for each one

### Step 4: Configure Start Command
1. Go to **Settings** tab
2. Set **Start Command**: `python main.py --max-tickets 10`
3. For Flask app, create separate service with: `python flask_app.py`

### Step 5: Add Cron Job
Create `railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python scheduler.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 6: Deploy
Railway auto-deploys on git push!

**Pros:**
- ✅ Very modern and easy
- ✅ Generous free tier ($5/month)
- ✅ No credit card required
- ✅ Auto-deploys from GitHub

**Cons:**
- ❌ Limited free credits
- ❌ May need to upgrade for 24/7 operation

---

## Option 4: Render (Simple & Reliable)

**Best for**: Simple deployment, cron jobs
**Free Tier**: 750 hours/month, cron jobs

### Step 1: Sign Up
1. Go to https://render.com
2. Sign up with GitHub

### Step 2: Create Web Service (Flask App)
1. Click **New +** → **Web Service**
2. Connect your GitHub repository
3. Settings:
   - **Name**: jira-automation-flask
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python flask_app.py`
   - **Plan**: Free

### Step 3: Create Cron Job (Automation)
1. Click **New +** → **Cron Job**
2. Settings:
   - **Name**: jira-automation-cron
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Command**: `python main.py --max-tickets 10`
   - **Schedule**: `0 */1 * * *` (every hour)
   - **Plan**: Free

### Step 4: Add Environment Variables
1. Go to **Environment** tab for each service
2. Add all variables from .env file

**Pros:**
- ✅ Free cron jobs
- ✅ Easy to use
- ✅ Reliable platform
- ✅ Good documentation

**Cons:**
- ❌ Free tier services spin down after inactivity
- ❌ Limited to 750 hours/month

---

## Option 5: GitHub Actions (Scheduled Runs)

**Best for**: Scheduled automation without web app
**Free Tier**: 2000 minutes/month

### Step 1: Create Workflow File
Create `.github/workflows/jira-automation.yml`:

```yaml
name: JIRA Automation

on:
  schedule:
    # Run every hour
    - cron: '0 * * * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  automate:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run automation
      env:
        JIRA_URL: ${{ secrets.JIRA_URL }}
        JIRA_PAT_TOKEN: ${{ secrets.JIRA_PAT_TOKEN }}
        MISTRAL_API_KEY: ${{ secrets.MISTRAL_API_KEY }}
        SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
        SLACK_CHANNEL_ID: ${{ secrets.SLACK_CHANNEL_ID }}
        JIRA_PROJECT_KEY: ${{ secrets.JIRA_PROJECT_KEY }}
        JIRA_QUEUE_JQL: ${{ secrets.JIRA_QUEUE_JQL }}
        LOG_LEVEL: INFO
      run: |
        python main.py --max-tickets 10
```

### Step 2: Add Secrets
1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add all environment variables as secrets

### Step 3: Enable Workflows
1. Go to **Actions** tab
2. Enable workflows if disabled
3. Workflow will run automatically on schedule

### Step 4: Manual Trigger
1. Go to **Actions** tab
2. Select **JIRA Automation** workflow
3. Click **Run workflow** to test

**Pros:**
- ✅ Completely free
- ✅ No server management
- ✅ Integrated with GitHub
- ✅ Easy to set up

**Cons:**
- ❌ No web app hosting (can't host Flask for Slack buttons)
- ❌ Limited to scheduled runs
- ❌ 2000 minutes/month limit

---

## Recommended Setup for Complete Solution

### For Full Features (Flask + Automation):
**Option 1: Heroku** (web + worker dynos)
- Web dyno: Flask app for Slack buttons
- Worker dyno: Scheduled automation
- Cost: Free with credit card verification

**Option 2: Railway** (2 services)
- Service 1: Flask app (always-on)
- Service 2: Scheduler (cron-like)
- Cost: ~$3-4/month from $5 credit

### For Automation Only (No Slack Buttons):
**Option 1: GitHub Actions**
- Completely free
- Runs on schedule
- No server management

**Option 2: Render Cron Job**
- Free tier
- Easy setup
- Reliable

---

## Cost Comparison

| Platform | Free Tier | Best For | Limitations |
|----------|-----------|----------|-------------|
| **PythonAnywhere** | 1 scheduled task | Learning, simple tasks | CPU limits, 1 task only |
| **Heroku** | 550-1000 hrs/mo | Production apps | Requires credit card |
| **Railway** | $5 credit/mo | Modern deployment | Limited credits |
| **Render** | 750 hrs/mo | Cron jobs | Services spin down |
| **GitHub Actions** | 2000 min/mo | Scheduled automation | No web hosting |

---

## Next Steps

1. **Choose a platform** based on your needs
2. **Follow the deployment guide** for that platform
3. **Test the deployment** with a manual run
4. **Monitor logs** to ensure everything works
5. **Set up alerts** for failures (optional)

## Monitoring & Maintenance

### Check Logs Regularly
```bash
# Heroku
heroku logs --tail

# Railway
railway logs

# Render
# View logs in dashboard

# GitHub Actions
# View in Actions tab
```

### Set Up Alerts
- Configure Slack notifications for errors
- Use platform's built-in monitoring
- Set up email alerts for failures

### Update Deployment
```bash
# Push changes
git add .
git commit -m "Update automation"
git push origin main

# Most platforms auto-deploy from GitHub
```

---

## Troubleshooting

### Common Issues

**1. Environment Variables Not Set**
- Double-check all variables are added
- Restart the service after adding variables

**2. Dependencies Not Installing**
- Ensure requirements.txt is up to date
- Check Python version compatibility

**3. Scheduled Tasks Not Running**
- Verify cron syntax
- Check platform-specific scheduling format
- Review logs for errors

**4. Flask App Not Accessible**
- Ensure correct port binding (use `0.0.0.0`)
- Check firewall/security settings
- Verify URL in Slack app settings

### Getting Help

- Check platform documentation
- Review application logs
- Test locally first
- Ask in platform community forums

---

## Security Best Practices

1. **Never commit .env file** - Use .gitignore
2. **Use environment variables** for all secrets
3. **Rotate tokens regularly** - Update in platform settings
4. **Enable 2FA** on all platforms
5. **Monitor access logs** for suspicious activity
6. **Use least privilege** - Only grant necessary permissions

---

Made with ❤️ for seamless JIRA automation