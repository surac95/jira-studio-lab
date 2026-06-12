"""
Ticket model for JIRA automation system.

This module defines the Ticket class that represents a JIRA issue
with all relevant properties and methods for processing.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional


class Ticket:
    """
    Represents a JIRA ticket with all relevant information.
    
    This class encapsulates ticket data and provides methods for
    conversion and content extraction for AI analysis.
    
    Attributes:
        key: JIRA ticket key (e.g., 'PROJ-123')
        summary: Brief description of the ticket
        description: Detailed description of the issue
        comments: List of comments on the ticket
        attachments: List of attachment filenames
        created_date: When the ticket was created
        reporter: Username of the person who created the ticket
        priority: Priority level (e.g., 'High', 'Medium', 'Low')
    """
    
    def __init__(
        self,
        key: str,
        summary: str,
        description: str = "",
        comments: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        created_date: Optional[datetime] = None,
        reporter: str = "",
        priority: str = "Medium"
    ):
        """
        Initialize a Ticket instance.
        
        Args:
            key: JIRA ticket key
            summary: Brief description of the ticket
            description: Detailed description (default: empty string)
            comments: List of comments (default: empty list)
            attachments: List of attachments (default: empty list)
            created_date: Creation timestamp (default: current time)
            reporter: Reporter username (default: empty string)
            priority: Priority level (default: 'Medium')
        """
        self.key = key
        self.summary = summary
        self.description = description or ""
        self.comments = comments or []
        self.attachments = attachments or []
        self.created_date = created_date or datetime.now()
        self.reporter = reporter
        self.priority = priority
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ticket to dictionary representation.
        
        Returns:
            Dictionary containing all ticket properties
        """
        return {
            'key': self.key,
            'summary': self.summary,
            'description': self.description,
            'comments': self.comments,
            'attachments': self.attachments,
            'created_date': self.created_date.isoformat(),
            'reporter': self.reporter,
            'priority': self.priority
        }
    
    @classmethod
    def from_jira_issue(cls, jira_issue: Any) -> 'Ticket':
        """
        Create a Ticket instance from a JIRA issue object.
        
        This method extracts relevant fields from the JIRA API response
        and creates a Ticket instance.
        
        Args:
            jira_issue: JIRA issue object from the JIRA API
            
        Returns:
            Ticket instance populated with data from the JIRA issue
            
        Raises:
            AttributeError: If required fields are missing from jira_issue
        """
        # Extract basic fields
        key = jira_issue.key
        summary = jira_issue.fields.summary
        description = getattr(jira_issue.fields, 'description', '') or ''
        
        # Extract comments
        comments = []
        if hasattr(jira_issue.fields, 'comment') and jira_issue.fields.comment:
            comments = [
                comment.body 
                for comment in jira_issue.fields.comment.comments
            ]
        
        # Extract attachments
        attachments = []
        if hasattr(jira_issue.fields, 'attachment') and jira_issue.fields.attachment:
            attachments = [
                attachment.filename 
                for attachment in jira_issue.fields.attachment
            ]
        
        # Extract created date
        created_date = None
        if hasattr(jira_issue.fields, 'created'):
            try:
                # JIRA returns ISO format datetime strings
                created_date = datetime.fromisoformat(
                    jira_issue.fields.created.replace('Z', '+00:00')
                )
            except (ValueError, AttributeError):
                created_date = datetime.now()
        
        # Extract reporter
        reporter = ""
        if hasattr(jira_issue.fields, 'reporter') and jira_issue.fields.reporter:
            reporter = getattr(jira_issue.fields.reporter, 'displayName', '') or \
                      getattr(jira_issue.fields.reporter, 'name', '')
        
        # Extract priority
        priority = "Medium"
        if hasattr(jira_issue.fields, 'priority') and jira_issue.fields.priority:
            priority = jira_issue.fields.priority.name
        
        return cls(
            key=key,
            summary=summary,
            description=description,
            comments=comments,
            attachments=attachments,
            created_date=created_date,
            reporter=reporter,
            priority=priority
        )
    
    def get_full_content(self) -> str:
        """
        Combine summary, description, and comments for AI analysis.
        
        This method creates a comprehensive text representation of the ticket
        that can be used for AI-based categorization and analysis.
        
        Returns:
            Combined string containing all ticket text content
        """
        content_parts = []
        
        # Add summary
        if self.summary:
            content_parts.append(f"Summary: {self.summary}")
        
        # Add description
        if self.description:
            content_parts.append(f"Description: {self.description}")
        
        # Add comments
        if self.comments:
            comments_text = "\n".join([f"- {comment}" for comment in self.comments])
            content_parts.append(f"Comments:\n{comments_text}")
        
        # Add attachment info if present
        if self.attachments:
            attachments_text = ", ".join(self.attachments)
            content_parts.append(f"Attachments: {attachments_text}")
        
        return "\n\n".join(content_parts)
    
    def __repr__(self) -> str:
        """String representation of the Ticket."""
        return f"Ticket(key='{self.key}', summary='{self.summary[:50]}...', priority='{self.priority}')"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.key}: {self.summary}"

# Made with Bob
