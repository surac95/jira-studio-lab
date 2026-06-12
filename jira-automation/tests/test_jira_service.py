"""
Unit tests for the JiraService class.

This module contains comprehensive tests for the JiraService class,
including connection testing, ticket operations, error handling, and retry logic.
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, call
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.jira_service import JiraService
from models.ticket import Ticket
from config.settings import Settings


class TestJiraService(unittest.TestCase):
    """Test cases for the JiraService class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mock settings
        self.mock_settings = Mock(spec=Settings)
        self.mock_settings.jira_url = "https://jira.example.com"
        self.mock_settings.jira_pat_token = "test_token_123"
        self.mock_settings.jira_project_key = "PROJ"
        self.mock_settings.jira_queue_jql = "project = PROJ AND assignee is EMPTY"
        
        # Create JiraService instance with mock settings
        self.jira_service = JiraService(self.mock_settings, max_retries=3, retry_delay=0.1)
    
    def tearDown(self):
        """Clean up after each test method."""
        # Reset the jira_client to None
        self.jira_service.jira_client = None
    
    @patch('services.jira_service.JIRA')
    def test_get_client_creates_new_client(self, mock_jira_class):
        """Test that _get_client creates a new JIRA client."""
        mock_client = Mock()
        mock_jira_class.return_value = mock_client
        
        client = self.jira_service._get_client()
        
        # Verify JIRA client was created
        mock_jira_class.assert_called_once()
        self.assertEqual(client, mock_client)
        self.assertEqual(self.jira_service.jira_client, mock_client)
    
    @patch('services.jira_service.JIRA')
    def test_get_client_returns_cached_client(self, mock_jira_class):
        """Test that _get_client returns cached client on subsequent calls."""
        mock_client = Mock()
        self.jira_service.jira_client = mock_client
        
        client = self.jira_service._get_client()
        
        # Verify JIRA client was not created again
        mock_jira_class.assert_not_called()
        self.assertEqual(client, mock_client)
    
    @patch('services.jira_service.JIRA')
    def test_get_client_detects_jira_cloud(self, mock_jira_class):
        """Test that _get_client detects JIRA Cloud instances."""
        self.mock_settings.jira_url = "https://example.atlassian.net"
        mock_client = Mock()
        mock_jira_class.return_value = mock_client
        
        client = self.jira_service._get_client()
        
        # Verify JIRA client was created with token_auth
        mock_jira_class.assert_called_once_with(
            server="https://example.atlassian.net",
            token_auth="test_token_123"
        )
    
    def test_get_client_raises_error_without_url(self):
        """Test that _get_client raises ValueError without JIRA URL."""
        self.mock_settings.jira_url = ""
        
        with self.assertRaises(ValueError) as context:
            self.jira_service._get_client()
        
        self.assertIn("JIRA URL is not configured", str(context.exception))
    
    def test_get_client_raises_error_without_token(self):
        """Test that _get_client raises ValueError without PAT token."""
        self.mock_settings.jira_pat_token = ""
        
        with self.assertRaises(ValueError) as context:
            self.jira_service._get_client()
        
        self.assertIn("JIRA PAT token is not configured", str(context.exception))
    
    @patch('services.jira_service.JIRA')
    def test_test_connection_success(self, mock_jira_class):
        """Test successful connection test."""
        mock_client = Mock()
        mock_client.server_info.return_value = {'version': '8.20.0'}
        mock_client.current_user.return_value = 'test_user'
        mock_jira_class.return_value = mock_client
        
        result = self.jira_service.test_connection()
        
        self.assertTrue(result)
        mock_client.server_info.assert_called_once()
        mock_client.current_user.assert_called_once()
    
    @patch('services.jira_service.JIRA')
    def test_test_connection_failure(self, mock_jira_class):
        """Test connection test failure."""
        from jira.exceptions import JIRAError
        
        mock_client = Mock()
        mock_client.server_info.side_effect = JIRAError(status_code=401, text="Unauthorized")
        mock_jira_class.return_value = mock_client
        
        result = self.jira_service.test_connection()
        
        self.assertFalse(result)
    
    @patch('services.jira_service.JIRA')
    def test_get_new_tickets_success(self, mock_jira_class):
        """Test successful fetching of new tickets."""
        # Create mock JIRA issues
        mock_issue1 = self._create_mock_jira_issue("PROJ-123", "Test ticket 1")
        mock_issue2 = self._create_mock_jira_issue("PROJ-124", "Test ticket 2")
        
        mock_client = Mock()
        mock_client.search_issues.return_value = [mock_issue1, mock_issue2]
        mock_jira_class.return_value = mock_client
        
        tickets = self.jira_service.get_new_tickets(max_results=10)
        
        self.assertEqual(len(tickets), 2)
        self.assertIsInstance(tickets[0], Ticket)
        self.assertEqual(tickets[0].key, "PROJ-123")
        self.assertEqual(tickets[1].key, "PROJ-124")
        
        # Verify search_issues was called with correct parameters
        mock_client.search_issues.assert_called_once_with(
            self.mock_settings.jira_queue_jql,
            maxResults=10,
            fields='summary,description,comment,attachment,created,reporter,priority,assignee'
        )
    
    @patch('services.jira_service.JIRA')
    def test_get_new_tickets_empty_result(self, mock_jira_class):
        """Test fetching new tickets with empty result."""
        mock_client = Mock()
        mock_client.search_issues.return_value = []
        mock_jira_class.return_value = mock_client
        
        tickets = self.jira_service.get_new_tickets()
        
        self.assertEqual(len(tickets), 0)
    
    @patch('services.jira_service.JIRA')
    def test_get_ticket_by_key_success(self, mock_jira_class):
        """Test successful fetching of a specific ticket."""
        mock_issue = self._create_mock_jira_issue("PROJ-123", "Test ticket")
        
        mock_client = Mock()
        mock_client.issue.return_value = mock_issue
        mock_jira_class.return_value = mock_client
        
        ticket = self.jira_service.get_ticket_by_key("PROJ-123")
        
        self.assertIsNotNone(ticket)
        self.assertIsInstance(ticket, Ticket)
        self.assertEqual(ticket.key, "PROJ-123")
        
        mock_client.issue.assert_called_once_with(
            "PROJ-123",
            fields='summary,description,comment,attachment,created,reporter,priority,assignee'
        )
    
    @patch('services.jira_service.JIRA')
    def test_get_ticket_by_key_not_found(self, mock_jira_class):
        """Test fetching a non-existent ticket."""
        from jira.exceptions import JIRAError
        
        mock_client = Mock()
        mock_client.issue.side_effect = JIRAError(status_code=404, text="Issue not found")
        mock_jira_class.return_value = mock_client
        
        ticket = self.jira_service.get_ticket_by_key("PROJ-999")
        
        self.assertIsNone(ticket)
    
    @patch('services.jira_service.JIRA')
    def test_get_ticket_comments_success(self, mock_jira_class):
        """Test successful fetching of ticket comments."""
        mock_comment1 = Mock()
        mock_comment1.body = "First comment"
        mock_comment2 = Mock()
        mock_comment2.body = "Second comment"
        
        mock_client = Mock()
        mock_client.comments.return_value = [mock_comment1, mock_comment2]
        mock_jira_class.return_value = mock_client
        
        comments = self.jira_service.get_ticket_comments("PROJ-123")
        
        self.assertEqual(len(comments), 2)
        self.assertEqual(comments[0], "First comment")
        self.assertEqual(comments[1], "Second comment")
        
        mock_client.comments.assert_called_once_with("PROJ-123")
    
    @patch('services.jira_service.JIRA')
    def test_get_ticket_attachments_success(self, mock_jira_class):
        """Test successful fetching of ticket attachments."""
        mock_attachment1 = Mock()
        mock_attachment1.filename = "file1.txt"
        mock_attachment1.size = 1024
        mock_attachment1.mimeType = "text/plain"
        mock_attachment1.created = "2026-06-10T10:30:00.000+0000"
        mock_attachment1.author.displayName = "John Doe"
        
        mock_attachment2 = Mock()
        mock_attachment2.filename = "file2.pdf"
        mock_attachment2.size = 2048
        mock_attachment2.mimeType = "application/pdf"
        mock_attachment2.created = "2026-06-10T11:00:00.000+0000"
        mock_attachment2.author.displayName = "Jane Smith"
        
        mock_issue = Mock()
        mock_issue.fields.attachment = [mock_attachment1, mock_attachment2]
        
        mock_client = Mock()
        mock_client.issue.return_value = mock_issue
        mock_jira_class.return_value = mock_client
        
        attachments = self.jira_service.get_ticket_attachments("PROJ-123")
        
        self.assertEqual(len(attachments), 2)
        self.assertEqual(attachments[0]['filename'], "file1.txt")
        self.assertEqual(attachments[0]['size'], 1024)
        self.assertEqual(attachments[1]['filename'], "file2.pdf")
        self.assertEqual(attachments[1]['author'], "Jane Smith")
    
    @patch('services.jira_service.JIRA')
    def test_assign_ticket_success(self, mock_jira_class):
        """Test successful ticket assignment."""
        mock_client = Mock()
        mock_client.assign_issue.return_value = None
        mock_jira_class.return_value = mock_client
        
        result = self.jira_service.assign_ticket("PROJ-123", "john.doe")
        
        self.assertTrue(result)
        mock_client.assign_issue.assert_called_once_with("PROJ-123", "john.doe")
    
    @patch('services.jira_service.JIRA')
    def test_assign_ticket_failure(self, mock_jira_class):
        """Test ticket assignment failure."""
        from jira.exceptions import JIRAError
        
        mock_client = Mock()
        mock_client.assign_issue.side_effect = JIRAError(status_code=400, text="Invalid user")
        mock_jira_class.return_value = mock_client
        
        with self.assertRaises(JIRAError):
            self.jira_service.assign_ticket("PROJ-123", "invalid_user")
    
    @patch('services.jira_service.JIRA')
    def test_add_comment_success(self, mock_jira_class):
        """Test successful comment addition."""
        mock_client = Mock()
        mock_client.add_comment.return_value = None
        mock_jira_class.return_value = mock_client
        
        result = self.jira_service.add_comment("PROJ-123", "Test comment")
        
        self.assertTrue(result)
        mock_client.add_comment.assert_called_once_with("PROJ-123", "Test comment")
    
    @patch('services.jira_service.JIRA')
    def test_update_ticket_field_success(self, mock_jira_class):
        """Test successful field update."""
        mock_issue = Mock()
        mock_issue.update.return_value = None
        
        mock_client = Mock()
        mock_client.issue.return_value = mock_issue
        mock_jira_class.return_value = mock_client
        
        result = self.jira_service.update_ticket_field("PROJ-123", "customfield_10001", "High Priority")
        
        self.assertTrue(result)
        mock_client.issue.assert_called_once_with("PROJ-123")
        mock_issue.update.assert_called_once_with(fields={"customfield_10001": "High Priority"})
    
    @patch('services.jira_service.JIRA')
    @patch('services.jira_service.time.sleep')
    def test_retry_on_failure_with_transient_error(self, mock_sleep, mock_jira_class):
        """Test retry logic with transient errors."""
        from jira.exceptions import JIRAError
        
        mock_client = Mock()
        # First two calls fail with 500, third succeeds
        mock_client.search_issues.side_effect = [
            JIRAError(status_code=500, text="Server error"),
            JIRAError(status_code=500, text="Server error"),
            []
        ]
        mock_jira_class.return_value = mock_client
        
        tickets = self.jira_service.get_new_tickets()
        
        # Verify it retried and eventually succeeded
        self.assertEqual(len(tickets), 0)
        self.assertEqual(mock_client.search_issues.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # Two retries
    
    @patch('services.jira_service.JIRA')
    def test_retry_on_failure_with_auth_error(self, mock_jira_class):
        """Test that authentication errors are not retried."""
        from jira.exceptions import JIRAError
        
        mock_client = Mock()
        mock_client.search_issues.side_effect = JIRAError(status_code=401, text="Unauthorized")
        mock_jira_class.return_value = mock_client
        
        with self.assertRaises(JIRAError) as context:
            self.jira_service.get_new_tickets()
        
        # Verify it didn't retry
        self.assertEqual(mock_client.search_issues.call_count, 1)
        self.assertEqual(context.exception.status_code, 401)
    
    @patch('services.jira_service.JIRA')
    def test_retry_on_failure_with_not_found_error(self, mock_jira_class):
        """Test that 404 errors are not retried."""
        from jira.exceptions import JIRAError
        
        mock_client = Mock()
        mock_client.issue.side_effect = JIRAError(status_code=404, text="Not found")
        mock_jira_class.return_value = mock_client
        
        # Should return None instead of raising
        ticket = self.jira_service.get_ticket_by_key("PROJ-999")
        
        # Verify it didn't retry
        self.assertEqual(mock_client.issue.call_count, 1)
        self.assertIsNone(ticket)
    
    @patch('services.jira_service.JIRA')
    @patch('services.jira_service.time.sleep')
    def test_retry_on_failure_exhausts_retries(self, mock_sleep, mock_jira_class):
        """Test that retry logic exhausts all attempts."""
        from jira.exceptions import JIRAError
        
        mock_client = Mock()
        # All calls fail
        mock_client.search_issues.side_effect = JIRAError(status_code=500, text="Server error")
        mock_jira_class.return_value = mock_client
        
        with self.assertRaises(JIRAError):
            self.jira_service.get_new_tickets()
        
        # Verify it tried max_retries times
        self.assertEqual(mock_client.search_issues.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # max_retries - 1
    
    @patch('services.jira_service.JIRA')
    def test_get_queue_statistics_success(self, mock_jira_class):
        """Test successful queue statistics retrieval."""
        # Create mock issues with different priorities and statuses
        mock_issue1 = self._create_mock_jira_issue("PROJ-123", "Ticket 1", priority="High")
        mock_issue2 = self._create_mock_jira_issue("PROJ-124", "Ticket 2", priority="High")
        mock_issue3 = self._create_mock_jira_issue("PROJ-125", "Ticket 3", priority="Medium")
        
        # Add status to mock issues
        mock_issue1.fields.status = Mock()
        mock_issue1.fields.status.name = "Open"
        mock_issue2.fields.status = Mock()
        mock_issue2.fields.status.name = "In Progress"
        mock_issue3.fields.status = Mock()
        mock_issue3.fields.status.name = "Open"
        
        mock_client = Mock()
        mock_client.search_issues.return_value = [mock_issue1, mock_issue2, mock_issue3]
        mock_jira_class.return_value = mock_client
        
        stats = self.jira_service.get_queue_statistics()
        
        self.assertEqual(stats['total_tickets'], 3)
        self.assertEqual(stats['by_priority']['High'], 2)
        self.assertEqual(stats['by_priority']['Medium'], 1)
        self.assertEqual(stats['by_status']['Open'], 2)
        self.assertEqual(stats['by_status']['In Progress'], 1)
        self.assertIn('average_age_days', stats)
    
    def test_parse_jira_issue(self):
        """Test parsing JIRA issue to Ticket."""
        mock_issue = self._create_mock_jira_issue("PROJ-123", "Test ticket")
        
        ticket = self.jira_service.parse_jira_issue(mock_issue)
        
        self.assertIsInstance(ticket, Ticket)
        self.assertEqual(ticket.key, "PROJ-123")
        self.assertEqual(ticket.summary, "Test ticket")
    
    def _create_mock_jira_issue(self, key, summary, priority="Medium"):
        """Helper method to create a mock JIRA issue."""
        mock_issue = Mock()
        mock_issue.key = key
        mock_issue.fields = Mock()
        mock_issue.fields.summary = summary
        mock_issue.fields.description = "Test description"
        mock_issue.fields.created = "2026-06-10T10:30:00.000+0000"
        
        # Mock priority
        mock_issue.fields.priority = Mock()
        mock_issue.fields.priority.name = priority
        
        # Mock reporter
        mock_issue.fields.reporter = Mock()
        mock_issue.fields.reporter.displayName = "Test User"
        
        # Mock comments
        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = []
        
        # Mock attachments
        mock_issue.fields.attachment = []
        
        return mock_issue


if __name__ == '__main__':
    unittest.main()


# Made with Bob