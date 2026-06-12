# Slack Interactive Features Setup Guide

This guide explains how to set up the interactive Slack buttons for on-demand deep analysis.

## 🎯 Overview

The system now includes interactive Slack buttons that allow team members to:
- **Get Deep Analysis** - Request detailed AI analysis on-demand
- **Re-analyze** - Re-run analysis with latest ticket updates
- **View in JIRA** - Quick link to the ticket

This saves costs by only running deep analysis when needed!

## 📋 Prerequisites

1. ✅ Slack Bot Token configured
2. ✅ Flask app deployed (PythonAnywhere, Heroku, etc.)
3. ✅ Public URL for your Flask app
4. ✅ Slack App with appropriate permissions

## 🔧 Setup Steps

### Step 1: Configure Slack App Interactivity

1. **Go to Slack API Dashboard**
   - Visit: https://api.slack.com/apps
   - Select your app (or create one if you haven't)

2. **Enable Interactivity**
   - Go to "Interactivity & Shortcuts" in the left sidebar
   - Toggle "Interactivity" to **ON**

3. **Set Request URL**
   - Enter your Flask app URL + `/slack/interactive`
   - Example: `https://yourusername.pythonanywhere.com/slack/interactive`
   - Click "Save Changes"

4. **Verify Permissions**
   - Go to "OAuth & Permissions"
   - Ensure these scopes are added:
     - `chat:write` - Send messages
     - `chat:write.public` - Send to public channels
     - `channels:read` - Read channel info
     - `users:read` - Read user info

### Step 2: Deploy Flask App

#### Option A: PythonAnywhere (Recommended)

1. **Upload Code**
   ```bash
   # Zip your jira-automation folder
   zip -r jira-automation.zip jira-automation/
   
   # Upload to PythonAnywhere via Web interface
   ```

2. **Configure Web App**
   - Go to "Web" tab
   - Click "Add a new web app"
   - Choose "Flask"
   - Set working directory: `/home/yourusername/jira-automation`
   - Set WSGI file to point to `flask_app.py`

3. **Install Dependencies**
   ```bash
   # In PythonAnywhere Bash console
   cd jira-automation
   pip install --user -r requirements.txt
   ```

4. **Set Environment Variables**
   - Add to `.env` file or set in WSGI configuration
   - Include all JIRA, Mistral, and Slack credentials

5. **Reload Web App**
   - Click "Reload" button in Web tab

#### Option B: Heroku

1. **Create Heroku App**
   ```bash
   heroku create your-app-name
   ```

2. **Add Procfile**
   ```
   web: gunicorn flask_app:app
   ```

3. **Deploy**
   ```bash
   git push heroku main
   ```

4. **Set Environment Variables**
   ```bash
   heroku config:set JIRA_URL=...
   heroku config:set JIRA_PAT_TOKEN=...
   heroku config:set MISTRAL_API_KEY=...
   heroku config:set SLACK_BOT_TOKEN=...
   heroku config:set SLACK_CHANNEL_ID=...
   ```

### Step 3: Test the Setup

1. **Test Flask Endpoint**
   ```bash
   curl https://your-app-url.com/health
   ```
   
   Should return:
   ```json
   {
     "status": "healthy",
     "services": {
       "jira": true,
       "slack": true,
       "ai": true
     }
   }
   ```

2. **Process a Test Ticket**
   ```bash
   python main.py --max-tickets 1
   ```

3. **Check Slack Channel**
   - You should see a ticket notification
   - With three buttons: "Get Deep Analysis", "View in JIRA", "Re-analyze"

4. **Click "Get Deep Analysis"**
   - Should see a loading indicator
   - Within 5-10 seconds, detailed analysis appears
   - Includes root cause, solutions, impact, next steps

## 🎨 Message Examples

### Initial Ticket Notification
```
🎫 New Ticket Assigned: ITSD-321122

Ticket: ITSD-321122
Assigned To: Chandrasekaran, Surendran
Category: 🏢 TRIRIGA
Urgency: 🟡 MEDIUM
Confidence: 85%
Priority: Low

Summary: tririga lock users with KIA

AI Analysis:
User experiencing account lockouts when switching between 
TRIRIGA instances using KIA mobile app.

Key Points:
• User gets locked after switching instances
• Issue started after APIC activation
• Affects cross-instance mobile operations

[🔍 Get Deep Analysis] [📊 View in JIRA] [🔄 Re-analyze]
```

### Deep Analysis Response (After Button Click)
```
🤖 AI Deep Analysis: ITSD-321122

🔍 Root Cause Analysis:
API Gateway session persistence conflict. APIC maintaining 
session state between independent TRIRIGA backends, causing 
authentication failures during instance switching.

💡 Recommended Solutions:
1. Configure APIC to disable sticky sessions for TRIRIGA endpoints
2. Implement header stripping between backends
3. Review session affinity settings
4. Consider implementing SSO across instances

⚠️ Impact Assessment:
Currently affects 1 user but will scale with multi-instance 
adoption. Blocks mobile app cross-instance operations. 
Medium-high priority for resolution.

🎯 Next Steps:
• Review APIC logs for provided timestamps
• Check session affinity configuration
• Test with header stripping
• Involve APIC team for gateway configuration

📊 Estimated Resolution: 3-5 days
💰 Analysis Cost: ~$0.004

[📊 View in JIRA] [🔄 Re-analyze]
```

## 💰 Cost Analysis

### Without Interactive Buttons (All Tickets)
- 100 tickets/month × $0.004 = **$0.40/month**

### With Interactive Buttons (On-Demand)
- 100 tickets/month × $0.001 (basic) = $0.10
- 20 tickets need deep analysis × $0.004 = $0.08
- **Total: $0.18/month** (55% savings!)

## 🔍 Troubleshooting

### Buttons Don't Appear
- Check Slack app has `chat:write` permission
- Verify Block Kit formatting in logs
- Ensure Slack SDK is up to date

### Buttons Don't Respond
- Check Flask app is running and accessible
- Verify Request URL in Slack app settings
- Check Flask logs for errors: `/var/log/flask_app.log`
- Ensure `/slack/interactive` endpoint is working

### Deep Analysis Times Out
- Check Mistral AI API key is valid
- Verify network connectivity from Flask app
- Check Flask app logs for AI service errors
- Increase timeout if needed (default: 30 seconds)

### Error Messages in Slack
- Check Flask app logs for detailed error
- Verify all environment variables are set
- Test JIRA connection: `python main.py --test-connections`
- Test AI service separately

## 🔐 Security Considerations

1. **Slack Verification**
   - Slack sends a verification token with each request
   - Flask app should verify this token
   - Add to `.env`: `SLACK_SIGNING_SECRET=your_secret`

2. **Rate Limiting**
   - Consider adding rate limiting to prevent abuse
   - Use Flask-Limiter or similar

3. **Authentication**
   - Keep your Slack Bot Token secure
   - Never commit tokens to git
   - Use environment variables

## 📊 Monitoring

### Track Button Usage
Add logging to track which buttons are clicked:

```python
# In flask_app.py
logger.info(f"Button clicked: {action_id} by user {user_id} for {ticket_key}")
```

### Monitor Costs
Track AI API usage:

```python
# In ai_service.py
logger.info(f"Deep analysis cost: ~$0.004 for {ticket_key}")
```

### Slack Analytics
- Go to Slack API Dashboard
- Check "Analytics" tab
- Monitor button click rates
- Track response times

## 🚀 Advanced Features

### Add More Buttons

Edit `slack_service.py` to add custom buttons:

```python
{
    "type": "button",
    "text": {"type": "plain_text", "text": "🔗 Find Similar"},
    "action_id": "find_similar",
    "value": ticket.key
}
```

Then handle in `flask_app.py`:

```python
elif action_id == 'find_similar':
    handle_find_similar_request(ticket_key, response_url)
```

### Smart Triggers

Auto-trigger deep analysis for high-priority tickets:

```python
# In main.py
if ticket.priority == "High":
    deep_analysis = ai_service.analyze_ticket_deep(ticket)
    slack_service.send_deep_analysis_response(...)
```

### Custom Analysis Types

Add different analysis depths:

- **Quick Analysis** (free) - Basic categorization
- **Standard Analysis** ($0.001) - With summary
- **Deep Analysis** ($0.004) - Full technical analysis
- **Expert Analysis** ($0.01) - With solution validation

## 📝 Next Steps

1. ✅ Complete Slack app configuration
2. ✅ Deploy Flask app to hosting platform
3. ✅ Test with a real ticket
4. ✅ Monitor usage and costs
5. ✅ Gather team feedback
6. ✅ Iterate and improve

## 🆘 Support

If you encounter issues:

1. Check Flask app logs
2. Check Slack app event logs
3. Test each component separately
4. Review this guide
5. Check Slack API documentation

## 🎉 Success Criteria

You'll know it's working when:
- ✅ Tickets appear in Slack with buttons
- ✅ Clicking "Get Deep Analysis" shows detailed analysis
- ✅ Analysis appears within 5-10 seconds
- ✅ Re-analyze button updates with latest info
- ✅ Team finds the analysis helpful
- ✅ Costs are under control

---

**Made with ❤️ by Bob - Your AI Coding Assistant**