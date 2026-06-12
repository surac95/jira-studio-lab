# Testing Guide for JIRA Automation System

This guide explains how to test the system without real JIRA credentials and with mock data.

## 🧪 Testing Options

### Option 1: Unit Tests (No Credentials Needed)

The easiest way to test the system is to run the unit tests, which use mocked services:

```bash
# Install dependencies first
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test files
pytest tests/test_workload_service.py
pytest tests/test_slack_service.py
pytest tests/test_main.py
```

**What this tests:**
- ✅ All service logic
- ✅ Assignment algorithms
- ✅ Message formatting
- ✅ Error handling
- ✅ Integration between services
- ❌ Real API connections (mocked)

### Option 2: Demo Script with Mock Data

Run the demo script to see the system in action with simulated data:

```bash
python demo.py
```

This will:
- Create mock tickets
- Simulate AI analysis
- Demonstrate assignment logic
- Show Slack message formatting
- Display team workload
- No real API calls needed

### Option 3: Test Individual Components

Test specific components interactively:

```python
# Test WorkloadService
python -c "
from config import get_settings
from services import WorkloadService

settings = get_settings()
workload = WorkloadService(settings)

# Show team status
print('Team Members:')
for member in workload.get_team_workload():
    print(f'  {member[\"name\"]}: {member[\"current_ticket_count\"]}/{member[\"max_capacity\"]}')

# Get statistics
stats = workload.get_assignment_statistics()
print(f'\nTeam Capacity: {stats[\"capacity_percentage\"]:.1f}%')
"
```

### Option 4: Test with Real Credentials (Optional)

If you have JIRA credentials, you can test with real data:

#### Step 1: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Add your credentials:
```env
JIRA_URL=https://your-jira-instance.com
JIRA_PAT_TOKEN=your_token_here
JIRA_PROJECT_KEY=YOUR_PROJECT
JIRA_QUEUE_JQL=project = YOUR_PROJECT AND assignee is EMPTY
MISTRAL_API_KEY=your_mistral_key_here
SLACK_BOT_TOKEN=xoxb-your-slack-token
SLACK_CHANNEL_ID=C1234567890
LOG_LEVEL=INFO
```

#### Step 2: Test Connections

```bash
python main.py --test-connections
```

This will verify:
- ✅ JIRA connection and authentication
- ✅ Slack connection and bot permissions
- ✅ AI service initialization

#### Step 3: Check Team Status

```bash
python main.py --team-status
```

Shows current team workload without making any changes.

#### Step 4: Dry Run

```bash
python main.py --dry-run
```

This will:
- ✅ Fetch real tickets from JIRA
- ✅ Analyze with AI
- ✅ Determine assignments
- ❌ NOT update JIRA
- ❌ NOT send Slack notifications

Perfect for testing the logic without making changes!

#### Step 5: Limited Production Run

```bash
python main.py --max-tickets 1
```

Process just 1 ticket to test the full workflow safely.

## 🎯 Recommended Testing Workflow

### For Development/Testing (No Credentials):

1. **Run Unit Tests:**
   ```bash
   pytest -v
   ```

2. **Run Demo Script:**
   ```bash
   python demo.py
   ```

3. **Test Individual Components:**
   ```bash
   python -c "from services import WorkloadService; print('WorkloadService imported successfully')"
   ```

### For Production Setup (With Credentials):

1. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Test Connections:**
   ```bash
   python main.py --test-connections
   ```

3. **Check Team Status:**
   ```bash
   python main.py --team-status
   ```

4. **Dry Run:**
   ```bash
   python main.py --dry-run --max-tickets 5
   ```

5. **Limited Production:**
   ```bash
   python main.py --max-tickets 1
   ```

6. **Full Production:**
   ```bash
   python main.py
   ```

## 🔍 What Each Test Validates

### Unit Tests (`pytest`)
- ✅ Service initialization
- ✅ Assignment algorithm logic
- ✅ Workload calculations
- ✅ Message formatting
- ✅ Error handling
- ✅ Edge cases
- ✅ Integration between components

### Demo Script (`demo.py`)
- ✅ End-to-end workflow
- ✅ Mock data processing
- ✅ Assignment decisions
- ✅ Message generation
- ✅ Statistics tracking

### Connection Test (`--test-connections`)
- ✅ JIRA API connectivity
- ✅ JIRA authentication
- ✅ Slack API connectivity
- ✅ Slack bot permissions
- ✅ AI service initialization

### Team Status (`--team-status`)
- ✅ Team configuration loading
- ✅ Workload calculations
- ✅ Capacity tracking
- ✅ Specialization mapping

### Dry Run (`--dry-run`)
- ✅ Ticket fetching from JIRA
- ✅ AI analysis
- ✅ Assignment logic
- ✅ Workflow execution
- ❌ No JIRA updates
- ❌ No Slack notifications

## 🐛 Troubleshooting

### "Module not found" errors
```bash
# Make sure you're in the jira-automation directory
cd jira-automation

# Install dependencies
pip install -r requirements.txt
```

### "Configuration validation failed"
```bash
# For unit tests, this is normal - tests use mocked settings
pytest

# For main.py, you need to configure .env
cp .env.example .env
# Edit .env with your credentials
```

### "Import errors"
```bash
# Make sure Python can find the modules
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run from the jira-automation directory
cd jira-automation
python main.py --help
```

## 📊 Expected Test Results

### Successful Unit Tests:
```
tests/test_workload_service.py ............ [ 20%]
tests/test_slack_service.py ............... [ 45%]
tests/test_integration.py ................. [ 65%]
tests/test_main.py ........................ [100%]

====== 50+ passed in 2.5s ======
```

### Successful Connection Test:
```
Testing service connections...
JIRA connection: ✓ OK
Slack connection: ✓ OK
AI service: ✓ OK

✓ All connections successful!
```

### Successful Dry Run:
```
Processing ticket 1/5: PROJ-123
Analyzing ticket PROJ-123...
Analysis complete: TRIRIGA (confidence: 95%, urgency: high)
Assigned to Alice Johnson (workload: 2/5)
✓ Ticket PROJ-123 assigned to Alice Johnson

Workflow Completed
Tickets fetched: 5
Tickets analyzed: 5
Tickets assigned: 5
Tickets failed: 0
```

## 🎓 Learning Path

1. **Start with Unit Tests** - Understand how each component works
2. **Run Demo Script** - See the full workflow with mock data
3. **Test Connections** - Verify your credentials (if available)
4. **Dry Run** - Test with real data without making changes
5. **Limited Production** - Process 1-2 tickets
6. **Full Production** - Deploy with confidence

## 💡 Tips

- Always start with `--dry-run` when testing with real data
- Use `--max-tickets 1` for initial production tests
- Check logs in `logs/` directory for detailed information
- Use `--log-level DEBUG` for more verbose output
- Test team configuration changes with `--team-status`

## 🔐 Security Notes

- Never commit `.env` file to git
- Use environment variables for sensitive data
- Test with limited permissions first
- Review dry-run results before production
- Monitor logs for unexpected behavior

---

**Ready to test? Start with:** `pytest -v`