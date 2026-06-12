"""Analyze a specific ticket with AI."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import AIService
from services.jira_service import JiraService
from config import get_settings
import json

if len(sys.argv) < 2:
    print("Usage: python analyze_ticket.py TICKET-KEY")
    sys.exit(1)

ticket_key = sys.argv[1]

# Initialize services
settings = get_settings()
ai_service = AIService(settings)
jira_service = JiraService(settings)

# Fetch ticket
print(f"Fetching ticket {ticket_key}...")
tickets = jira_service.get_new_tickets(max_results=1)

# Find the specific ticket
ticket = None
for t in tickets:
    if t.key == ticket_key:
        ticket = t
        break

if not ticket:
    # Try fetching with a broader search
    print(f"Ticket not in unassigned queue, searching all tickets...")
    from jira import JIRA
    jira_client = JIRA(
        server=settings.jira_url,
        token_auth=settings.jira_pat_token
    )
    try:
        issue = jira_client.issue(ticket_key)
        from models import Ticket
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

print(f"\n{'='*80}")
print(f"TICKET: {ticket.key}")
print(f"{'='*80}")
print(f"Summary: {ticket.summary}")
print(f"Priority: {ticket.priority}")
print(f"\n{'='*80}")
print("AI ANALYSIS")
print(f"{'='*80}\n")

# Analyze with AI
try:
    analysis = ai_service.analyze_ticket(ticket)
    
    print(f"Category: {analysis['category']}")
    print(f"Confidence: {analysis['confidence']:.0%}")
    print(f"Urgency: {analysis['urgency'].upper()}")
    print(f"\nReasoning:")
    print(f"  {analysis['reasoning']}")
    print(f"\nSummary:")
    print(f"  {analysis['summary']}")
    print(f"\nKey Points:")
    for i, point in enumerate(analysis['key_points'], 1):
        print(f"  {i}. {point}")
    
    print(f"\n{'='*80}")
    print("DEEP ANALYSIS (On-Demand)")
    print(f"{'='*80}\n")
    
    # Get deep analysis
    deep = ai_service.analyze_ticket_deep(ticket)
    
    print(f"Root Cause:")
    print(f"  {deep['root_cause']}")
    print(f"\nRecommended Solutions:")
    for i, solution in enumerate(deep['solutions'], 1):
        print(f"  {i}. {solution}")
    print(f"\nImpact Assessment:")
    print(f"  {deep['impact']}")
    print(f"\nNext Steps:")
    for i, step in enumerate(deep['next_steps'], 1):
        print(f"  {i}. {step}")
    print(f"\nEstimated Resolution Time: {deep['estimated_resolution_time']}")
    print(f"Analysis Confidence: {deep['confidence']:.0%}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Made with Bob
