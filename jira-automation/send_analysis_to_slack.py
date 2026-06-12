"""Send ticket analysis to Slack."""
import sys
from services.ai_service import AIService
from services.jira_service import JiraService
from services.slack_service import SlackService
from services.workload_service import WorkloadService
from config import get_settings

if len(sys.argv) < 2:
    print("Usage: python send_analysis_to_slack.py TICKET-KEY")
    sys.exit(1)

ticket_key = sys.argv[1]

# Initialize services
settings = get_settings()
ai_service = AIService(settings)
jira_service = JiraService(settings)
slack_service = SlackService(settings)
workload_service = WorkloadService(settings)

# Fetch ticket
print(f"Fetching ticket {ticket_key}...")
tickets = jira_service.get_new_tickets(max_results=1)

# Find the specific ticket or fetch it directly
ticket = None
for t in tickets:
    if t.key == ticket_key:
        ticket = t
        break

if not ticket:
    # Try fetching with JIRA client
    print(f"Ticket not in unassigned queue, searching all tickets...")
    from jira import JIRA
    from models import Ticket
    
    jira_client = JIRA(
        server=settings.jira_url,
        token_auth=settings.jira_pat_token
    )
    try:
        issue = jira_client.issue(ticket_key)
        ticket = Ticket(
            key=issue.key,
            summary=issue.fields.summary,
            description=issue.fields.description or "",
            priority=issue.fields.priority.name if issue.fields.priority else "Medium",
            reporter=issue.fields.reporter.displayName if issue.fields.reporter else "Unknown",
            comments=[c.body for c in issue.fields.comment.comments] if hasattr(issue.fields, 'comment') else [],
            attachments=[a.filename for a in issue.fields.attachment] if hasattr(issue.fields, 'attachment') else []
        )
    except Exception as e:
        print(f"ERROR: Failed to fetch ticket {ticket_key}: {e}")
        sys.exit(1)

print(f"Analyzing ticket {ticket.key}...")

# Analyze with AI
try:
    analysis = ai_service.analyze_ticket(ticket)
    
    print(f"\nAnalysis complete:")
    print(f"  Category: {analysis['category']}")
    print(f"  Confidence: {analysis['confidence']:.0%}")
    print(f"  Urgency: {analysis['urgency']}")
    
    # Get assignee recommendation
    assignee = workload_service.assign_ticket(ticket, analysis['category'])
    
    if assignee:
        print(f"  Recommended assignee: {assignee.name}")
    else:
        print(f"  No available assignee for {analysis['category']}")
    
    # Send to Slack
    print(f"\nSending to Slack...")
    slack_service.send_ticket_notification(ticket, analysis, assignee)
    print(f"[OK] Slack notification sent successfully!")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Made with Bob
