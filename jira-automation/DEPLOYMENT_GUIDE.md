# Deployment Guide - JIRA Automation System

This guide explains how to deploy and run the JIRA automation system seamlessly in various environments.

## 🎯 Deployment Options

### Option 1: Scheduled Cron Job (Linux/Mac) ⭐ Recommended

Run the automation on a schedule using cron on any Linux/Mac server.

#### Setup:

1. **Deploy to Server:**
```bash
# SSH to your server
ssh user@your-server.com

# Clone/copy the project
git clone <your-repo> /opt/jira-automation
cd /opt/jira-automation/jira-automation

# Install dependencies
pip3 install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your credentials
```

2. **Create Wrapper Script:**
```bash
# Create run script
cat > /opt/jira-automation/run.sh << 'EOF'
#!/bin/bash
cd /opt/jira-automation/jira-automation
/usr/bin/python3 main.py >> /var/log/jira-automation.log 2>&1
EOF

chmod +x /opt/jira-automation/run.sh
```

3. **Setup Cron Job:**
```bash
# Edit crontab
crontab -e

# Add one of these schedules:

# Every 15 minutes
*/15 * * * * /opt/jira-automation/run.sh

# Every hour at minute 0
0 * * * * /opt/jira-automation/run.sh

# Every 4 hours
0 */4 * * * /opt/jira-automation/run.sh

# Business hours only (9 AM - 5 PM, Mon-Fri)
0 9-17 * * 1-5 /opt/jira-automation/run.sh

# Once daily at 9 AM
0 9 * * * /opt/jira-automation/run.sh
```

**Pros:**
- ✅ Simple and reliable
- ✅ No additional infrastructure
- ✅ Easy to monitor logs
- ✅ Low resource usage

**Cons:**
- ❌ Requires a server
- ❌ Manual scheduling

---

### Option 2: Windows Task Scheduler

Run on Windows Server or desktop.

#### Setup:

1. **Install Python and Dependencies:**
```powershell
# Install Python 3.9+
# Download from python.org

# Install dependencies
cd C:\jira-automation\jira-automation
pip install -r requirements.txt

# Configure .env
copy .env.example .env
notepad .env
```

2. **Create Batch Script:**
```batch
@echo off
cd C:\jira-automation\jira-automation
python main.py >> C:\jira-automation\logs\automation.log 2>&1
```

Save as `C:\jira-automation\run.bat`

3. **Setup Task Scheduler:**
- Open Task Scheduler
- Create Basic Task
- Name: "JIRA Automation"
- Trigger: Choose schedule (e.g., every 15 minutes)
- Action: Start a program
- Program: `C:\jira-automation\run.bat`
- Finish

**Pros:**
- ✅ Native Windows solution
- ✅ GUI configuration
- ✅ Reliable scheduling

**Cons:**
- ❌ Windows-specific
- ❌ Requires Windows Server

---

### Option 3: Docker Container 🐳

Run in a containerized environment.

#### Setup:

1. **Create Dockerfile:**
```dockerfile
# jira-automation/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run the application
CMD ["python", "main.py"]
```

2. **Create docker-compose.yml:**
```yaml
version: '3.8'

services:
  jira-automation:
    build: .
    container_name: jira-automation
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config
    restart: unless-stopped
    # Run every hour using cron in container
    command: >
      sh -c "
        while true; do
          python main.py
          sleep 3600
        done
      "
```

3. **Deploy:**
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Pros:**
- ✅ Portable and consistent
- ✅ Easy to deploy anywhere
- ✅ Isolated environment

**Cons:**
- ❌ Requires Docker knowledge
- ❌ Additional overhead

---

### Option 4: AWS Lambda (Serverless) ☁️

Run as a serverless function on AWS.

#### Setup:

1. **Create Lambda Handler:**
```python
# lambda_handler.py
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from main import TicketOrchestrator
from config import get_settings

def lambda_handler(event, context):
    """AWS Lambda handler."""
    try:
        settings = get_settings()
        orchestrator = TicketOrchestrator(settings)
        
        # Run with max tickets limit for Lambda
        stats = orchestrator.run(max_tickets=10)
        
        return {
            'statusCode': 200,
            'body': {
                'message': 'Success',
                'stats': stats
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': {
                'message': 'Error',
                'error': str(e)
            }
        }
```

2. **Package for Lambda:**
```bash
# Install dependencies in a directory
pip install -r requirements.txt -t package/

# Copy application files
cp -r jira-automation/* package/

# Create deployment package
cd package
zip -r ../lambda-deployment.zip .
```

3. **Deploy to AWS:**
- Create Lambda function in AWS Console
- Upload lambda-deployment.zip
- Set environment variables from .env
- Configure EventBridge (CloudWatch Events) trigger
- Set schedule: `rate(15 minutes)` or `cron(0 * * * ? *)`

**Pros:**
- ✅ Serverless (no server management)
- ✅ Auto-scaling
- ✅ Pay per execution
- ✅ Highly available

**Cons:**
- ❌ AWS-specific
- ❌ 15-minute execution limit
- ❌ Cold start delays

---

### Option 5: Azure Functions

Similar to AWS Lambda but on Azure.

#### Setup:

1. **Create function_app.py:**
```python
import azure.functions as func
from main import TicketOrchestrator
from config import get_settings

app = func.FunctionApp()

@app.schedule(schedule="0 */15 * * * *", 
              arg_name="timer", 
              run_on_startup=False)
def jira_automation(timer: func.TimerRequest) -> None:
    """Azure Function triggered by timer."""
    settings = get_settings()
    orchestrator = TicketOrchestrator(settings)
    stats = orchestrator.run(max_tickets=10)
    print(f"Processed {stats['tickets_assigned']} tickets")
```

2. **Deploy:**
```bash
# Install Azure Functions Core Tools
# Then deploy
func azure functionapp publish <your-function-app-name>
```

**Pros:**
- ✅ Serverless
- ✅ Azure integration
- ✅ Auto-scaling

**Cons:**
- ❌ Azure-specific
- ❌ Requires Azure account

---

### Option 6: Kubernetes CronJob

For enterprise Kubernetes environments.

#### Setup:

1. **Create ConfigMap for .env:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: jira-automation-config
data:
  .env: |
    JIRA_URL=https://your-jira.com
    # ... other config
```

2. **Create CronJob:**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: jira-automation
spec:
  schedule: "*/15 * * * *"  # Every 15 minutes
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: jira-automation
            image: your-registry/jira-automation:latest
            envFrom:
            - configMapRef:
                name: jira-automation-config
          restartPolicy: OnFailure
```

3. **Deploy:**
```bash
kubectl apply -f cronjob.yaml
```

**Pros:**
- ✅ Enterprise-grade
- ✅ Scalable
- ✅ Integrated monitoring

**Cons:**
- ❌ Requires Kubernetes
- ❌ Complex setup

---

### Option 7: GitHub Actions (CI/CD)

Run as a scheduled GitHub Action.

#### Setup:

1. **Create .github/workflows/automation.yml:**
```yaml
name: JIRA Automation

on:
  schedule:
    # Run every 15 minutes
    - cron: '*/15 * * * *'
  workflow_dispatch:  # Manual trigger

jobs:
  automate:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd jira-automation
        pip install -r requirements.txt
    
    - name: Run automation
      env:
        JIRA_URL: ${{ secrets.JIRA_URL }}
        JIRA_PAT_TOKEN: ${{ secrets.JIRA_PAT_TOKEN }}
        JIRA_PROJECT_KEY: ${{ secrets.JIRA_PROJECT_KEY }}
        JIRA_QUEUE_JQL: ${{ secrets.JIRA_QUEUE_JQL }}
        MISTRAL_API_KEY: ${{ secrets.MISTRAL_API_KEY }}
        SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
        SLACK_CHANNEL_ID: ${{ secrets.SLACK_CHANNEL_ID }}
      run: |
        cd jira-automation
        python main.py
```

2. **Add Secrets:**
- Go to GitHub repo → Settings → Secrets
- Add all environment variables as secrets

**Pros:**
- ✅ Free for public repos
- ✅ No server needed
- ✅ Version controlled

**Cons:**
- ❌ GitHub-dependent
- ❌ Limited to 5-minute minimum schedule
- ❌ Usage limits on free tier

---

## 🎯 Recommended Setup by Use Case

### Small Team (< 50 tickets/day)
**Recommendation:** Cron Job on Linux Server
- Simple, reliable, low cost
- Easy to maintain
- Full control

### Medium Team (50-200 tickets/day)
**Recommendation:** Docker Container
- Portable and scalable
- Easy to deploy
- Good monitoring

### Large Enterprise
**Recommendation:** Kubernetes CronJob
- Enterprise-grade
- Highly available
- Integrated with existing infrastructure

### Serverless/Cloud-First
**Recommendation:** AWS Lambda or Azure Functions
- No server management
- Auto-scaling
- Pay per use

### Budget-Conscious
**Recommendation:** GitHub Actions
- Free for public repos
- No infrastructure costs
- Easy setup

---

## 📊 Monitoring & Maintenance

### Log Monitoring

**View Logs:**
```bash
# Cron job
tail -f /var/log/jira-automation.log

# Docker
docker-compose logs -f

# Kubernetes
kubectl logs -f cronjob/jira-automation
```

**Log Rotation:**
```bash
# Create logrotate config
cat > /etc/logrotate.d/jira-automation << EOF
/var/log/jira-automation.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
EOF
```

### Health Checks

**Create Health Check Script:**
```bash
#!/bin/bash
# health-check.sh

cd /opt/jira-automation/jira-automation
python main.py --test-connections

if [ $? -eq 0 ]; then
    echo "✓ Health check passed"
    exit 0
else
    echo "✗ Health check failed"
    # Send alert (email, Slack, etc.)
    exit 1
fi
```

### Alerting

**Setup Alerts:**
- Monitor log files for errors
- Check execution frequency
- Track assignment success rate
- Alert on connection failures

---

## 🔧 Configuration Tips

### Environment Variables

**Production .env:**
```env
# JIRA
JIRA_URL=https://your-jira.com
JIRA_PAT_TOKEN=<secure-token>
JIRA_PROJECT_KEY=PROJ
JIRA_QUEUE_JQL=project = PROJ AND assignee is EMPTY AND status = "To Do"

# AI
MISTRAL_API_KEY=<secure-key>

# Slack
SLACK_BOT_TOKEN=xoxb-<secure-token>
SLACK_CHANNEL_ID=C1234567890

# Logging
LOG_LEVEL=INFO
```

### Security Best Practices

1. **Never commit .env to git**
2. **Use secrets management** (AWS Secrets Manager, Azure Key Vault)
3. **Rotate tokens regularly**
4. **Use least-privilege access**
5. **Monitor for unauthorized access**

---

## 🚀 Quick Start Deployment

### Fastest Setup (Cron Job):

```bash
# 1. SSH to server
ssh user@server

# 2. Clone and setup
git clone <repo> /opt/jira-automation
cd /opt/jira-automation/jira-automation
pip3 install -r requirements.txt
cp .env.example .env
nano .env  # Add credentials

# 3. Test
python3 main.py --test-connections
python3 main.py --dry-run --max-tickets 1

# 4. Schedule
echo "*/15 * * * * cd /opt/jira-automation/jira-automation && python3 main.py" | crontab -

# Done! Running every 15 minutes
```

---

## 📞 Support

For deployment issues:
1. Check logs first
2. Test connections: `python main.py --test-connections`
3. Run dry-run: `python main.py --dry-run`
4. Review this guide
5. Contact your DevOps team

---

**Choose the deployment option that best fits your infrastructure and team size!**