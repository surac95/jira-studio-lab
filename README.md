# JIRA Incident Ticket Automation System

An AI-powered automation system that monitors JIRA L3/L4 support queues, classifies incidents using Mistral AI, assigns tickets based on team workload, and notifies the team via Slack with interactive features.

## 🎯 Features

- **Automated Ticket Monitoring**: Continuously monitors JIRA queues for unassigned incidents
- **AI-Powered Classification**: Uses Mistral AI to classify tickets into TRIRIGA, APIC, or APPC categories
- **Deep Technical Analysis**: On-demand AI analysis with root cause, solutions, and impact assessment
- **Intelligent Assignment**: Assigns tickets based on team member specialization and current workload
- **AI Summarization**: Generates concise summaries of ticket content for quick understanding
- **Slack Integration**: Interactive notifications with buttons for deep analysis and re-analysis
- **Scheduled Execution**: Runs automatically every hour via Supervisor
- **Web API**: HTTP endpoints for manual triggering and health checks
- **VPS Deployment**: Production-ready deployment on Hostinger VPS

## 📋 Prerequisites

- Python 3.12 or higher
- JIRA Server access with PAT token
- Mistral AI API key (v1.0.0+)
- Slack Bot token with appropriate permissions
- VPS or cloud hosting (Hostinger, AWS, etc.)

## 🚀 Quick Start

### Option 1: VPS Deployment (Recommended)

**For production deployment on Hostinger VPS:**

See **[VPS_DEPLOYMENT_INSTRUCTIONS.md](VPS_DEPLOYMENT_INSTRUCTIONS.md)** for complete setup guide.

Quick deploy:
```bash
# On Windows
.\deploy-to-vps.ps1

# On Linux/Mac
./deploy-to-vps.sh
```

### Option 2: Local Development

```bash
# Clone the repository
git clone https://github.com/surac95/jira-studio-lab.git
cd jira-studio-lab/jira-automation

# Create virtual environment
python3.12 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install schedule==1.2.0
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# JIRA Configuration
JIRA_SERVER_URL=https://jira.issworld.com
JIRA_PAT_TOKEN=your_personal_access_token_here
JIRA_QUEUE_FILTER=L3/L4
JIRA_PROJECT_KEY=PROJ

# Mistral AI Configuration
MISTRAL_API_KEY=your_mistral_api_key_here
MISTRAL_MODEL=mistral-large-latest
MISTRAL_MAX_TOKENS=1000
MISTRAL_TEMPERATURE=0.3

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL_ID=C01234567890
SLACK_ERROR_CHANNEL_ID=C09876543210

# Team Configuration
TEAM_CONFIG_PATH=config/team.json

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/automation.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5

# Execution Configuration
DRY_RUN=false
MAX_TICKETS_PER_RUN=50
```

### 4. Configure Team Members

Create `config/team.json`:

```json
{
  "members": [
    {
      "username": "john.doe",
      "name": "John Doe",
      "email": "john.doe@company.com",
      "specializations": ["TRIRIGA", "APIC"],
      "max_tickets": 10,
      "active": true
    },
    {
      "username": "jane.smith",
      "name": "Jane Smith",
      "email": "jane.smith@company.com",
      "specializations": ["APPC"],
      "max_tickets": 8,
      "active": true
    },
    {
      "username": "bob.wilson",
      "name": "Bob Wilson",
      "email": "bob.wilson@company.com",
      "specializations": ["TRIRIGA", "APIC", "APPC"],
      "max_tickets": 12,
      "active": true
    }
  ],
  "fallback_assignee": "team.lead",
  "assignment_strategy": "workload_balanced"
}
```

### 5. Test the Configuration

Run in dry-run mode to test without making changes:

```bash
python main.py --dry-run
```

### 6. Run the System

**Automated (Scheduler):**
```bash
python scheduler.py
```

**Manual (One-time):**
```bash
python main.py --max-tickets 10
```

**Web API (Flask):**
```bash
python flask_app.py
# Access at http://localhost:5000
```

## 📁 Project Structure

```
jira-automation/
│
├── config/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   └── team.json              # Team member configuration
│
├── services/
│   ├── __init__.py
│   ├── jira_service.py        # JIRA API interactions
│   ├── mistral_service.py     # Mistral AI integration
│   ├── workload_manager.py    # Assignment logic
│   └── slack_service.py       # Slack notifications
│
├── models/
│   ├── __init__.py
│   └── ticket.py              # Data models
│
├── utils/
│   ├── __init__.py
│   ├── logger.py              # Logging configuration
│   └── validators.py          # Input validation
│
├── tests/
│   ├── __init__.py
│   ├── test_jira_service.py
│   ├── test_mistral_service.py
│   ├── test_workload_manager.py
│   └── test_slack_service.py
│
├── logs/
│   └── .gitkeep
│
├── main.py                    # Entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment variables
├── .gitignore
├── README.md                 # This file
└── ARCHITECTURE.md           # Detailed architecture documentation
```

## 🔧 Configuration Details

### JIRA Configuration

**Required Permissions for PAT Token**:
- Read tickets
- Update assignee field
- Add comments

**JQL Query Used**:
```sql
project = PROJ 
AND status IN ("Open", "New", "To Do") 
AND assignee is EMPTY 
AND (labels = "L3" OR labels = "L4")
AND created >= -1h
ORDER BY priority DESC, created ASC
```

### Mistral AI Configuration

The system uses Mistral AI for two purposes:

1. **Classification**: Categorizes tickets into TRIRIGA, APIC, or APPC
2. **Summarization**: Generates concise summaries of ticket content

**Recommended Model**: `mistral-large-latest` for best accuracy

### Slack Configuration

**Required Bot Permissions**:
- `chat:write` - Send messages to channels
- `channels:read` - Read channel information

**Notification Format**:
```
🎫 New Ticket Assigned

Ticket: [PROJ-123] Brief ticket summary
Classification: TRIRIGA
Assigned To: @john.doe
Priority: High

Summary:
AI-generated summary of the ticket...

Link: https://jira.issworld.com/browse/PROJ-123
```

## 🧪 Testing

### Run Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov=models --cov-report=html

# Run specific test file
pytest tests/test_jira_service.py
```

### Manual Testing Checklist

- [ ] JIRA connection with PAT token
- [ ] Fetch unassigned tickets from queue
- [ ] AI classification accuracy
- [ ] AI summarization quality
- [ ] Workload calculation correctness
- [ ] Ticket assignment in JIRA
- [ ] Slack notification delivery
- [ ] Error handling for each service
- [ ] Dry-run mode functionality
- [ ] Log file creation and rotation

## 📊 Monitoring

### View Logs

```bash
# Real-time log monitoring
tail -f logs/automation.log

# View last 100 lines
tail -n 100 logs/automation.log

# Search for errors
grep ERROR logs/automation.log
```

### Check Execution Status

```bash
# If using systemd timer
systemctl status jira-automation.timer

# View execution history
journalctl -u jira-automation.service -n 50
```

## 🔒 Security Best Practices

1. **Never commit `.env` file** - Add to `.gitignore`
2. **Rotate tokens regularly** - Update PAT and API keys quarterly
3. **Use least-privilege access** - Grant only required permissions
4. **Secure log files** - Restrict access to logs directory
5. **Monitor for anomalies** - Set up alerts for unusual activity

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| No tickets found | Verify JQL filter in JIRA UI |
| Authentication failed | Regenerate PAT token |
| AI classification fails | Check Mistral API key and quota |
| Slack notification fails | Verify channel ID and bot permissions |
| Assignment fails | Check username exists in team.json |

### Debug Mode

Enable debug logging:

```bash
# In .env file
LOG_LEVEL=DEBUG

# Or run with debug flag
python main.py --debug
```

## 📈 Performance Considerations

- **Execution Time**: ~30-60 seconds for 10 tickets
- **API Rate Limits**: 
  - JIRA: 100 requests/minute
  - Mistral AI: Depends on plan
  - Slack: 1 message/second
- **Memory Usage**: ~100-200 MB
- **Disk Usage**: ~10 MB/day for logs

## 🔄 Workflow

```mermaid
graph TD
    A[Cron Trigger] --> B[Fetch Unassigned Tickets]
    B --> C{Tickets Found?}
    C -->|No| D[Exit]
    C -->|Yes| E[For Each Ticket]
    E --> F[Classify with AI]
    F --> G[Generate Summary]
    G --> H[Get Best Assignee]
    H --> I[Assign in JIRA]
    I --> J[Send Slack Notification]
    J --> K{More Tickets?}
    K -->|Yes| E
    K -->|No| L[Log Summary]
    L --> D
```

## 🚀 Deployment

### VPS Deployment (Production)

**Complete deployment guide**: [VPS_DEPLOYMENT_INSTRUCTIONS.md](VPS_DEPLOYMENT_INSTRUCTIONS.md)

**Quick deploy to Hostinger VPS:**
```bash
# Automated deployment
./deploy-to-vps.sh

# Or manual deployment
ssh root@31.97.231.244
cd /home/jirabot
git clone https://github.com/surac95/jira-studio-lab.git jira-automation
cd jira-automation/jira-automation
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Services managed by Supervisor:**
- `jira-automation-scheduler` - Runs every hour
- `jira-automation-flask` - Web API and Slack interactive endpoints

**Service management:**
```bash
supervisorctl status              # Check status
supervisorctl restart all         # Restart services
supervisorctl stop all            # Stop services
supervisorctl start all           # Start services
```

### Cloud Deployment Options

See deployment guides:
- **[CLOUD_DEPLOYMENT.md](jira-automation/CLOUD_DEPLOYMENT.md)** - Render, Railway, Heroku
- **[HOSTINGER_VPS_DEPLOYMENT.md](jira-automation/HOSTINGER_VPS_DEPLOYMENT.md)** - Detailed VPS setup

## 📚 Documentation

- **[OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md)** - Complete operations manual (service management, monitoring, troubleshooting)
- **[VPS_DEPLOYMENT_INSTRUCTIONS.md](VPS_DEPLOYMENT_INSTRUCTIONS.md)** - VPS deployment guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Development guide
- **[SLACK_INTERACTIVE_SETUP.md](jira-automation/SLACK_INTERACTIVE_SETUP.md)** - Slack integration setup

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is proprietary and confidential.

## 👥 Support

For issues or questions:
- Create an issue in the repository
- Contact the development team
- Check the troubleshooting guide in ARCHITECTURE.md

## 🎮 Current Deployment

**Status**: ✅ Live on Hostinger VPS
- **URL**: http://31.97.231.244:5000
- **Scheduler**: Runs every hour (10 tickets per run)
- **Slack**: Interactive buttons enabled
- **Python**: 3.12.3

## 🔮 Future Enhancements

- [ ] Web dashboard for configuration
- [ ] Advanced assignment algorithms
- [ ] Multi-label classification
- [ ] Ticket escalation rules
- [ ] SLA monitoring
- [ ] Performance analytics dashboard
- [ ] Microsoft Teams integration
- [ ] Email notifications
- [ ] SSL/HTTPS support

---

**Version**: 1.1
**Last Updated**: 2026-06-12
**Maintained By**: Surendran C
**Repository**: https://github.com/surac95/jira-studio-lab