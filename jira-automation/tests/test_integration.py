"""
Integration tests for JIRA automation services.

Tests the integration between WorkloadService, SlackService, and other components.
"""

import pytest
from unittest.mock import Mock, patch

from config import get_settings
from services import WorkloadService, SlackService, AIService
from models import Ticket, TeamMember


@pytest.fixture
def mock_settings():
    """Create a mock Settings object for integration testing."""
    settings = Mock()
    settings.slack_bot_token = 'xoxb-test-token'
    settings.slack_channel_id = 'C12345678'
    settings.jira_url = 'https://jira.example.com'
    settings.mistral_api_key = 'test-api-key'
    settings.load_team_members.return_value = [
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
            'current_ticket_count': 1,
            'max_capacity': 5,
            'is_available': True
        }
    ]
    return settings


class TestServiceIntegration:
    """Test integration between services."""
    
    def test_workload_and_slack_integration(self, mock_settings):
        """Test that WorkloadService and SlackService can work together."""
        with patch('services.workload_service.get_logger'), \
             patch('services.slack_service.get_logger'), \
             patch('services.slack_service.WebClient') as mock_slack:
            
            # Setup mock Slack client
            mock_client = Mock()
            mock_client.chat_postMessage.return_value = {'ok': True}
            mock_slack.return_value = mock_client
            
            # Initialize services
            workload_service = WorkloadService(mock_settings)
            slack_service = SlackService(mock_settings)
            
            # Create a ticket
            ticket = Ticket(
                key='TEST-123',
                summary='Test ticket',
                description='Test description',
                priority='High'
            )
            
            # Create mock analysis
            analysis = {
                'category': 'TRIRIGA',
                'confidence': 0.95,
                'reasoning': 'Test reasoning',
                'summary': 'Test summary',
                'key_points': ['Point 1', 'Point 2'],
                'urgency': 'high'
            }
            
            # Assign ticket
            assignee = workload_service.assign_ticket(ticket, 'TRIRIGA')
            assert assignee is not None
            
            # Send notification
            result = slack_service.send_ticket_notification(
                ticket,
                analysis,
                assignee
            )
            assert result is True
            
            # Update workload
            success = workload_service.update_member_workload(
                assignee.jira_username,
                1
            )
            assert success is True
    
    def test_full_workflow_simulation(self, mock_settings):
        """Test a complete workflow from ticket assignment to notification."""
        with patch('services.workload_service.get_logger'), \
             patch('services.slack_service.get_logger'), \
             patch('services.slack_service.WebClient') as mock_slack:
            
            # Setup mock Slack client
            mock_client = Mock()
            mock_client.chat_postMessage.return_value = {'ok': True}
            mock_slack.return_value = mock_client
            
            # Initialize services
            workload_service = WorkloadService(mock_settings)
            slack_service = SlackService(mock_settings)
            
            # Simulate processing multiple tickets
            tickets = [
                ('TEST-101', 'TRIRIGA'),
                ('TEST-102', 'APIC'),
                ('TEST-103', 'TRIRIGA'),
            ]
            
            assigned_count = 0
            
            for ticket_key, category in tickets:
                ticket = Ticket(
                    key=ticket_key,
                    summary=f'{category} issue',
                    description='Test description',
                    priority='Medium'
                )
                
                analysis = {
                    'category': category,
                    'confidence': 0.90,
                    'reasoning': 'Test',
                    'summary': 'Test summary',
                    'key_points': ['Point 1'],
                    'urgency': 'medium'
                }
                
                # Assign ticket
                assignee = workload_service.assign_ticket(ticket, category)
                
                if assignee:
                    # Send notification
                    slack_service.send_ticket_notification(
                        ticket,
                        analysis,
                        assignee
                    )
                    
                    # Update workload
                    workload_service.update_member_workload(
                        assignee.jira_username,
                        1
                    )
                    
                    assigned_count += 1
            
            # Verify assignments were made
            assert assigned_count > 0
            
            # Get statistics
            stats = workload_service.get_assignment_statistics()
            assert stats['used_capacity'] > 0
    
    def test_workload_statistics_for_slack_summary(self, mock_settings):
        """Test that workload statistics can be used for Slack summaries."""
        with patch('services.workload_service.get_logger'), \
             patch('services.slack_service.get_logger'), \
             patch('services.slack_service.WebClient') as mock_slack:
            
            # Setup mock Slack client
            mock_client = Mock()
            mock_client.chat_postMessage.return_value = {'ok': True}
            mock_slack.return_value = mock_client
            
            # Initialize services
            workload_service = WorkloadService(mock_settings)
            slack_service = SlackService(mock_settings)
            
            # Get workload statistics
            stats = workload_service.get_assignment_statistics()
            
            # Create summary statistics
            summary_stats = {
                'tickets_processed': 10,
                'tickets_assigned': 8,
                'by_category': {
                    'TRIRIGA': 3,
                    'APIC': 2,
                    'APPC': 3
                },
                'team_capacity': {
                    'total_capacity': stats['total_capacity'],
                    'used_capacity': stats['used_capacity'],
                    'capacity_percentage': stats['capacity_percentage']
                }
            }
            
            # Send daily summary
            result = slack_service.send_daily_summary(summary_stats)
            assert result is True


class TestServiceImports:
    """Test that all services can be imported correctly."""
    
    def test_import_all_services(self):
        """Test that all services can be imported from services package."""
        from services import (
            JiraService,
            AIService,
            SlackService,
            WorkloadService
        )
        
        assert JiraService is not None
        assert AIService is not None
        assert SlackService is not None
        assert WorkloadService is not None
    
    def test_import_all_models(self):
        """Test that all models can be imported from models package."""
        from models import Ticket, TeamMember
        
        assert Ticket is not None
        assert TeamMember is not None
    
    def test_import_config(self):
        """Test that config can be imported."""
        from config import Settings, get_settings
        
        assert Settings is not None
        assert get_settings is not None


class TestErrorHandling:
    """Test error handling in integrated scenarios."""
    
    def test_slack_notification_failure_doesnt_break_workflow(self, mock_settings):
        """Test that Slack notification failure doesn't break the workflow."""
        with patch('services.workload_service.get_logger'), \
             patch('services.slack_service.get_logger'), \
             patch('services.slack_service.WebClient') as mock_slack:
            
            # Setup mock Slack client that fails
            mock_client = Mock()
            mock_client.chat_postMessage.side_effect = Exception('Slack error')
            mock_slack.return_value = mock_client
            
            # Initialize services
            workload_service = WorkloadService(mock_settings)
            slack_service = SlackService(mock_settings)
            
            # Create a ticket
            ticket = Ticket(key='TEST-123', summary='Test')
            analysis = {
                'category': 'TRIRIGA',
                'confidence': 0.95,
                'summary': 'Test',
                'key_points': [],
                'urgency': 'medium'
            }
            
            # Assign ticket
            assignee = workload_service.assign_ticket(ticket, 'TRIRIGA')
            assert assignee is not None
            
            # Try to send notification (should fail gracefully)
            result = slack_service.send_ticket_notification(
                ticket,
                analysis,
                assignee
            )
            assert result is False
            
            # Workload should still be updated
            success = workload_service.update_member_workload(
                assignee.jira_username,
                1
            )
            assert success is True
    
    def test_no_available_members_scenario(self, mock_settings):
        """Test handling when no team members are available."""
        # Modify settings to have no available members
        mock_settings.load_team_members.return_value = [
            {
                'name': 'Alice Johnson',
                'jira_username': 'alice.johnson',
                'specializations': ['TRIRIGA'],
                'current_ticket_count': 5,
                'max_capacity': 5,
                'is_available': True  # At capacity
            }
        ]
        
        with patch('services.workload_service.get_logger'), \
             patch('services.slack_service.get_logger'), \
             patch('services.slack_service.WebClient'):
            
            workload_service = WorkloadService(mock_settings)
            
            ticket = Ticket(key='TEST-123', summary='Test')
            
            # Try to assign when no one is available
            assignee = workload_service.assign_ticket(ticket, 'TRIRIGA')
            assert assignee is None


# Made with Bob