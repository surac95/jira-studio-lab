# Local Testing with Real Data - Step-by-Step Guide

This guide will help you test the JIRA automation system locally with your real credentials before deploying to production.

## 🎯 Overview

Testing locally allows you to:
- ✅ Verify all credentials work correctly
- ✅ Test with real JIRA tickets
- ✅ See actual AI analysis
- ✅ Preview Slack notifications
- ✅ Validate team assignments
- ❌ **Without making any changes** (using dry-run mode)

## 📋 Prerequisites

### What You'll Need:

1. **JIRA Credentials:**
   - JIRA instance URL
   - Personal Access Token (PAT)
   - Project key
   - JQL query for your queue

2. **Mistral AI API Key:**
   - Sign up at https://console.mistral.ai
   - Get API key from dashboard

3. **Slack Bot Token:**
   - Create Slack app at https://api.slack.com/apps
   - Add bot to workspace
   - Get bot token (starts with `xoxb-`)
   - Get channel ID

4. **Team Configuration:**
   - Team member names
   - JIRA usernames
   - Specializations (TRIRIGA, APIC, APPC)

## 🚀 Step-by-Step Setup

### Step 1: Install Dependencies

```bash
# Navigate to project directory
cd jira-automation

# Install all dependencies
pip install -r requirements.txt

# Verify installation
python -c "import jira, mistralai, slack_sdk; print('✓ All packages installed')"
```

### Step 2: Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Open for editing
# Windows: notepad .env
# Mac/Linux: nano .env
```

**Fill in your credentials:**

```env
# JIRA Configuration
JIRA_URL=https://your-company.atlassian.net
JIRA_PAT_TOKEN=your_personal_access_token_here
JIRA_PROJECT_KEY=YOURPROJECT
JIRA_QUEUE_JQL=project = YOURPROJECT AND assignee is EMPTY AND status = "To Do"

# Mistral AI Configuration
MISTRAL_API_KEY=your_mistral_api_key_here

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_CHANNEL_ID=C1234567890

# Logging
LOG_LEVEL=INFO
```

### Step 3: Configure Team Members

Edit `config/team.json`:

```json
{
  "team_members": [
    {
      "name": "Your Name",
      "jira_username": "your.jira.username",
      "specializations": ["TRIRIGA", "APPC"],
      "current_ticket_count": 0,
      "max_capacity": 5,
      "is_available": true
    },
    {
      "name": "Team Member 2",
      "jira_username": "member2.username",
      "specializations": ["APIC", "APPC"],
      "current_ticket_count": 0,
      "max_capacity": 5,
      "is_available": true
    }
  ]
}
```

**Important Fields:**
- `jira_username`: Must match exactly with JIRA username
- `specializations`: Categories this person can handle
- `max_capacity`: Maximum concurrent tickets
- `is_available`: Set to `false` if on vacation/unavailable

### Step 4: Test Connections

```bash
# Test all service connections
python main.py --test-connections
```

**Expected Output:**
```
Testing service connections...
JIRA connection: ✓ OK
Slack connection: ✓ OK
AI service: ✓ OK

✓ All connections successful!
```

**If any fail, check:**
- ❌ JIRA: Verify URL and PAT token
- ❌ Slack: Verify bot token and channel access
- ❌ AI: Verify Mistral API key

### Step 5: Check Team Status

```bash
# View current team workload
python main.py --team-status
```

**Expected Output:**
```
Team Workload Status:

Team Members:
----------------------------------------------------------------------
✓ Your Name            0/5 tickets ( 0.0%) - Available
   Specializations: TRIRIGA, APPC
✓ Team Member 2        0/5 tickets ( 0.0%) - Available
   Specializations: APIC, APPC

Overall Statistics:
----------------------------------------------------------------------
Total Capacity: 0/10 (0.0%)
Team Size: 2
Available Members: 2
```

### Step 6: Dry Run with 1 Ticket (SAFE!)

```bash
# Process just 1 ticket without making any changes
python main.py --dry-run --max-tickets 1
```

**What This Does:**
- ✅ Fetches 1 real ticket from JIRA
- ✅ Analyzes with AI
- ✅ Determines assignment
- ✅ Shows what would happen
- ❌ Does NOT update JIRA
- ❌ Does NOT send Slack notification

**Expected Output:**
```
======================================================================
  Starting JIRA Automation Workflow
======================================================================

Step 1: Fetching unassigned tickets from JIRA...
✓ Found 1 unassigned ticket(s)

Processing ticket 1/1: PROJ-123

📋 PROJ-123: User login issue in TRIRIGA
   Priority: High | Reporter: john.doe

🤖 Analyzing with AI...
   Category: TRIRIGA (confidence: 95%)
   Urgency: high

👤 Assigning ticket...
   ✓ Assigned to: Your Name
   Workload: 0/5

======================================================================
  Workflow Completed
======================================================================
Execution time: 3.45 seconds
Tickets fetched: 1
Tickets analyzed: 1
Tickets assigned: 1
Tickets failed: 0
```

### Step 7: Dry Run with Multiple Tickets

```bash
# Process up to 5 tickets (still safe, no changes)
python main.py --dry-run --max-tickets 5
```

**Review the output:**
- Check if categorization is correct
- Verify assignments make sense
- Look for any errors

### Step 8: Test with Debug Logging

```bash
# Run with detailed logging
python main.py --dry-run --max-tickets 1 --log-level DEBUG
```

This shows detailed information about:
- API calls
- AI responses
- Assignment decisions
- Error details

### Step 9: Review Logs

```bash
# Check the log files
cat logs/services_ai_service.log
cat logs/services_workload_service.log

# Or on Windows:
type logs\services_ai_service.log
```

## 🧪 Testing Checklist

Before going to production, verify:

- [ ] ✅ All connections test successfully
- [ ] ✅ Team members load correctly
- [ ] ✅ Tickets are fetched from JIRA
- [ ] ✅ AI categorization is accurate
- [ ] ✅ Assignments are logical
- [ ] ✅ No errors in logs
- [ ] ✅ Dry-run completes successfully
- [ ] ✅ Team status shows correct data

## 🎯 Production Test (1 Ticket)

Once dry-run looks good, test with 1 real ticket:

```bash
# Process 1 ticket FOR REAL
python main.py --max-tickets 1
```

**This WILL:**
- ✅ Update JIRA with assignment
- ✅ Send Slack notification
- ✅ Update team workload

**Check:**
1. JIRA ticket is assigned correctly
2. Slack notification appears in channel
3. Team status updates

## 🐛 Troubleshooting

### Issue: "Configuration validation failed"

**Solution:**
```bash
# Check which settings are missing
python -c "
from config import get_settings
settings = get_settings()
is_valid, missing = settings.validate_required_settings()
if not is_valid:
    print('Missing:', missing)
"
```

### Issue: "JIRA connection failed"

**Possible causes:**
1. Wrong JIRA URL (check for typos)
2. Invalid PAT token
3. Token doesn't have required permissions
4. Network/firewall issues

**Test JIRA separately:**
```python
python -c "
from jira import JIRA
jira = JIRA('https://your-jira.com', token_auth='your-token')
print('Connected:', jira.current_user())
"
```

### Issue: "Slack connection failed"

**Possible causes:**
1. Invalid bot token
2. Bot not added to channel
3. Wrong channel ID

**Test Slack separately:**
```python
python -c "
from slack_sdk import WebClient
client = WebClient(token='xoxb-your-token')
response = client.auth_test()
print('Connected:', response['ok'])
"
```

### Issue: "No tickets found"

**Check your JQL:**
```bash
# Test JQL in JIRA web interface
# Go to: Issues → Search for issues → Advanced
# Paste your JQL query
```

### Issue: "AI analysis failed"

**Possible causes:**
1. Invalid Mistral API key
2. Rate limit exceeded
3. Network issues

**Test Mistral separately:**
```python
python -c "
from mistralai.client import MistralClient
client = MistralClient(api_key='your-key')
response = client.chat.complete(
    model='mistral-large-latest',
    messages=[{'role': 'user', 'content': 'Hello'}]
)
print('Connected:', response.choices[0].message.content)
"
```

## 📊 Understanding the Output

### Successful Run:
```
✓ Ticket PROJ-123 assigned to Your Name
```
- Ticket was categorized
- Suitable team member found
- Assignment made successfully

### Warning:
```
✗ No available team member for PROJ-456 (APIC)
```
- No one with APIC specialization available
- Or all APIC specialists at capacity
- Ticket remains unassigned

### Error:
```
Error processing ticket PROJ-789: Connection timeout
```
- Something went wrong
- Check logs for details
- Ticket will be retried next run

## 🎓 Best Practices for Testing

1. **Start Small:**
   - Test with 1 ticket first
   - Gradually increase to 5, 10, etc.

2. **Use Dry-Run:**
   - Always test with `--dry-run` first
   - Verify output before real run

3. **Check Logs:**
   - Review logs after each test
   - Look for warnings or errors

4. **Verify Assignments:**
   - Check if assignments make sense
   - Ensure workload is balanced

5. **Test Edge Cases:**
   - What if no one is available?
   - What if all at capacity?
   - What if ticket has no category?

## 🚀 Ready for Production?

Once you've verified:
- ✅ Connections work
- ✅ Dry-run succeeds
- ✅ 1 ticket test works
- ✅ Assignments are correct
- ✅ Slack notifications appear

You're ready to:
1. Deploy to PythonAnywhere
2. Configure cron-job.org
3. Let it run automatically!

## 📞 Need Help?

If you encounter issues:
1. Check this troubleshooting guide
2. Review logs in `logs/` directory
3. Test each service individually
4. Verify all credentials
5. Check network connectivity

---

**Remember: Always test with `--dry-run` first!**