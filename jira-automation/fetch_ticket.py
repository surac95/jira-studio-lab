"""
Quick script to fetch and display a specific JIRA ticket with comments.
"""

import sys
from config.settings import get_settings
from services.jira_service import JiraService
from models.ticket import Ticket

def fetch_and_display_ticket(ticket_key: str):
    """Fetch and display a JIRA ticket with all its details."""
    
    # Load settings
    settings = get_settings()
    
    # Initialize JIRA service
    jira_service = JiraService(settings)
    
    try:
        # Get the JIRA client
        client = jira_service._get_client()
        
        # Fetch the specific ticket
        print(f"\nFetching ticket {ticket_key}...\n")
        jira_issue = client.issue(ticket_key)
        
        # Convert to our Ticket model
        ticket = Ticket.from_jira_issue(jira_issue)
        
        # Display ticket information
        print("=" * 80)
        print(f"TICKET: {ticket.key}")
        print("=" * 80)
        print(f"\nSummary: {ticket.summary}")
        print(f"Priority: {ticket.priority}")
        print(f"Reporter: {ticket.reporter}")
        print(f"Created: {ticket.created_date}")
        
        print(f"\n{'Description:':-^80}")
        print(ticket.description if ticket.description else "(No description)")
        
        if ticket.comments:
            print(f"\n{'Comments (' + str(len(ticket.comments)) + '):':-^80}")
            for i, comment in enumerate(ticket.comments, 1):
                print(f"\n[Comment {i}]")
                print(comment)
                print("-" * 80)
        else:
            print(f"\n{'Comments:':-^80}")
            print("(No comments)")
        
        if ticket.attachments:
            print(f"\n{'Attachments:':-^80}")
            for attachment in ticket.attachments:
                print(f"  - {attachment}")
        
        print("\n" + "=" * 80)
        print("FULL CONTENT FOR AI ANALYSIS:")
        print("=" * 80)
        print(ticket.get_full_content())
        print("=" * 80)
        
        return ticket
        
    except Exception as e:
        print(f"\nError fetching ticket: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    ticket_key = sys.argv[1] if len(sys.argv) > 1 else "ITSD-321122"
    fetch_and_display_ticket(ticket_key)

# Made with Bob
