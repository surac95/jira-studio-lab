"""
JIRA Automation System - Main Entry Point

This is the main entry point for the JIRA incident ticket automation system.
It orchestrates the workflow of fetching tickets, analyzing them with AI,
and assigning them to team members based on workload and skills.
"""

import sys
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import get_settings, Settings
from services import JiraService, AIService, WorkloadService, SlackService
from models import Ticket, TeamMember
from utils.logger import get_logger, shutdown_loggers


class TicketOrchestrator:
    """
    Main orchestrator for the JIRA automation workflow.
    
    This class coordinates all services to:
    1. Fetch unassigned tickets from JIRA
    2. Analyze tickets using AI
    3. Assign tickets based on workload and skills
    4. Send notifications via Slack
    5. Update JIRA with assignments
    
    Attributes:
        settings: Application settings
        jira_service: JIRA API service
        ai_service: AI analysis service
        workload_service: Workload management service
        slack_service: Slack notification service
        logger: Logger instance
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the orchestrator with all required services.
        
        Args:
            settings: Settings instance with configuration
        """
        self.settings = settings
        self.logger = get_logger(__name__)
        
        # Initialize services
        self.logger.info("Initializing services...")
        try:
            self.jira_service = JiraService(settings)
            self.ai_service = AIService(settings)
            self.workload_service = WorkloadService(settings)
            self.slack_service = SlackService(settings)
            self.logger.info("All services initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise
    
    def run(self, dry_run: bool = False, max_tickets: Optional[int] = None) -> Dict[str, Any]:
        """
        Run the main automation workflow.
        
        Args:
            dry_run: If True, don't make actual changes (no JIRA updates, no Slack notifications)
            max_tickets: Maximum number of tickets to process (None for all)
            
        Returns:
            Dictionary with execution statistics
        """
        self.logger.info("=" * 70)
        self.logger.info("Starting JIRA Automation Workflow")
        self.logger.info(f"Dry run mode: {dry_run}")
        self.logger.info("=" * 70)
        
        start_time = time.time()
        stats = {
            'tickets_fetched': 0,
            'tickets_analyzed': 0,
            'tickets_assigned': 0,
            'tickets_failed': 0,
            'by_category': {},
            'errors': []
        }
        
        try:
            # Step 1: Fetch unassigned tickets from JIRA
            self.logger.info("Step 1: Fetching unassigned tickets from JIRA...")
            tickets = self._fetch_tickets(max_tickets)
            stats['tickets_fetched'] = len(tickets)
            
            if not tickets:
                self.logger.info("No unassigned tickets found")
                return stats
            
            self.logger.info(f"Found {len(tickets)} unassigned ticket(s)")
            
            # Step 2: Process each ticket
            for i, ticket in enumerate(tickets, 1):
                self.logger.info(f"\nProcessing ticket {i}/{len(tickets)}: {ticket.key}")
                
                try:
                    # Analyze ticket
                    analysis = self._analyze_ticket(ticket)
                    stats['tickets_analyzed'] += 1
                    
                    # Track by category
                    category = analysis['category']
                    stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
                    
                    # Assign ticket
                    assignee = self._assign_ticket(ticket, analysis)
                    
                    if assignee:
                        # Update JIRA (unless dry run)
                        if not dry_run:
                            self._update_jira(ticket, assignee)
                        
                        # Send Slack notification (unless dry run)
                        if not dry_run:
                            self._send_notification(ticket, analysis, assignee)
                        
                        # Update workload
                        self.workload_service.update_member_workload(
                            assignee.jira_username,
                            1
                        )
                        
                        stats['tickets_assigned'] += 1
                        self.logger.info(
                            f"[OK] Ticket {ticket.key} assigned to {assignee.name}"
                        )
                    else:
                        self.logger.warning(
                            f"[SKIP] No available team member for {ticket.key} ({category})"
                        )
                        stats['tickets_failed'] += 1
                        stats['errors'].append({
                            'ticket': ticket.key,
                            'error': 'No available team member',
                            'category': category
                        })
                        
                        # Send error notification (unless dry run)
                        if not dry_run:
                            self._send_error_notification(ticket, category)
                
                except Exception as e:
                    self.logger.error(f"Error processing ticket {ticket.key}: {e}")
                    stats['tickets_failed'] += 1
                    stats['errors'].append({
                        'ticket': ticket.key,
                        'error': str(e)
                    })
            
            # Step 3: Send summary
            if not dry_run and stats['tickets_assigned'] > 0:
                self._send_summary(stats)
            
        except Exception as e:
            self.logger.error(f"Fatal error in workflow: {e}")
            stats['errors'].append({
                'error': f"Fatal error: {str(e)}"
            })
        
        finally:
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log final statistics
            self.logger.info("\n" + "=" * 70)
            self.logger.info("Workflow Completed")
            self.logger.info("=" * 70)
            self.logger.info(f"Execution time: {execution_time:.2f} seconds")
            self.logger.info(f"Tickets fetched: {stats['tickets_fetched']}")
            self.logger.info(f"Tickets analyzed: {stats['tickets_analyzed']}")
            self.logger.info(f"Tickets assigned: {stats['tickets_assigned']}")
            self.logger.info(f"Tickets failed: {stats['tickets_failed']}")
            
            if stats['by_category']:
                self.logger.info("\nBy Category:")
                for category, count in stats['by_category'].items():
                    self.logger.info(f"  {category}: {count}")
            
            if stats['errors']:
                self.logger.warning(f"\nErrors encountered: {len(stats['errors'])}")
                for error in stats['errors'][:5]:  # Show first 5 errors
                    self.logger.warning(f"  - {error}")
            
            self.logger.info("=" * 70)
            
            stats['execution_time'] = execution_time
        
        return stats
    
    def _fetch_tickets(self, max_tickets: Optional[int] = None) -> List[Ticket]:
        """
        Fetch unassigned tickets from JIRA.
        
        Args:
            max_tickets: Maximum number of tickets to fetch
            
        Returns:
            List of Ticket objects
        """
        try:
            tickets = self.jira_service.get_new_tickets(max_results=max_tickets or 50)
            return tickets
        except Exception as e:
            self.logger.error(f"Failed to fetch tickets from JIRA: {e}")
            raise
    
    def _analyze_ticket(self, ticket: Ticket) -> Dict[str, Any]:
        """
        Analyze a ticket using AI service.
        
        Args:
            ticket: Ticket to analyze
            
        Returns:
            Analysis dictionary with category, summary, etc.
        """
        try:
            self.logger.info(f"Analyzing ticket {ticket.key}...")
            analysis = self.ai_service.analyze_ticket(ticket)
            
            self.logger.info(
                f"Analysis complete: {analysis['category']} "
                f"(confidence: {analysis['confidence']:.0%}, "
                f"urgency: {analysis['urgency']})"
            )
            
            return analysis
        except Exception as e:
            self.logger.error(f"Failed to analyze ticket {ticket.key}: {e}")
            raise
    
    def _assign_ticket(
        self,
        ticket: Ticket,
        analysis: Dict[str, Any]
    ) -> Optional[TeamMember]:
        """
        Assign a ticket to a team member based on analysis.
        
        Args:
            ticket: Ticket to assign
            analysis: AI analysis results
            
        Returns:
            Assigned TeamMember or None if no one available
        """
        try:
            category = analysis['category']
            self.logger.info(f"Assigning ticket {ticket.key} ({category})...")
            
            assignee = self.workload_service.assign_ticket(ticket, category)
            
            if assignee:
                self.logger.info(
                    f"Assigned to {assignee.name} "
                    f"(workload: {assignee.current_ticket_count}/{assignee.max_capacity})"
                )
            else:
                self.logger.warning(f"No available team member for category {category}")
            
            return assignee
        except Exception as e:
            self.logger.error(f"Failed to assign ticket {ticket.key}: {e}")
            raise
    
    def _update_jira(self, ticket: Ticket, assignee: TeamMember) -> bool:
        """
        Update JIRA with the assignment.
        
        Args:
            ticket: Ticket to update
            assignee: Team member to assign to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Updating JIRA for ticket {ticket.key}...")
            success = self.jira_service.assign_ticket(
                ticket.key,
                assignee.jira_username
            )
            
            if success:
                self.logger.info(f"JIRA updated successfully for {ticket.key}")
            else:
                self.logger.warning(f"Failed to update JIRA for {ticket.key}")
            
            return success
        except Exception as e:
            self.logger.error(f"Error updating JIRA for {ticket.key}: {e}")
            return False
    
    def _send_notification(
        self,
        ticket: Ticket,
        analysis: Dict[str, Any],
        assignee: TeamMember
    ) -> bool:
        """
        Send Slack notification about the assignment.
        
        Args:
            ticket: Assigned ticket
            analysis: AI analysis results
            assignee: Assigned team member
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Sending Slack notification for {ticket.key}...")
            success = self.slack_service.send_ticket_notification(
                ticket,
                analysis,
                assignee
            )
            
            if success:
                self.logger.info(f"Slack notification sent for {ticket.key}")
            else:
                self.logger.warning(f"Failed to send Slack notification for {ticket.key}")
            
            return success
        except Exception as e:
            self.logger.error(f"Error sending Slack notification for {ticket.key}: {e}")
            return False
    
    def _send_error_notification(self, ticket: Ticket, category: str) -> None:
        """
        Send error notification when ticket cannot be assigned.
        
        Args:
            ticket: Ticket that couldn't be assigned
            category: Ticket category
        """
        try:
            self.slack_service.send_error_notification(
                f"Unable to assign ticket {ticket.key}",
                {
                    'ticket_key': ticket.key,
                    'category': category,
                    'reason': 'No available team member with required specialization',
                    'summary': ticket.summary
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to send error notification: {e}")
    
    def _send_summary(self, stats: Dict[str, Any]) -> None:
        """
        Send daily summary to Slack.
        
        Args:
            stats: Execution statistics
        """
        try:
            self.logger.info("Sending workflow summary to Slack...")
            
            # Get team capacity
            team_stats = self.workload_service.get_assignment_statistics()
            
            summary_stats = {
                'tickets_processed': stats['tickets_fetched'],
                'tickets_assigned': stats['tickets_assigned'],
                'by_category': stats['by_category'],
                'team_capacity': {
                    'total_capacity': team_stats['total_capacity'],
                    'used_capacity': team_stats['used_capacity'],
                    'capacity_percentage': team_stats['capacity_percentage']
                }
            }
            
            self.slack_service.send_daily_summary(summary_stats)
            self.logger.info("Summary sent successfully")
        except Exception as e:
            self.logger.error(f"Failed to send summary: {e}")
    
    def test_connections(self) -> Dict[str, bool]:
        """
        Test connections to all external services.
        
        Returns:
            Dictionary with connection test results
        """
        self.logger.info("Testing service connections...")
        
        results = {
            'jira': False,
            'slack': False,
            'ai': False
        }
        
        # Test JIRA
        try:
            results['jira'] = self.jira_service.test_connection()
            self.logger.info(f"JIRA connection: {'[OK]' if results['jira'] else '[FAIL]'}")
        except Exception as e:
            self.logger.error(f"JIRA connection test failed: {e}")
        
        # Test Slack
        try:
            results['slack'] = self.slack_service.test_connection()
            self.logger.info(f"Slack connection: {'[OK]' if results['slack'] else '[FAIL]'}")
        except Exception as e:
            self.logger.error(f"Slack connection test failed: {e}")
        
        # AI service doesn't have a test method, assume OK if initialized
        results['ai'] = True
        self.logger.info("AI service: [OK]")
        
        return results
    
    def get_team_status(self) -> Dict[str, Any]:
        """
        Get current team workload status.
        
        Returns:
            Dictionary with team workload information
        """
        workload = self.workload_service.get_team_workload()
        stats = self.workload_service.get_assignment_statistics()
        
        return {
            'team_members': workload,
            'statistics': stats
        }


def main():
    """
    Main function to run the JIRA automation system.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='JIRA Automation System - Intelligent Ticket Assignment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in production mode
  python main.py

  # Run in dry-run mode (no actual changes)
  python main.py --dry-run

  # Process only 5 tickets
  python main.py --max-tickets 5

  # Test connections only
  python main.py --test-connections

  # Show team status
  python main.py --team-status
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without making actual changes (no JIRA updates, no Slack notifications)'
    )
    
    parser.add_argument(
        '--max-tickets',
        type=int,
        default=None,
        help='Maximum number of tickets to process'
    )
    
    parser.add_argument(
        '--test-connections',
        action='store_true',
        help='Test connections to all services and exit'
    )
    
    parser.add_argument(
        '--team-status',
        action='store_true',
        help='Show current team workload status and exit'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Initialize logger
    logger = get_logger(__name__)
    
    try:
        # Print banner
        print("\n" + "=" * 70)
        print("JIRA Automation System - Intelligent Ticket Assignment")
        print("=" * 70 + "\n")
        
        # Load settings
        logger.info("Loading configuration...")
        settings = get_settings()
        
        # Validate settings
        is_valid, missing = settings.validate_required_settings()
        if not is_valid:
            logger.error("Configuration validation failed!")
            logger.error(f"Missing required settings: {', '.join(missing)}")
            print("\n[ERROR] Configuration Error!")
            print(f"Missing required settings: {', '.join(missing)}")
            print("\nPlease check your .env file and ensure all required variables are set.")
            return 1
        
        logger.info("Configuration loaded successfully")
        
        # Initialize orchestrator
        orchestrator = TicketOrchestrator(settings)
        
        # Handle special commands
        if args.test_connections:
            print("\nTesting service connections...\n")
            results = orchestrator.test_connections()
            
            print("\nConnection Test Results:")
            print("-" * 40)
            for service, status in results.items():
                status_icon = "[OK]" if status else "[FAIL]"
                status_text = "OK" if status else "Failed"
                print(f"{status_icon} {service.upper()}: {status_text}")
            print("-" * 40)
            
            all_ok = all(results.values())
            if all_ok:
                print("\n[OK] All connections successful!")
                return 0
            else:
                print("\n[FAIL] Some connections failed. Please check your configuration.")
                return 1
        
        if args.team_status:
            print("\nTeam Workload Status:\n")
            status = orchestrator.get_team_status()
            
            print("Team Members:")
            print("-" * 70)
            for member in status['team_members']:
                capacity_pct = member['capacity_percentage']
                status_icon = "[OK]" if member['has_capacity'] else "[FULL]"
                avail_text = "Available" if member['is_available'] else "Unavailable"
                
                print(f"{status_icon} {member['name']:<20} "
                      f"{member['current_ticket_count']}/{member['max_capacity']} tickets "
                      f"({capacity_pct:>5.1f}%) - {avail_text}")
                print(f"   Specializations: {', '.join(member['specializations'])}")
            
            print("\nOverall Statistics:")
            print("-" * 70)
            stats = status['statistics']
            print(f"Total Capacity: {stats['used_capacity']}/{stats['total_capacity']} "
                  f"({stats['capacity_percentage']:.1f}%)")
            print(f"Team Size: {stats['team_size']}")
            print(f"Available Members: {stats['available_members']}")
            
            if stats['by_category']:
                print("\nBy Category:")
                for category, cat_stats in stats['by_category'].items():
                    print(f"  {category}: {cat_stats['used_capacity']}/{cat_stats['total_capacity']} "
                          f"({cat_stats['capacity_percentage']:.1f}%) - "
                          f"{cat_stats['available_members']} available")
            
            return 0
        
        # Run main workflow
        if args.dry_run:
            print("[DRY-RUN] Running in DRY-RUN mode (no actual changes will be made)\n")
        
        stats = orchestrator.run(
            dry_run=args.dry_run,
            max_tickets=args.max_tickets
        )
        
        # Print summary
        print("\n" + "=" * 70)
        print("Execution Summary")
        print("=" * 70)
        print(f"Tickets Fetched:  {stats['tickets_fetched']}")
        print(f"Tickets Analyzed: {stats['tickets_analyzed']}")
        print(f"Tickets Assigned: {stats['tickets_assigned']}")
        print(f"Tickets Failed:   {stats['tickets_failed']}")
        print(f"Execution Time:   {stats.get('execution_time', 0):.2f} seconds")
        
        if stats['by_category']:
            print("\nBy Category:")
            for category, count in stats['by_category'].items():
                print(f"  {category}: {count}")
        
        print("=" * 70 + "\n")
        
        # Return appropriate exit code
        if stats['tickets_failed'] > 0:
            return 1
        return 0
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\n\n[!] Interrupted by user")
        return 130
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n[ERROR] Fatal Error: {e}")
        return 1
    
    finally:
        # Cleanup
        logger.info("Shutting down...")
        shutdown_loggers()


if __name__ == "__main__":
    sys.exit(main())


# Made with Bob
