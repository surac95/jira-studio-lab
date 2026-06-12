"""
Demo script for JIRA Automation System.

This script demonstrates the system functionality with mock data,
allowing you to test without real JIRA/Slack/AI credentials.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models import Ticket, TeamMember
from services.workload_service import WorkloadService
from config.settings import Settings


class MockSettings:
    """Mock settings for demo purposes."""
    
    def __init__(self):
        self.jira_url = "https://demo-jira.example.com"
        self.jira_pat_token = "demo-token"
        self.jira_project_key = "DEMO"
        self.jira_queue_jql = "project = DEMO AND assignee is EMPTY"
        self.mistral_api_key = "demo-api-key"
        self.slack_bot_token = "xoxb-demo-token"
        self.slack_channel_id = "C12345DEMO"
        self.log_level = "INFO"
        
        # Demo team members
        self.team_members = [
            {
                'name': 'Alice Johnson',
                'jira_username': 'alice.johnson',
                'specializations': ['TRIRIGA', 'APPC'],
                'current_ticket_count': 2,
                'max_capacity': 5,
                'is_available': True
            },
            {
                'name': 'Bob Smith',
                'jira_username': 'bob.smith',
                'specializations': ['APIC', 'APPC'],
                'current_ticket_count': 4,
                'max_capacity': 5,
                'is_available': True
            },
            {
                'name': 'Charlie Brown',
                'jira_username': 'charlie.brown',
                'specializations': ['TRIRIGA'],
                'current_ticket_count': 0,
                'max_capacity': 5,
                'is_available': True
            },
            {
                'name': 'Diana Prince',
                'jira_username': 'diana.prince',
                'specializations': ['APIC'],
                'current_ticket_count': 3,
                'max_capacity': 5,
                'is_available': False
            }
        ]
    
    def load_team_members(self):
        return self.team_members


def create_demo_tickets() -> List[Ticket]:
    """Create demo tickets for testing."""
    return [
        Ticket(
            key='DEMO-101',
            summary='TRIRIGA login issues for multiple users',
            description='Users are unable to login to TRIRIGA application. Error message: "Authentication failed". Started after recent update.',
            comments=['Affects 5 users in Building A', 'Urgent - blocking work'],
            priority='High',
            reporter='john.doe',
            created_date=datetime.now()
        ),
        Ticket(
            key='DEMO-102',
            summary='API Connect gateway timeout errors',
            description='API Gateway is returning 504 timeout errors for all requests. Need immediate investigation.',
            comments=['Production issue', 'Multiple customers affected'],
            priority='Highest',
            reporter='jane.smith',
            created_date=datetime.now()
        ),
        Ticket(
            key='DEMO-103',
            summary='Application performance degradation',
            description='General application slowness reported by users. Response times increased by 300%.',
            comments=['Started this morning', 'Database queries seem slow'],
            priority='Medium',
            reporter='mike.wilson',
            created_date=datetime.now()
        ),
        Ticket(
            key='DEMO-104',
            summary='TRIRIGA space management module not loading',
            description='Space management module fails to load. Console shows JavaScript errors.',
            comments=['Only affects space management', 'Other modules work fine'],
            priority='Medium',
            reporter='sarah.jones',
            created_date=datetime.now()
        ),
        Ticket(
            key='DEMO-105',
            summary='APIC API documentation not accessible',
            description='API documentation portal returns 403 Forbidden error.',
            comments=['External developers cannot access docs'],
            priority='Low',
            reporter='tom.brown',
            created_date=datetime.now()
        )
    ]


def mock_ai_analysis(ticket: Ticket) -> Dict[str, Any]:
    """Mock AI analysis based on ticket content."""
    content = ticket.get_full_content().lower()
    
    # Simple keyword-based categorization
    if 'tririga' in content:
        category = 'TRIRIGA'
        confidence = 0.95
    elif 'api connect' in content or 'apic' in content or 'api gateway' in content:
        category = 'APIC'
        confidence = 0.92
    else:
        category = 'APPC'
        confidence = 0.85
    
    # Determine urgency
    if ticket.priority in ['Highest', 'Critical']:
        urgency = 'high'
    elif ticket.priority == 'High':
        urgency = 'medium'
    else:
        urgency = 'low'
    
    # Generate summary
    summary = f"{ticket.summary}. {ticket.description[:100]}..."
    
    # Extract key points
    key_points = [
        ticket.summary,
        f"Priority: {ticket.priority}",
        f"Reporter: {ticket.reporter}"
    ]
    if ticket.comments:
        key_points.append(f"{len(ticket.comments)} comment(s)")
    
    return {
        'category': category,
        'confidence': confidence,
        'reasoning': f'Categorized as {category} based on content analysis',
        'summary': summary,
        'key_points': key_points[:5],
        'urgency': urgency
    }


def format_slack_message(ticket: Ticket, analysis: Dict[str, Any], assignee: TeamMember) -> str:
    """Format a Slack-style message for display."""
    urgency_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}
    category_emoji = {'TRIRIGA': '🏢', 'APIC': '🔌', 'APPC': '💻'}
    
    message = f"""
╔══════════════════════════════════════════════════════════════
║ 🎫 NEW TICKET ASSIGNED: {ticket.key}
╠══════════════════════════════════════════════════════════════
║
║ Ticket:      {ticket.key}
║ Assigned To: {assignee.name}
║ Category:    {category_emoji.get(analysis['category'], '📋')} {analysis['category']}
║ Urgency:     {urgency_emoji.get(analysis['urgency'], '⚪')} {analysis['urgency'].upper()}
║ Confidence:  {analysis['confidence']:.0%}
║ Priority:    {ticket.priority}
║
║ Summary:
║ {ticket.summary}
║
║ AI Analysis:
║ {analysis['summary'][:200]}...
║
║ Key Points:
"""
    for point in analysis['key_points']:
        message += f"║   • {point}\n"
    
    message += f"""║
║ Link: https://demo-jira.example.com/browse/{ticket.key}
║
╚══════════════════════════════════════════════════════════════
"""
    return message


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_section(text: str):
    """Print a formatted section header."""
    print(f"\n{'─' * 70}")
    print(f"  {text}")
    print(f"{'─' * 70}")


def main():
    """Run the demo."""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  JIRA AUTOMATION SYSTEM - DEMO MODE".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    
    print("\n📝 This demo shows the system working with mock data.")
    print("   No real JIRA/Slack/AI credentials needed!")
    
    # Initialize services
    print_header("1. INITIALIZING SERVICES")
    settings = MockSettings()
    workload_service = WorkloadService(settings)
    print("✓ WorkloadService initialized")
    print(f"✓ Loaded {len(settings.team_members)} team members")
    
    # Show team status
    print_header("2. TEAM STATUS")
    workload = workload_service.get_team_workload()
    for member in workload:
        status_icon = "✓" if member['has_capacity'] else "✗"
        avail_text = "Available" if member['is_available'] else "Unavailable"
        capacity_pct = member['capacity_percentage']
        
        print(f"{status_icon} {member['name']:<20} "
              f"{member['current_ticket_count']}/{member['max_capacity']} tickets "
              f"({capacity_pct:>5.1f}%) - {avail_text}")
        print(f"   Specializations: {', '.join(member['specializations'])}")
    
    # Show statistics
    stats = workload_service.get_assignment_statistics()
    print(f"\n📊 Team Capacity: {stats['used_capacity']}/{stats['total_capacity']} "
          f"({stats['capacity_percentage']:.1f}%)")
    print(f"   Available Members: {stats['available_members']}/{stats['team_size']}")
    
    # Create demo tickets
    print_header("3. FETCHING TICKETS")
    tickets = create_demo_tickets()
    print(f"✓ Found {len(tickets)} unassigned tickets")
    
    # Process each ticket
    print_header("4. PROCESSING TICKETS")
    
    assigned_count = 0
    failed_count = 0
    
    for i, ticket in enumerate(tickets, 1):
        print_section(f"Ticket {i}/{len(tickets)}: {ticket.key}")
        
        print(f"\n📋 {ticket.key}: {ticket.summary}")
        print(f"   Priority: {ticket.priority} | Reporter: {ticket.reporter}")
        
        # Analyze ticket
        print(f"\n🤖 Analyzing with AI...")
        analysis = mock_ai_analysis(ticket)
        print(f"   Category: {analysis['category']} (confidence: {analysis['confidence']:.0%})")
        print(f"   Urgency: {analysis['urgency']}")
        
        # Assign ticket
        print(f"\n👤 Assigning ticket...")
        assignee = workload_service.assign_ticket(ticket, analysis['category'])
        
        if assignee:
            print(f"   ✓ Assigned to: {assignee.name}")
            print(f"   Workload: {assignee.current_ticket_count}/{assignee.max_capacity}")
            
            # Update workload
            workload_service.update_member_workload(assignee.jira_username, 1)
            
            # Show Slack notification
            print(f"\n📢 Slack Notification:")
            print(format_slack_message(ticket, analysis, assignee))
            
            assigned_count += 1
        else:
            print(f"   ✗ No available team member for {analysis['category']}")
            failed_count += 1
    
    # Final summary
    print_header("5. EXECUTION SUMMARY")
    print(f"Tickets Fetched:  {len(tickets)}")
    print(f"Tickets Analyzed: {len(tickets)}")
    print(f"Tickets Assigned: {assigned_count}")
    print(f"Tickets Failed:   {failed_count}")
    
    # Updated team status
    print_section("Updated Team Status")
    workload = workload_service.get_team_workload()
    for member in workload:
        capacity_pct = member['capacity_percentage']
        print(f"  {member['name']:<20} "
              f"{member['current_ticket_count']}/{member['max_capacity']} tickets "
              f"({capacity_pct:>5.1f}%)")
    
    # Final statistics
    stats = workload_service.get_assignment_statistics()
    print(f"\n📊 Final Team Capacity: {stats['used_capacity']}/{stats['total_capacity']} "
          f"({stats['capacity_percentage']:.1f}%)")
    
    if stats['by_category']:
        print("\n📈 By Category:")
        for category, cat_stats in stats['by_category'].items():
            print(f"   {category}: {cat_stats['used_capacity']}/{cat_stats['total_capacity']} "
                  f"({cat_stats['capacity_percentage']:.1f}%)")
    
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    
    print("\n💡 Next Steps:")
    print("   1. Run unit tests: pytest -v")
    print("   2. Configure .env with your credentials")
    print("   3. Test connections: python main.py --test-connections")
    print("   4. Run dry-run: python main.py --dry-run")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# Made with Bob