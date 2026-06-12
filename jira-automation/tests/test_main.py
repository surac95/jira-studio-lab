"""
Unit tests for main orchestrator.

Tests the TicketOrchestrator class and main workflow.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import List, Dict, Any

from main import TicketOrchestrator
from models import Ticket, TeamMember
from config import Settings


@pytest.fixture
def mock_settings():
    """Create a mock Settings object."""
    settings = Mock(spec=Settings)
    settings.jira_url = 'https://jira.example.com'
    settings.jira_pat_token = 'test-token'
    settings.jira_project_key = 'TEST'
    settings.jira_queue_jql = 'project = TEST AND assignee is EMPTY'
    settings.mistral_api_key = 'test-api-key'
    settings.slack_bot_token = 'xoxb-test-token'
    settings.slack_channel_id = 'C12345678'
    settings.log_level = 'INFO'
    settings.load_team_members.return_value = [
        {
            'name': 'Alice Johnson',
            'jira_username': 'alice.johnson',
            'specializations': ['TRIRIGA'],
            'current_ticket_count': 0,
            'max_capacity': 5,
            'is_available': True
        }
    ]
    return settings


@pytest.fixture
def mock_services():
    """Create mock service objects."""
    services = {
        'jira': Mock(),
        'ai': Mock(),
        'workload': Mock(),
        'slack': Mock()
    }
    
    # Configure default behaviors
    services['jira'].test_connection.return_value = True
    services['jira'].get_new_tickets.return_value = []
    services['jira'].assign_ticket.return_value = True
    
    services['ai'].analyze_ticket.return_value = {
        'category': 'TRIRIGA',
        'confidence': 0.95,
        'reasoning': 'Test reasoning',
        'summary': 'Test summary',
        'key_points': ['Point 1', 'Point 2'],
        'urgency': 'medium'
    }
    
    services['workload'].assign_ticket.return_value = TeamMember(
        name='Alice Johnson',
        jira_username='alice.johnson',
        specializations=['TRIRIGA'],
        current_ticket_count=0,
        max_capacity=5,
        is_available=True
    )
    services['workload'].update_member_workload.return_value = True
    services['workload'].get_assignment_statistics.return_value = {
        'total_capacity': 5,
        'used_capacity': 1,
        'capacity_percentage': 20.0,
        'team_size': 1,
        'available_members': 1,
        'by_category': {}
    }
    services['workload'].get_team_workload.return_value = []
    
    services['slack'].send_ticket_notification.return_value = True
    services['slack'].send_error_notification.return_value = True
    services['slack'].send_daily_summary.return_value = True
    services['slack'].test_connection.return_value = True
    
    return services


@pytest.fixture
def orchestrator(mock_settings, mock_services):
    """Create a TicketOrchestrator with mocked services."""
    with patch('main.JiraService', return_value=mock_services['jira']), \
         patch('main.AIService', return_value=mock_services['ai']), \
         patch('main.WorkloadService', return_value=mock_services['workload']), \
         patch('main.SlackService', return_value=mock_services['slack']), \
         patch('main.get_logger'):
        
        orchestrator = TicketOrchestrator(mock_settings)
        orchestrator.jira_service = mock_services['jira']
        orchestrator.ai_service = mock_services['ai']
        orchestrator.workload_service = mock_services['workload']
        orchestrator.slack_service = mock_services['slack']
        
        return orchestrator


@pytest.fixture
def sample_ticket():
    """Create a sample ticket."""
    return Ticket(
        key='TEST-123',
        summary='Test ticket',
        description='Test description',
        priority='High'
    )


class TestOrchestratorInitialization:
    """Test TicketOrchestrator initialization."""
    
    def test_initialization_success(self, mock_settings):
        """Test successful initialization."""
        with patch('main.JiraService'), \
             patch('main.AIService'), \
             patch('main.WorkloadService'), \
             patch('main.SlackService'), \
             patch('main.get_logger'):
            
            orchestrator = TicketOrchestrator(mock_settings)
            
            assert orchestrator.settings == mock_settings
            assert orchestrator.jira_service is not None
            assert orchestrator.ai_service is not None
            assert orchestrator.workload_service is not None
            assert orchestrator.slack_service is not None
    
    def test_initialization_failure(self, mock_settings):
        """Test initialization failure when service fails."""
        with patch('main.JiraService', side_effect=Exception('Connection failed')), \
             patch('main.get_logger'), \
             pytest.raises(Exception, match='Connection failed'):
            
            TicketOrchestrator(mock_settings)


class TestRunWorkflow:
    """Test main workflow execution."""
    
    def test_run_with_no_tickets(self, orchestrator, mock_services):
        """Test workflow when no tickets are found."""
        mock_services['jira'].get_new_tickets.return_value = []
        
        stats = orchestrator.run()
        
        assert stats['tickets_fetched'] == 0
        assert stats['tickets_analyzed'] == 0
        assert stats['tickets_assigned'] == 0
    
    def test_run_with_single_ticket(self, orchestrator, mock_services, sample_ticket):
        """Test workflow with a single ticket."""
        mock_services['jira'].get_new_tickets.return_value = [sample_ticket]
        
        stats = orchestrator.run()
        
        assert stats['tickets_fetched'] == 1
        assert stats['tickets_analyzed'] == 1
        assert stats['tickets_assigned'] == 1
        assert 'TRIRIGA' in stats['by_category']
        
        # Verify service calls
        mock_services['ai'].analyze_ticket.assert_called_once_with(sample_ticket)
        mock_services['workload'].assign_ticket.assert_called_once()
        mock_services['jira'].assign_ticket.assert_called_once()
        mock_services['slack'].send_ticket_notification.assert_called_once()
    
    def test_run_with_multiple_tickets(self, orchestrator, mock_services):
        """Test workflow with multiple tickets."""
        tickets = [
            Ticket(key='TEST-101', summary='Ticket 1', priority='High'),
            Ticket(key='TEST-102', summary='Ticket 2', priority='Medium'),
            Ticket(key='TEST-103', summary='Ticket 3', priority='Low')
        ]
        mock_services['jira'].get_new_tickets.return_value = tickets
        
        stats = orchestrator.run()
        
        assert stats['tickets_fetched'] == 3
        assert stats['tickets_analyzed'] == 3
        assert stats['tickets_assigned'] == 3
        
        # Verify all tickets were processed
        assert mock_services['ai'].analyze_ticket.call_count == 3
        assert mock_services['workload'].assign_ticket.call_count == 3
    
    def test_run_dry_run_mode(self, orchestrator, mock_services, sample_ticket):
        """Test workflow in dry-run mode."""
        mock_services['jira'].get_new_tickets.return_value = [sample_ticket]
        
        stats = orchestrator.run(dry_run=True)
        
        assert stats['tickets_fetched'] == 1
        assert stats['tickets_analyzed'] == 1
        assert stats['tickets_assigned'] == 1
        
        # In dry-run mode, JIRA and Slack should not be updated
        mock_services['jira'].assign_ticket.assert_not_called()
        mock_services['slack'].send_ticket_notification.assert_not_called()
        mock_services['slack'].send_daily_summary.assert_not_called()
    
    def test_run_with_max_tickets_limit(self, orchestrator, mock_services):
        """Test workflow with max_tickets limit."""
        tickets = [
            Ticket(key=f'TEST-{i}', summary=f'Ticket {i}', priority='Medium')
            for i in range(10)
        ]
        mock_services['jira'].get_new_tickets.return_value = tickets
        
        stats = orchestrator.run(max_tickets=5)
        
        # Should fetch with max_tickets parameter
        mock_services['jira'].get_new_tickets.assert_called_once_with(max_results=5)
    
    def test_run_with_no_available_assignee(self, orchestrator, mock_services, sample_ticket):
        """Test workflow when no assignee is available."""
        mock_services['jira'].get_new_tickets.return_value = [sample_ticket]
        mock_services['workload'].assign_ticket.return_value = None
        
        stats = orchestrator.run()
        
        assert stats['tickets_fetched'] == 1
        assert stats['tickets_analyzed'] == 1
        assert stats['tickets_assigned'] == 0
        assert stats['tickets_failed'] == 1
        assert len(stats['errors']) == 1
        
        # Should send error notification
        mock_services['slack'].send_error_notification.assert_called_once()
    
    def test_run_with_analysis_failure(self, orchestrator, mock_services, sample_ticket):
        """Test workflow when ticket analysis fails."""
        mock_services['jira'].get_new_tickets.return_value = [sample_ticket]
        mock_services['ai'].analyze_ticket.side_effect = Exception('Analysis failed')
        
        stats = orchestrator.run()
        
        assert stats['tickets_fetched'] == 1
        assert stats['tickets_analyzed'] == 0
        assert stats['tickets_failed'] == 1
        assert len(stats['errors']) == 1
    
    def test_run_sends_summary(self, orchestrator, mock_services, sample_ticket):
        """Test that summary is sent after successful assignments."""
        mock_services['jira'].get_new_tickets.return_value = [sample_ticket]
        
        stats = orchestrator.run()
        
        # Summary should be sent
        mock_services['slack'].send_daily_summary.assert_called_once()
        
        # Verify summary content
        call_args = mock_services['slack'].send_daily_summary.call_args[0][0]
        assert 'tickets_processed' in call_args
        assert 'tickets_assigned' in call_args
        assert 'team_capacity' in call_args


class TestFetchTickets:
    """Test ticket fetching."""
    
    def test_fetch_tickets_success(self, orchestrator, mock_services):
        """Test successful ticket fetching."""
        tickets = [Ticket(key='TEST-123', summary='Test')]
        mock_services['jira'].get_new_tickets.return_value = tickets
        
        result = orchestrator._fetch_tickets()
        
        assert result == tickets
        mock_services['jira'].get_new_tickets.assert_called_once()
    
    def test_fetch_tickets_with_max_limit(self, orchestrator, mock_services):
        """Test fetching with max limit."""
        orchestrator._fetch_tickets(max_tickets=10)
        
        mock_services['jira'].get_new_tickets.assert_called_once_with(max_results=10)
    
    def test_fetch_tickets_failure(self, orchestrator, mock_services):
        """Test ticket fetching failure."""
        mock_services['jira'].get_new_tickets.side_effect = Exception('JIRA error')
        
        with pytest.raises(Exception, match='JIRA error'):
            orchestrator._fetch_tickets()


class TestAnalyzeTicket:
    """Test ticket analysis."""
    
    def test_analyze_ticket_success(self, orchestrator, mock_services, sample_ticket):
        """Test successful ticket analysis."""
        expected_analysis = {
            'category': 'TRIRIGA',
            'confidence': 0.95,
            'summary': 'Test summary',
            'key_points': ['Point 1'],
            'urgency': 'high'
        }
        mock_services['ai'].analyze_ticket.return_value = expected_analysis
        
        result = orchestrator._analyze_ticket(sample_ticket)
        
        assert result == expected_analysis
        mock_services['ai'].analyze_ticket.assert_called_once_with(sample_ticket)
    
    def test_analyze_ticket_failure(self, orchestrator, mock_services, sample_ticket):
        """Test ticket analysis failure."""
        mock_services['ai'].analyze_ticket.side_effect = Exception('AI error')
        
        with pytest.raises(Exception, match='AI error'):
            orchestrator._analyze_ticket(sample_ticket)


class TestAssignTicket:
    """Test ticket assignment."""
    
    def test_assign_ticket_success(self, orchestrator, mock_services, sample_ticket):
        """Test successful ticket assignment."""
        analysis = {'category': 'TRIRIGA', 'confidence': 0.95}
        assignee = TeamMember(
            name='Alice',
            jira_username='alice',
            specializations=['TRIRIGA']
        )
        mock_services['workload'].assign_ticket.return_value = assignee
        
        result = orchestrator._assign_ticket(sample_ticket, analysis)
        
        assert result == assignee
        mock_services['workload'].assign_ticket.assert_called_once_with(
            sample_ticket,
            'TRIRIGA'
        )
    
    def test_assign_ticket_no_assignee(self, orchestrator, mock_services, sample_ticket):
        """Test assignment when no assignee available."""
        analysis = {'category': 'TRIRIGA', 'confidence': 0.95}
        mock_services['workload'].assign_ticket.return_value = None
        
        result = orchestrator._assign_ticket(sample_ticket, analysis)
        
        assert result is None


class TestUpdateJira:
    """Test JIRA updates."""
    
    def test_update_jira_success(self, orchestrator, mock_services, sample_ticket):
        """Test successful JIRA update."""
        assignee = TeamMember(name='Alice', jira_username='alice')
        mock_services['jira'].assign_ticket.return_value = True
        
        result = orchestrator._update_jira(sample_ticket, assignee)
        
        assert result is True
        mock_services['jira'].assign_ticket.assert_called_once_with(
            'TEST-123',
            'alice'
        )
    
    def test_update_jira_failure(self, orchestrator, mock_services, sample_ticket):
        """Test JIRA update failure."""
        assignee = TeamMember(name='Alice', jira_username='alice')
        mock_services['jira'].assign_ticket.return_value = False
        
        result = orchestrator._update_jira(sample_ticket, assignee)
        
        assert result is False


class TestSendNotification:
    """Test Slack notifications."""
    
    def test_send_notification_success(self, orchestrator, mock_services, sample_ticket):
        """Test successful notification sending."""
        analysis = {'category': 'TRIRIGA', 'summary': 'Test'}
        assignee = TeamMember(name='Alice', jira_username='alice')
        mock_services['slack'].send_ticket_notification.return_value = True
        
        result = orchestrator._send_notification(sample_ticket, analysis, assignee)
        
        assert result is True
        mock_services['slack'].send_ticket_notification.assert_called_once()
    
    def test_send_notification_failure(self, orchestrator, mock_services, sample_ticket):
        """Test notification sending failure."""
        analysis = {'category': 'TRIRIGA', 'summary': 'Test'}
        assignee = TeamMember(name='Alice', jira_username='alice')
        mock_services['slack'].send_ticket_notification.return_value = False
        
        result = orchestrator._send_notification(sample_ticket, analysis, assignee)
        
        assert result is False


class TestConnectionTesting:
    """Test connection testing functionality."""
    
    def test_test_connections_all_success(self, orchestrator, mock_services):
        """Test connection testing when all succeed."""
        results = orchestrator.test_connections()
        
        assert results['jira'] is True
        assert results['slack'] is True
        assert results['ai'] is True
    
    def test_test_connections_jira_failure(self, orchestrator, mock_services):
        """Test connection testing when JIRA fails."""
        mock_services['jira'].test_connection.return_value = False
        
        results = orchestrator.test_connections()
        
        assert results['jira'] is False
        assert results['slack'] is True
        assert results['ai'] is True
    
    def test_test_connections_exception_handling(self, orchestrator, mock_services):
        """Test connection testing with exceptions."""
        mock_services['jira'].test_connection.side_effect = Exception('Connection error')
        
        results = orchestrator.test_connections()
        
        assert results['jira'] is False


class TestTeamStatus:
    """Test team status retrieval."""
    
    def test_get_team_status(self, orchestrator, mock_services):
        """Test getting team status."""
        workload = [
            {
                'name': 'Alice',
                'jira_username': 'alice',
                'current_ticket_count': 2,
                'max_capacity': 5
            }
        ]
        stats = {
            'total_capacity': 5,
            'used_capacity': 2,
            'team_size': 1
        }
        
        mock_services['workload'].get_team_workload.return_value = workload
        mock_services['workload'].get_assignment_statistics.return_value = stats
        
        result = orchestrator.get_team_status()
        
        assert 'team_members' in result
        assert 'statistics' in result
        assert result['team_members'] == workload
        assert result['statistics'] == stats


# Made with Bob