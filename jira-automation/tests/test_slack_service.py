"""
Unit tests for SlackService.

Tests the Slack notification functionality including message formatting
and error handling.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, Any

from services.slack_service import SlackService
from models.ticket import Ticket
from models.team_member import TeamMember
from config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create a mock Settings object with Slack configuration."""
    settings = Mock(spec=Settings)
    settings.slack_bot_token = 'xoxb-test-token'
    settings.slack_channel_id = 'C12345678'
    settings.jira_url = 'https://jira.example.com'
    return settings


@pytest.fixture
def mock_slack_client():
    """Create a mock Slack WebClient."""
    with patch('services.slack_service.WebClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock successful responses
        mock_client.chat_postMessage.return_value = {'ok': True, 'ts': '1234567890.123456'}
        mock_client.auth_test.return_value = {'ok': True, 'user': 'test_bot'}
        mock_client.conversations_info.return_value = {
            'ok': True,
            'channel': {
                'id': 'C12345678',
                'name': 'test-channel',
                'is_channel': True,
                'is_private': False,
                'num_members': 10
            }
        }
        
        yield mock_client


@pytest.fixture
def slack_service(mock_settings, mock_slack_client):
    """Create a SlackService instance with mocked dependencies."""
    with patch('services.slack_service.get_logger'):
        service = SlackService(mock_settings)
    return service


@pytest.fixture
def sample_ticket():
    """Create a sample ticket for testing."""
    return Ticket(
        key='TEST-123',
        summary='Test ticket summary',
        description='Test ticket description',
        priority='High'
    )


@pytest.fixture
def sample_analysis():
    """Create sample AI analysis data."""
    return {
        'category': 'TRIRIGA',
        'confidence': 0.95,
        'reasoning': 'Contains TRIRIGA-specific keywords',
        'summary': 'User experiencing login issues with TRIRIGA application',
        'key_points': [
            'Login fails with error message',
            'Issue started after recent update',
            'Affects multiple users'
        ],
        'urgency': 'high'
    }


@pytest.fixture
def sample_assignee():
    """Create a sample team member."""
    return TeamMember(
        name='John Doe',
        jira_username='john.doe',
        specializations=['TRIRIGA', 'APPC'],
        current_ticket_count=2,
        max_capacity=5,
        is_available=True
    )


class TestSlackServiceInitialization:
    """Test SlackService initialization."""
    
    def test_initialization_success(self, mock_settings):
        """Test successful initialization with valid settings."""
        with patch('services.slack_service.WebClient'), \
             patch('services.slack_service.get_logger'):
            service = SlackService(mock_settings)
        
        assert service.settings == mock_settings
        assert service.channel_id == 'C12345678'
    
    def test_initialization_missing_token(self):
        """Test initialization fails with missing bot token."""
        settings = Mock(spec=Settings)
        settings.slack_bot_token = ''
        settings.slack_channel_id = 'C12345678'
        
        with patch('services.slack_service.get_logger'), \
             pytest.raises(ValueError, match='Slack bot token is not configured'):
            SlackService(settings)
    
    def test_initialization_missing_channel(self):
        """Test initialization fails with missing channel ID."""
        settings = Mock(spec=Settings)
        settings.slack_bot_token = 'xoxb-test-token'
        settings.slack_channel_id = ''
        
        with patch('services.slack_service.get_logger'), \
             pytest.raises(ValueError, match='Slack channel ID is not configured'):
            SlackService(settings)


class TestSendTicketNotification:
    """Test ticket notification sending."""
    
    def test_send_ticket_notification_success(
        self,
        slack_service,
        mock_slack_client,
        sample_ticket,
        sample_analysis,
        sample_assignee
    ):
        """Test successful ticket notification sending."""
        result = slack_service.send_ticket_notification(
            sample_ticket,
            sample_analysis,
            sample_assignee
        )
        
        assert result is True
        mock_slack_client.chat_postMessage.assert_called_once()
        
        # Verify call arguments
        call_args = mock_slack_client.chat_postMessage.call_args
        assert call_args.kwargs['channel'] == 'C12345678'
        assert 'blocks' in call_args.kwargs
        assert call_args.kwargs['text'] == 'New ticket assigned: TEST-123'
    
    def test_send_ticket_notification_includes_ticket_info(
        self,
        slack_service,
        mock_slack_client,
        sample_ticket,
        sample_analysis,
        sample_assignee
    ):
        """Test that notification includes ticket information."""
        slack_service.send_ticket_notification(
            sample_ticket,
            sample_analysis,
            sample_assignee
        )
        
        call_args = mock_slack_client.chat_postMessage.call_args
        blocks = call_args.kwargs['blocks']
        
        # Convert blocks to string for easier searching
        blocks_str = str(blocks)
        
        assert 'TEST-123' in blocks_str
        assert 'John Doe' in blocks_str
        assert 'TRIRIGA' in blocks_str
    
    def test_send_ticket_notification_includes_urgency_emoji(
        self,
        slack_service,
        mock_slack_client,
        sample_ticket,
        sample_analysis,
        sample_assignee
    ):
        """Test that notification includes urgency emoji."""
        slack_service.send_ticket_notification(
            sample_ticket,
            sample_analysis,
            sample_assignee
        )
        
        call_args = mock_slack_client.chat_postMessage.call_args
        blocks = call_args.kwargs['blocks']
        blocks_str = str(blocks)
        
        # High urgency should have red circle emoji
        assert '🔴' in blocks_str
    
    def test_send_ticket_notification_includes_jira_link(
        self,
        slack_service,
        mock_slack_client,
        sample_ticket,
        sample_analysis,
        sample_assignee
    ):
        """Test that notification includes JIRA link."""
        slack_service.send_ticket_notification(
            sample_ticket,
            sample_analysis,
            sample_assignee
        )
        
        call_args = mock_slack_client.chat_postMessage.call_args
        blocks = call_args.kwargs['blocks']
        blocks_str = str(blocks)
        
        assert 'https://jira.example.com/browse/TEST-123' in blocks_str
    
    def test_send_ticket_notification_api_error(
        self,
        slack_service,
        mock_slack_client,
        sample_ticket,
        sample_analysis,
        sample_assignee
    ):
        """Test handling of Slack API errors."""
        from slack_sdk.errors import SlackApiError
        
        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {}
        mock_slack_client.chat_postMessage.side_effect = SlackApiError(
            'Error', mock_response
        )
        
        result = slack_service.send_ticket_notification(
            sample_ticket,
            sample_analysis,
            sample_assignee
        )
        
        assert result is False
    
    def test_send_ticket_notification_with_retry(
        self,
        slack_service,
        mock_slack_client,
        sample_ticket,
        sample_analysis,
        sample_assignee
    ):
        """Test retry logic on transient failures."""
        # First call fails, second succeeds
        mock_slack_client.chat_postMessage.side_effect = [
            Exception('Transient error'),
            {'ok': True, 'ts': '1234567890.123456'}
        ]
        
        with patch('services.slack_service.time.sleep'):  # Speed up test
            result = slack_service.send_ticket_notification(
                sample_ticket,
                sample_analysis,
                sample_assignee
            )
        
        assert result is True
        assert mock_slack_client.chat_postMessage.call_count == 2


class TestSendErrorNotification:
    """Test error notification sending."""
    
    def test_send_error_notification_success(self, slack_service, mock_slack_client):
        """Test successful error notification sending."""
        result = slack_service.send_error_notification(
            'Test error message',
            {'ticket_key': 'TEST-123', 'error_type': 'API timeout'}
        )
        
        assert result is True
        mock_slack_client.chat_postMessage.assert_called_once()
    
    def test_send_error_notification_includes_error_message(
        self,
        slack_service,
        mock_slack_client
    ):
        """Test that error notification includes error message."""
        slack_service.send_error_notification('Test error message')
        
        call_args = mock_slack_client.chat_postMessage.call_args
        blocks = call_args.kwargs['blocks']
        blocks_str = str(blocks)
        
        assert 'Test error message' in blocks_str
        assert '⚠️' in blocks_str  # Warning emoji
    
    def test_send_error_notification_includes_context(
        self,
        slack_service,
        mock_slack_client
    ):
        """Test that error notification includes context."""
        context = {
            'ticket_key': 'TEST-123',
            'error_type': 'API timeout',
            'timestamp': '2024-01-01 12:00:00'
        }
        
        slack_service.send_error_notification('Test error', context)
        
        call_args = mock_slack_client.chat_postMessage.call_args
        blocks = call_args.kwargs['blocks']
        blocks_str = str(blocks)
        
        assert 'TEST-123' in blocks_str
        assert 'API timeout' in blocks_str
    
    def test_send_error_notification_without_context(
        self,
        slack_service,
        mock_slack_client
    ):
        """Test error notification without context."""
        result = slack_service.send_error_notification('Test error')
        
        assert result is True
        mock_slack_client.chat_postMessage.assert_called_once()
    
    def test_send_error_notification_api_error(
        self,
        slack_service,
        mock_slack_client
    ):
        """Test handling of API errors when sending error notification."""
        mock_slack_client.chat_postMessage.return_value = {'ok': False}
        
        result = slack_service.send_error_notification('Test error')
        
        assert result is False


class TestSendDailySummary:
    """Test daily summary sending."""
    
    def test_send_daily_summary_success(self, slack_service, mock_slack_client):
        """Test successful daily summary sending."""
        statistics = {
            'tickets_processed': 15,
            'tickets_assigned': 12,
            'by_category': {
                'TRIRIGA': 5,
                'APIC': 4,
                'APPC': 3
            },
            'team_capacity': {
                'total_capacity': 25,
                'used_capacity': 14,
                'capacity_percentage': 56.0
            }
        }
        
        result = slack_service.send_daily_summary(statistics)
        
        assert result is True
        mock_slack_client.chat_postMessage.assert_called_once()
    
    def test_send_daily_summary_includes_statistics(
        self,
        slack_service,
        mock_slack_client
    ):
        """Test that daily summary includes statistics."""
        statistics = {
            'tickets_processed': 15,
            'tickets_assigned': 12,
            'by_category': {'TRIRIGA': 5, 'APIC': 4, 'APPC': 3}
        }
        
        slack_service.send_daily_summary(statistics)
        
        call_args = mock_slack_client.chat_postMessage.call_args
        blocks = call_args.kwargs['blocks']
        blocks_str = str(blocks)
        
        assert '15' in blocks_str  # tickets_processed
        assert '12' in blocks_str  # tickets_assigned
        assert 'TRIRIGA' in blocks_str
        assert '📊' in blocks_str  # Summary emoji
    
    def test_send_daily_summary_includes_category_breakdown(
        self,
        slack_service,
        mock_slack_client
    ):
        """Test that summary includes category breakdown."""
        statistics = {
            'tickets_processed': 15,
            'tickets_assigned': 12,
            'by_category': {
                'TRIRIGA': 5,
                'APIC': 4,
                'APPC': 3
            }
        }
        
        slack_service.send_daily_summary(statistics)
        
        call_args = mock_slack_client.chat_postMessage.call_args
        blocks = call_args.kwargs['blocks']
        blocks_str = str(blocks)
        
        assert '🏢' in blocks_str  # TRIRIGA emoji
        assert '🔌' in blocks_str  # APIC emoji
        assert '💻' in blocks_str  # APPC emoji
    
    def test_send_daily_summary_includes_team_capacity(
        self,
        slack_service,
        mock_slack_client
    ):
        """Test that summary includes team capacity."""
        statistics = {
            'tickets_processed': 15,
            'tickets_assigned': 12,
            'team_capacity': {
                'total_capacity': 25,
                'used_capacity': 14,
                'capacity_percentage': 56.0
            }
        }
        
        slack_service.send_daily_summary(statistics)
        
        call_args = mock_slack_client.chat_postMessage.call_args
        blocks = call_args.kwargs['blocks']
        blocks_str = str(blocks)
        
        assert '14/25' in blocks_str
        assert '56.0%' in blocks_str


class TestTestConnection:
    """Test Slack connection testing."""
    
    def test_connection_success(self, slack_service, mock_slack_client):
        """Test successful connection test."""
        result = slack_service.test_connection()
        
        assert result is True
        mock_slack_client.auth_test.assert_called_once()
    
    def test_connection_failure(self, slack_service, mock_slack_client):
        """Test connection test failure."""
        mock_slack_client.auth_test.return_value = {'ok': False}
        
        result = slack_service.test_connection()
        
        assert result is False
    
    def test_connection_api_error(self, slack_service, mock_slack_client):
        """Test connection test with API error."""
        from slack_sdk.errors import SlackApiError
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {}
        mock_slack_client.auth_test.side_effect = SlackApiError(
            'Invalid token', mock_response
        )
        
        result = slack_service.test_connection()
        
        assert result is False


class TestGetChannelInfo:
    """Test channel information retrieval."""
    
    def test_get_channel_info_success(self, slack_service, mock_slack_client):
        """Test successful channel info retrieval."""
        info = slack_service.get_channel_info()
        
        assert info is not None
        assert info['id'] == 'C12345678'
        assert info['name'] == 'test-channel'
        assert info['is_channel'] is True
        assert info['num_members'] == 10
    
    def test_get_channel_info_failure(self, slack_service, mock_slack_client):
        """Test channel info retrieval failure."""
        mock_slack_client.conversations_info.return_value = {'ok': False}
        
        info = slack_service.get_channel_info()
        
        assert info is None
    
    def test_get_channel_info_api_error(self, slack_service, mock_slack_client):
        """Test channel info retrieval with API error."""
        from slack_sdk.errors import SlackApiError
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_slack_client.conversations_info.side_effect = SlackApiError(
            'Channel not found', mock_response
        )
        
        info = slack_service.get_channel_info()
        
        assert info is None


class TestMessageFormatting:
    """Test message formatting methods."""
    
    def test_format_ticket_message_structure(
        self,
        slack_service,
        sample_ticket,
        sample_analysis,
        sample_assignee
    ):
        """Test that ticket message has correct structure."""
        blocks = slack_service._format_ticket_message(
            sample_ticket,
            sample_analysis,
            sample_assignee
        )
        
        assert isinstance(blocks, list)
        assert len(blocks) > 0
        
        # Should have header, sections, and divider
        block_types = [block['type'] for block in blocks]
        assert 'header' in block_types
        assert 'section' in block_types
        assert 'divider' in block_types
    
    def test_format_error_message_structure(self, slack_service):
        """Test that error message has correct structure."""
        blocks = slack_service._format_error_message(
            'Test error',
            {'key': 'value'}
        )
        
        assert isinstance(blocks, list)
        assert len(blocks) > 0
        
        block_types = [block['type'] for block in blocks]
        assert 'header' in block_types
        assert 'section' in block_types
        assert 'divider' in block_types
    
    def test_format_daily_summary_structure(self, slack_service):
        """Test that daily summary has correct structure."""
        statistics = {
            'tickets_processed': 15,
            'tickets_assigned': 12
        }
        
        blocks = slack_service._format_daily_summary(statistics)
        
        assert isinstance(blocks, list)
        assert len(blocks) > 0
        
        block_types = [block['type'] for block in blocks]
        assert 'header' in block_types
        assert 'section' in block_types
        assert 'divider' in block_types


class TestRetryLogic:
    """Test retry logic for transient failures."""
    
    def test_retry_on_rate_limit(
        self,
        slack_service,
        mock_slack_client,
        sample_ticket,
        sample_analysis,
        sample_assignee
    ):
        """Test retry logic on rate limit error."""
        from slack_sdk.errors import SlackApiError
        
        # Mock rate limit error then success
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {'Retry-After': '1'}
        
        mock_slack_client.chat_postMessage.side_effect = [
            SlackApiError('Rate limited', mock_response_429),
            {'ok': True, 'ts': '1234567890.123456'}
        ]
        
        with patch('services.slack_service.time.sleep'):  # Speed up test
            result = slack_service.send_ticket_notification(
                sample_ticket,
                sample_analysis,
                sample_assignee
            )
        
        assert result is True
        assert mock_slack_client.chat_postMessage.call_count == 2
    
    def test_no_retry_on_client_error(
        self,
        slack_service,
        mock_slack_client,
        sample_ticket,
        sample_analysis,
        sample_assignee
    ):
        """Test that client errors are not retried."""
        from slack_sdk.errors import SlackApiError
        
        # Mock client error (400)
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers = {}
        
        mock_slack_client.chat_postMessage.side_effect = SlackApiError(
            'Bad request', mock_response
        )
        
        result = slack_service.send_ticket_notification(
            sample_ticket,
            sample_analysis,
            sample_assignee
        )
        
        assert result is False
        # Should only try once (no retry on client errors)
        assert mock_slack_client.chat_postMessage.call_count == 1
    
    def test_retry_on_server_error(
        self,
        slack_service,
        mock_slack_client,
        sample_ticket,
        sample_analysis,
        sample_assignee
    ):
        """Test retry logic on server error."""
        from slack_sdk.errors import SlackApiError
        
        # Mock server error then success
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        mock_response_500.headers = {}
        
        mock_slack_client.chat_postMessage.side_effect = [
            SlackApiError('Server error', mock_response_500),
            {'ok': True, 'ts': '1234567890.123456'}
        ]
        
        with patch('services.slack_service.time.sleep'):  # Speed up test
            result = slack_service.send_ticket_notification(
                sample_ticket,
                sample_analysis,
                sample_assignee
            )
        
        assert result is True
        assert mock_slack_client.chat_postMessage.call_count == 2


class TestStringRepresentations:
    """Test string representations."""
    
    def test_repr(self, slack_service):
        """Test __repr__ method."""
        repr_str = repr(slack_service)
        
        assert 'SlackService' in repr_str
        assert 'C12345678' in repr_str
    
    def test_str(self, slack_service):
        """Test __str__ method."""
        str_repr = str(slack_service)
        
        assert 'SlackService' in str_repr
        assert 'C12345678' in str_repr


# Made with Bob