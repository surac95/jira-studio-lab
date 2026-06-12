# Cloud Cron Service Deployment Guide

This guide explains how to deploy the JIRA automation system to cloud-based cron services like **cron-job.org**, **EasyCron**, or similar platforms.

## 🌐 Cloud Cron Services Overview

Cloud cron services allow you to schedule HTTP requests or run scripts without managing your own server.

### Popular Services:
- **cron-job.org** - Free tier available
- **EasyCron** - Free and paid plans
- **Cronitor** - Monitoring + scheduling
- **AWS EventBridge** - AWS native
- **Google Cloud Scheduler** - GCP native

## 🎯 Deployment Strategy

Since cloud cron services typically trigger HTTP endpoints, we need to:
1. Host the application somewhere accessible
2. Create an HTTP endpoint
3. Configure the cron service to call it

## 📦 Option 1: Deploy to Free Hosting + Cloud Cron

### Step 1: Deploy Application to PythonAnywhere (Free Tier)

**PythonAnywhere** offers free Python hosting perfect for this use case.

#### A. Sign up for PythonAnywhere
1. Go to https://www.pythonanywhere.com
2. Create free account
3. You get a subdomain: `yourusername.pythonanywhere.com`

#### B. Upload Your Code
```bash
# On PythonAnywhere Bash console
cd ~
git clone <your-repo-url> jira-automation
cd jira-automation/jira-automation

# Install dependencies
pip3 install --user -r requirements.txt
```

#### C. Configure Environment
```bash
# Create .env file
nano .env

# Add your credentials:
JIRA_URL=https://your-jira.com
JIRA_PAT_TOKEN=your_token
JIRA_PROJECT_KEY=PROJ
JIRA_QUEUE_JQL=project = PROJ AND assignee is EMPTY
MISTRAL_API_KEY=your_key
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_CHANNEL_ID=C1234567890
LOG_LEVEL=INFO
```

#### D. Create Web Endpoint
Create `flask_app.py` in your PythonAnywhere directory:

```python
"""
Flask web endpoint for triggering JIRA automation.
Deploy this to PythonAnywhere or similar hosting.
"""

from flask import Flask, jsonify, request
import sys
import os
from pathlib import Path

# Add jira-automation to path
sys.path.insert(0, str(Path(__file__).parent / 'jira-automation'))

from main import TicketOrchestrator
from config import get_settings

app = Flask(__name__)

# Security: Add a secret token
SECRET_TOKEN = os.getenv('WEBHOOK_SECRET', 'change-this-secret-token')

@app.route('/')
def home():
    """Home page."""
    return jsonify({
        'service': 'JIRA Automation',
        'status': 'running',
        'message': 'Use POST /trigger to run automation'
    })

@app.route('/trigger', methods=['POST'])
def trigger_automation():
    """Trigger the automation workflow."""
    
    # Verify secret token
    token = request.headers.get('X-Secret-Token')
    if token != SECRET_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get parameters
        dry_run = request.json.get('dry_run', False) if request.json else False
        max_tickets = request.json.get('max_tickets', None) if request.json else None
        
        # Run automation
        settings = get_settings()
        orchestrator = TicketOrchestrator(settings)
        stats = orchestrator.run(dry_run=dry_run, max_tickets=max_tickets)
        
        return jsonify({
            'status': 'success',
            'stats': {
                'tickets_fetched': stats['tickets_fetched'],
                'tickets_analyzed': stats['tickets_analyzed'],
                'tickets_assigned': stats['tickets_assigned'],
                'tickets_failed': stats['tickets_failed'],
                'execution_time': stats.get('execution_time', 0)
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        settings = get_settings()
        orchestrator = TicketOrchestrator(settings)
        connections = orchestrator.test_connections()
        
        return jsonify({
            'status': 'healthy',
            'connections': connections
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/status', methods=['GET'])
def team_status():
    """Get team status."""
    try:
        settings = get_settings()
        orchestrator = TicketOrchestrator(settings)
        status = orchestrator.get_team_status()
        
        return jsonify({
            'status': 'success',
            'team_status': status
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=False)
```

#### E. Configure PythonAnywhere Web App
1. Go to "Web" tab in PythonAnywhere
2. Click "Add a new web app"
3. Choose Flask
4. Set source code directory: `/home/yourusername/jira-automation`
5. Set WSGI file to point to `flask_app.py`
6. Reload web app

Your endpoint will be: `https://yourusername.pythonanywhere.com/trigger`

### Step 2: Configure Cloud Cron Service

#### For cron-job.org:

1. **Login to cron-job.org**
2. **Create New Cron Job:**
   - Title: "JIRA Automation"
   - URL: `https://yourusername.pythonanywhere.com/trigger`
   - Schedule: Every 15 minutes (or your preference)
   - Request Method: POST
   - Headers: Add `X-Secret-Token: your-secret-token`
   - Request Body (JSON):
     ```json
     {
       "dry_run": false,
       "max_tickets": 50
     }
     ```

3. **Save and Enable**

#### For EasyCron:

1. **Login to EasyCron**
2. **Add Cron Job:**
   - URL: `https://yourusername.pythonanywhere.com/trigger`
   - Cron Expression: `*/15 * * * *` (every 15 minutes)
   - HTTP Method: POST
   - HTTP Headers: `X-Secret-Token: your-secret-token`
   - POST Data:
     ```json
     {"dry_run": false, "max_tickets": 50}
     ```

3. **Test and Enable**

## 📦 Option 2: Deploy to Heroku + Cloud Cron

### Step 1: Deploy to Heroku

#### A. Prepare Application

Create `Procfile`:
```
web: gunicorn flask_app:app
```

Create `runtime.txt`:
```
python-3.11.0
```

Update `requirements.txt` to include:
```
gunicorn==21.2.0
flask==3.0.0
```

#### B. Deploy to Heroku
```bash
# Install Heroku CLI
# Then:

heroku login
heroku create your-app-name
git push heroku main

# Set environment variables
heroku config:set JIRA_URL=https://your-jira.com
heroku config:set JIRA_PAT_TOKEN=your_token
heroku config:set MISTRAL_API_KEY=your_key
heroku config:set SLACK_BOT_TOKEN=xoxb-your-token
heroku config:set SLACK_CHANNEL_ID=C1234567890
heroku config:set WEBHOOK_SECRET=your-secret-token

# Your app will be at: https://your-app-name.herokuapp.com
```

### Step 2: Configure Cloud Cron
Same as Option 1, but use your Heroku URL:
`https://your-app-name.herokuapp.com/trigger`

## 📦 Option 3: Deploy to Render.com + Cloud Cron

### Step 1: Deploy to Render

1. **Sign up at render.com**
2. **Create New Web Service**
3. **Connect your Git repository**
4. **Configure:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn flask_app:app`
   - Add environment variables

Your endpoint: `https://your-service.onrender.com/trigger`

### Step 2: Configure Cloud Cron
Use your Render URL with the cron service.

## 🔐 Security Best Practices

### 1. Use Secret Token
Always protect your endpoint with a secret token:

```python
SECRET_TOKEN = os.getenv('WEBHOOK_SECRET', 'generate-random-token-here')
```

Generate a secure token:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. IP Whitelisting (if supported)
Some hosting platforms allow IP whitelisting. Add your cron service's IPs.

### 3. Rate Limiting
Add rate limiting to prevent abuse:

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.headers.get('X-Secret-Token'))

@app.route('/trigger', methods=['POST'])
@limiter.limit("10 per hour")
def trigger_automation():
    # ... your code
```

## 📊 Monitoring

### Check Execution Logs

**PythonAnywhere:**
- Go to "Web" tab
- Click "Log files"
- View error.log and server.log

**Heroku:**
```bash
heroku logs --tail
```

**Render:**
- Go to your service dashboard
- Click "Logs"

### Monitor Cron Executions

**cron-job.org:**
- View execution history in dashboard
- Check success/failure rates
- Review response times

**Set up Alerts:**
- Configure email notifications for failures
- Use Slack webhooks for alerts
- Monitor response times

## 🧪 Testing Your Deployment

### 1. Test Health Endpoint
```bash
curl https://yourusername.pythonanywhere.com/health
```

### 2. Test Trigger (Dry Run)
```bash
curl -X POST https://yourusername.pythonanywhere.com/trigger \
  -H "Content-Type: application/json" \
  -H "X-Secret-Token: your-secret-token" \
  -d '{"dry_run": true, "max_tickets": 1}'
```

### 3. Check Team Status
```bash
curl https://yourusername.pythonanywhere.com/status
```

## 💰 Cost Comparison

| Service | Free Tier | Paid Plans |
|---------|-----------|------------|
| PythonAnywhere | ✅ Yes (limited) | $5/month |
| Heroku | ❌ No (was free) | $7/month |
| Render | ✅ Yes | $7/month |
| cron-job.org | ✅ Yes | $4.99/month |
| EasyCron | ✅ Yes (limited) | $3/month |

**Recommended Combo:**
- **PythonAnywhere Free** + **cron-job.org Free** = $0/month
- Perfect for small teams!

## 🚀 Quick Start (PythonAnywhere + cron-job.org)

```bash
# 1. Sign up for both services (free)
# - PythonAnywhere: https://www.pythonanywhere.com
# - cron-job.org: https://cron-job.org

# 2. On PythonAnywhere console:
git clone <your-repo> jira-automation
cd jira-automation/jira-automation
pip3 install --user -r requirements.txt
nano .env  # Add credentials

# 3. Create flask_app.py (copy from above)

# 4. Configure PythonAnywhere web app

# 5. On cron-job.org:
# - Create job pointing to your PythonAnywhere URL
# - Set schedule: */15 * * * * (every 15 minutes)
# - Add secret token header

# Done! ✅
```

## 📞 Troubleshooting

### Issue: "Module not found"
**Solution:** Ensure all dependencies are installed:
```bash
pip3 install --user -r requirements.txt
```

### Issue: "Unauthorized" error
**Solution:** Check your secret token matches in both places:
- Environment variable: `WEBHOOK_SECRET`
- Cron job header: `X-Secret-Token`

### Issue: Timeout errors
**Solution:** 
- Reduce `max_tickets` parameter
- Increase timeout in cron service settings
- Check hosting platform limits

### Issue: "Configuration validation failed"
**Solution:** Verify all environment variables are set correctly in your hosting platform.

## 🎯 Recommended Setup

**For Your Use Case (cron-job.org account):**

1. ✅ **Deploy to PythonAnywhere** (Free tier)
2. ✅ **Use cron-job.org** (Your existing account)
3. ✅ **Schedule every 15 minutes**
4. ✅ **Monitor via dashboards**

This gives you a completely free, reliable solution!

---

**Need help? Check the logs and test endpoints individually!**