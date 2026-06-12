# JIRA Automation System

AI-powered JIRA incident ticket automation system that automatically analyzes and assigns tickets to team members based on skills and workload.

## 🎯 Features

- **Intelligent Ticket Analysis**: Uses Mistral AI to categorize tickets (TRIRIGA, APIC, APPC)
- **Smart Assignment**: Assigns tickets based on team member specialization, availability, and workload
- **Slack Integration**: Sends rich notifications with ticket details and AI analysis
- **Workload Management**: Tracks team capacity and prevents overload
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Dry-Run Mode**: Test the system without making actual changes
- **Command-Line Interface**: Easy-to-use CLI with multiple options

## 📋 Project Structure

```
jira-automation/
├── config/              # Configuration files
│   ├── __init__.py
│   ├── settings.py      # Settings management ✅
│   └── team.json        # Team member configuration ✅
├── services/            # Service modules
│   ├── __init__.py
│   ├── jira_service.py      # JIRA API integration ✅
│   ├── ai_service.py        # Mistral AI integration ✅
│   ├── workload_service.py  # Workload management ✅
│   └── slack_service.py     # Slack notifications ✅
├── models/              # Data models
│   ├── __init__.py
│   ├── ticket.py        # Ticket model ✅
│   └── team_member.py   # Team member model ✅
├── utils/               # Utility modules
│   ├── __init__.py
│   └── logger.py        # Logging configuration ✅
├── tests/               # Test modules
│   ├── __init__.py
│   ├── test_jira_service.py      # JIRA service tests ✅
│   ├── test_ai_service.py        # AI service tests ✅
│   ├── test_workload_service.py  # Workload service tests ✅
│   ├── test_slack_service.py     # Slack service tests ✅
│   ├── test_integration.py       # Integration tests ✅
│   └── test_main.py              # Orchestrator tests ✅
├── logs/                # Log files directory
│   └── .gitkeep
├── main.py              # Main entry point ✅
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .gitignore          # Git ignore rules
└── setup.py            # Package installation configuration
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` and fill in your actual credentials:

```env
# JIRA Configuration
JIRA_URL=https://your-jira-instance.com
JIRA_PAT_TOKEN=your_personal_access_token
JIRA_PROJECT_KEY=PROJ
JIRA_QUEUE_JQL=project = PROJ AND assignee is EMPTY AND status = "To Do"

# Mistral AI Configuration
MISTRAL_API_KEY=your_mistral_api_key

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL_ID=C1234567890

# Logging
LOG_LEVEL=INFO
```

### 3. Configure Team Members

Edit `config/team.json` to add your team members:

```json
{
  "team_members": [
    {
      "name": "Alice Johnson",
      "jira_username": "alice.johnson",
      "specializations": ["TRIRIGA", "APPC"],
      "current_ticket_count": 0,
      "max_capacity": 5,
      "is_available": true
    },
    {
      "name": "Bob Smith",
      "jira_username": "bob.smith",
      "specializations": ["APIC", "APPC"],
      "current_ticket_count": 0,
      "max_capacity": 5,
      "is_available": true
    }
  ]
}
```

### 4. Test Connections

Before running the automation, test your connections:

```bash
python main.py --test-connections
```

### 5. Run the Application

```bash
# Run in production mode
python main.py

# Run in dry-run mode (no actual changes)
python main.py --dry-run

# Process only 5 tickets
python main.py --max-tickets 5

# Show team status
python main.py --team-status
```

## 📖 Usage

### Command-Line Options

```bash
python main.py [OPTIONS]

Options:
  --dry-run              Run without making actual changes
  --max-tickets N        Process maximum N tickets
  --test-connections     Test connections to all services
  --team-status          Show current team workload status
  --log-level LEVEL      Set logging level (DEBUG, INFO, WARNING, ERROR)
  -h, --help            Show help message
```

### Examples

**Test all service connections:**
```bash
python main.py --test-connections
```

**Check team workload:**
```bash
python main.py --team-status
```

**Run in dry-run mode (safe testing):**
```bash
python main.py --dry-run
```

**Process only 10 tickets:**
```bash
python main.py --max-tickets 10
```

**Enable debug logging:**
```bash
python main.py --log-level DEBUG
```

## 🔄 Workflow

The system follows this automated workflow:

1. **Fetch Tickets**: Retrieves unassigned tickets from JIRA using configured JQL
2. **Analyze Tickets**: Uses Mistral AI to:
   - Categorize tickets (TRIRIGA, APIC, APPC)
   - Generate summaries
   - Extract key points
   - Assess urgency
3. **Assign Tickets**: Intelligently assigns based on:
   - Team member specialization
   - Current workload
   - Availability status
   - Capacity limits
4. **Update JIRA**: Assigns ticket to selected team member
5. **Send Notifications**: Sends rich Slack notification with:
   - Ticket details
   - AI analysis
   - Assignee information
   - Urgency indicators
6. **Update Workload**: Tracks team member workload
7. **Send Summary**: Sends daily summary with statistics

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_workload_service.py

# Run with verbose output
pytest -v
```

Test coverage includes:
- Unit tests for all services (1,525+ lines)
- Integration tests
- Orchestrator tests
- Model tests
- Configuration tests

## 📊 Monitoring

### Logs

Logs are stored in the `logs/` directory with rotating file handlers:
- Maximum size: 10MB per file
- Keeps 5 backup files
- Includes timestamps, log levels, and detailed messages

### Slack Notifications

The system sends three types of Slack notifications:

1. **Ticket Notifications**: When a ticket is assigned
   - Ticket details with clickable link
   - AI analysis and summary
   - Category and urgency indicators
   - Assignee information

2. **Error Notifications**: When issues occur
   - Error description
   - Context information
   - Affected ticket details

3. **Daily Summaries**: After processing tickets
   - Tickets processed and assigned
   - Breakdown by category
   - Team capacity utilization

## 🔧 Configuration

### Team Member Configuration

Each team member in `config/team.json` has:

- `name`: Full name
- `jira_username`: JIRA username for assignment
- `specializations`: List of expertise areas (TRIRIGA, APIC, APPC)
- `current_ticket_count`: Current number of assigned tickets
- `max_capacity`: Maximum tickets they can handle
- `is_available`: Availability status

### JQL Query Configuration

The `JIRA_QUEUE_JQL` environment variable defines which tickets to fetch. Examples:

```jql
# Unassigned tickets in specific project
project = PROJ AND assignee is EMPTY

# Unassigned tickets with specific status
project = PROJ AND assignee is EMPTY AND status = "To Do"

# Unassigned tickets with priority
project = PROJ AND assignee is EMPTY AND priority in (High, Highest)

# Unassigned tickets created today
project = PROJ AND assignee is EMPTY AND created >= startOfDay()
```

## 🏗️ Architecture

### Services

- **JiraService**: JIRA API integration with retry logic
- **AIService**: Mistral AI integration for ticket analysis
- **WorkloadService**: Team workload management and assignment
- **SlackService**: Slack notifications with Block Kit formatting

### Models

- **Ticket**: Represents a JIRA ticket with all relevant fields
- **TeamMember**: Represents a team member with skills and capacity

### Orchestrator

The `TicketOrchestrator` class coordinates all services to execute the complete workflow.

## 🔐 Security

- API tokens stored in `.env` file (not committed to git)
- Sensitive values masked in logs
- PAT token authentication for JIRA
- Slack bot token for notifications

## 🐛 Troubleshooting

### Connection Issues

**JIRA Connection Failed:**
- Verify JIRA_URL is correct
- Check JIRA_PAT_TOKEN is valid
- Ensure network connectivity

**Slack Connection Failed:**
- Verify SLACK_BOT_TOKEN is valid
- Check bot has access to channel
- Ensure SLACK_CHANNEL_ID is correct

**AI Service Issues:**
- Verify MISTRAL_API_KEY is valid
- Check API rate limits
- Review error logs

### Assignment Issues

**No Available Team Members:**
- Check team member availability in `team.json`
- Verify specializations match ticket categories
- Check capacity limits

**Tickets Not Being Fetched:**
- Verify JQL query syntax
- Check JIRA permissions
- Review JIRA project configuration

## 📈 Performance

- Processes tickets with exponential backoff retry logic
- Handles rate limiting gracefully
- Thread-safe workload management
- Efficient API usage with batching

## 🔄 Development Status

### ✅ Completed Phases

- **Phase 1**: Project Setup
- **Phase 2**: Core Models and Configuration
- **Phase 3**: JIRA Service Implementation
- **Phase 4**: AI Service Implementation
- **Phase 5**: Workload and Slack Services
- **Phase 6**: Main Orchestrator and CLI

### 🎯 Production Ready

The system is fully implemented and ready for production use with:
- Complete service implementations
- Comprehensive test coverage
- Error handling and retry logic
- Logging and monitoring
- Documentation

## 📝 Dependencies

- **jira** (3.5.2): JIRA API integration
- **mistralai** (0.4.0): Mistral AI SDK for ticket analysis
- **slack-sdk** (3.27.1): Slack notifications
- **python-dotenv** (1.0.1): Environment variable management
- **requests** (2.31.0): HTTP requests
- **pytest** (8.1.1): Testing framework
- **pytest-cov** (5.0.0): Test coverage
- **python-dateutil** (2.9.0): Date utilities

## 🤝 Contributing

1. Follow PEP 8 style guide
2. Add tests for new features
3. Update documentation
4. Use type hints
5. Add Google-style docstrings

## 📄 License

Internal use only.

## 👥 Support

For issues or questions, contact the development team.

---

**Made with Bob** 🤖