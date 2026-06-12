"""
Unit tests for the Ticket model.

This module contains comprehensive tests for the Ticket class,
including initialization, conversion methods, and content extraction.
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, MagicMock
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.ticket import Ticket


class TestTicket(unittest.TestCase):
    """Test cases for the Ticket class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_key = "PROJ-123"
        self.test_summary = "Test ticket summary"
        self.test_description = "This is a test description"
        self.test_comments = ["Comment 1", "Comment 2"]
        self.test_attachments = ["file1.txt", "file2.pdf"]
        self.test_created_date = datetime(2026, 6, 10, 10, 30, 0)
        self.test_reporter = "john.doe"
        self.test_priority = "High"
    
    def test_ticket_initialization_with_all_params(self):
        """Test ticket initialization with all parameters."""
        ticket = Ticket(
            key=self.test_key,
            summary=self.test_summary,
            description=self.test_description,
            comments=self.test_comments,
            attachments=self.test_attachments,
            created_date=self.test_created_date,
            reporter=self.test_reporter,
            priority=self.test_priority
        )
        
        self.assertEqual(ticket.key, self.test_key)
        self.assertEqual(ticket.summary, self.test_summary)
        self.assertEqual(ticket.description, self.test_description)
        self.assertEqual(ticket.comments, self.test_comments)
        self.assertEqual(ticket.attachments, self.test_attachments)
        self.assertEqual(ticket.created_date, self.test_created_date)
        self.assertEqual(ticket.reporter, self.test_reporter)
        self.assertEqual(ticket.priority, self.test_priority)
    
    def test_ticket_initialization_with_defaults(self):
        """Test ticket initialization with default values."""
        ticket = Ticket(
            key=self.test_key,
            summary=self.test_summary
        )
        
        self.assertEqual(ticket.key, self.test_key)
        self.assertEqual(ticket.summary, self.test_summary)
        self.assertEqual(ticket.description, "")
        self.assertEqual(ticket.comments, [])
        self.assertEqual(ticket.attachments, [])
        self.assertIsInstance(ticket.created_date, datetime)
        self.assertEqual(ticket.reporter, "")
        self.assertEqual(ticket.priority, "Medium")
    
    def test_to_dict(self):
        """Test conversion of ticket to dictionary."""
        ticket = Ticket(
            key=self.test_key,
            summary=self.test_summary,
            description=self.test_description,
            comments=self.test_comments,
            attachments=self.test_attachments,
            created_date=self.test_created_date,
            reporter=self.test_reporter,
            priority=self.test_priority
        )
        
        ticket_dict = ticket.to_dict()
        
        self.assertEqual(ticket_dict['key'], self.test_key)
        self.assertEqual(ticket_dict['summary'], self.test_summary)
        self.assertEqual(ticket_dict['description'], self.test_description)
        self.assertEqual(ticket_dict['comments'], self.test_comments)
        self.assertEqual(ticket_dict['attachments'], self.test_attachments)
        self.assertEqual(ticket_dict['created_date'], self.test_created_date.isoformat())
        self.assertEqual(ticket_dict['reporter'], self.test_reporter)
        self.assertEqual(ticket_dict['priority'], self.test_priority)
    
    def test_from_jira_issue_complete(self):
        """Test creating ticket from JIRA issue with all fields."""
        # Create mock JIRA issue
        mock_issue = Mock()
        mock_issue.key = self.test_key
        mock_issue.fields = Mock()
        mock_issue.fields.summary = self.test_summary
        mock_issue.fields.description = self.test_description
        
        # Mock comments
        mock_comment1 = Mock()
        mock_comment1.body = "Comment 1"
        mock_comment2 = Mock()
        mock_comment2.body = "Comment 2"
        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = [mock_comment1, mock_comment2]
        
        # Mock attachments
        mock_attachment1 = Mock()
        mock_attachment1.filename = "file1.txt"
        mock_attachment2 = Mock()
        mock_attachment2.filename = "file2.pdf"
        mock_issue.fields.attachment = [mock_attachment1, mock_attachment2]
        
        # Mock created date
        mock_issue.fields.created = "2026-06-10T10:30:00+00:00"
        
        # Mock reporter
        mock_issue.fields.reporter = Mock()
        mock_issue.fields.reporter.displayName = "John Doe"
        
        # Mock priority
        mock_issue.fields.priority = Mock()
        mock_issue.fields.priority.name = "High"
        
        # Create ticket from mock issue
        ticket = Ticket.from_jira_issue(mock_issue)
        
        self.assertEqual(ticket.key, self.test_key)
        self.assertEqual(ticket.summary, self.test_summary)
        self.assertEqual(ticket.description, self.test_description)
        self.assertEqual(len(ticket.comments), 2)
        self.assertEqual(len(ticket.attachments), 2)
        self.assertEqual(ticket.reporter, "John Doe")
        self.assertEqual(ticket.priority, "High")
    
    def test_from_jira_issue_minimal(self):
        """Test creating ticket from JIRA issue with minimal fields."""
        # Create mock JIRA issue with only required fields
        mock_issue = Mock()
        mock_issue.key = self.test_key
        mock_issue.fields = Mock()
        mock_issue.fields.summary = self.test_summary
        mock_issue.fields.description = None
        mock_issue.fields.comment = None
        mock_issue.fields.attachment = None
        mock_issue.fields.reporter = None
        mock_issue.fields.priority = None
        
        # Create ticket from mock issue
        ticket = Ticket.from_jira_issue(mock_issue)
        
        self.assertEqual(ticket.key, self.test_key)
        self.assertEqual(ticket.summary, self.test_summary)
        self.assertEqual(ticket.description, "")
        self.assertEqual(ticket.comments, [])
        self.assertEqual(ticket.attachments, [])
        self.assertEqual(ticket.reporter, "")
        self.assertEqual(ticket.priority, "Medium")
    
    def test_get_full_content_complete(self):
        """Test getting full content with all fields populated."""
        ticket = Ticket(
            key=self.test_key,
            summary=self.test_summary,
            description=self.test_description,
            comments=self.test_comments,
            attachments=self.test_attachments
        )
        
        content = ticket.get_full_content()
        
        self.assertIn(self.test_summary, content)
        self.assertIn(self.test_description, content)
        self.assertIn("Comment 1", content)
        self.assertIn("Comment 2", content)
        self.assertIn("file1.txt", content)
        self.assertIn("file2.pdf", content)
    
    def test_get_full_content_minimal(self):
        """Test getting full content with minimal fields."""
        ticket = Ticket(
            key=self.test_key,
            summary=self.test_summary
        )
        
        content = ticket.get_full_content()
        
        self.assertIn(self.test_summary, content)
        self.assertNotIn("Description:", content)
        self.assertNotIn("Comments:", content)
        self.assertNotIn("Attachments:", content)
    
    def test_get_full_content_with_empty_description(self):
        """Test getting full content when description is empty."""
        ticket = Ticket(
            key=self.test_key,
            summary=self.test_summary,
            description=""
        )
        
        content = ticket.get_full_content()
        
        self.assertIn(self.test_summary, content)
        self.assertNotIn("Description:", content)
    
    def test_repr(self):
        """Test string representation of ticket."""
        ticket = Ticket(
            key=self.test_key,
            summary=self.test_summary,
            priority=self.test_priority
        )
        
        repr_str = repr(ticket)
        
        self.assertIn(self.test_key, repr_str)
        self.assertIn(self.test_priority, repr_str)
        self.assertIn("Ticket", repr_str)
    
    def test_str(self):
        """Test human-readable string representation."""
        ticket = Ticket(
            key=self.test_key,
            summary=self.test_summary
        )
        
        str_repr = str(ticket)
        
        self.assertIn(self.test_key, str_repr)
        self.assertIn(self.test_summary, str_repr)
    
    def test_none_description_handling(self):
        """Test that None description is converted to empty string."""
        ticket = Ticket(
            key=self.test_key,
            summary=self.test_summary,
            description=None
        )
        
        self.assertEqual(ticket.description, "")
    
    def test_none_lists_handling(self):
        """Test that None lists are converted to empty lists."""
        ticket = Ticket(
            key=self.test_key,
            summary=self.test_summary,
            comments=None,
            attachments=None
        )
        
        self.assertEqual(ticket.comments, [])
        self.assertEqual(ticket.attachments, [])


if __name__ == '__main__':
    unittest.main()

# Made with Bob
