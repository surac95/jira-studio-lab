"""
JIRA API integration service for JIRA automation system.

This module provides the JiraService class that handles all interactions
with the JIRA Server instance, including authentication, ticket fetching,
assignment, and updates.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from jira import JIRA
from jira.exceptions import JIRAError

from models.ticket import Ticket
from config.settings import Settings
from utils.logger import get_logger


class JiraService:
    """
    Service class for interacting with JIRA Server API.
    
    This class provides methods for:
    - Connection and authentication testing
    - Fetching tickets from queues
    - Assigning tickets to team members
    - Adding comments and updating fields
    - Retrieving ticket metadata (comments, attachments)
    
    The service includes retry logic for transient failures and
    comprehensive error handling.
    
    Attributes:
        settings: Settings instance containing JIRA configuration
        jira_client: JIRA client instance (cached after first connection)
        logger: Logger instance for this service
        max_retries: Maximum number of retry attempts for failed requests
        retry_delay: Initial delay between retries (exponential backoff)
    """
    
    def __init__(self, settings: Settings, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize JiraService with settings and configuration.
        
        Args:
            settings: Settings instance with JIRA configuration
            max_retries: Maximum retry attempts for failed requests (default: 3)
            retry_delay: Initial delay in seconds between retries (default: 1.0)
            
        Example:
            >>> from config import get_settings
            >>> settings = get_settings()
            >>> jira_service = JiraService(settings)
        """
        self.settings = settings
        self.jira_client: Optional[JIRA] = None
        self.logger = get_logger(__name__)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.logger.info("JiraService initialized")
    
    def _get_client(self) -> JIRA:
        """
        Get or create JIRA client instance.
        
        Creates a new JIRA client if one doesn't exist, otherwise returns
        the cached client. Uses PAT token authentication.
        
        Returns:
            JIRA client instance
            
        Raises:
            ValueError: If JIRA URL or PAT token is not configured
            JIRAError: If connection to JIRA fails
        """
        if self.jira_client is not None:
            return self.jira_client
        
        # Validate required settings
        if not self.settings.jira_url:
            raise ValueError("JIRA URL is not configured")
        if not self.settings.jira_pat_token:
            raise ValueError("JIRA PAT token is not configured")
        
        try:
            self.logger.info(f"Connecting to JIRA at {self.settings.jira_url}")
            
            # Determine if this is JIRA Server or Cloud based on URL
            is_cloud = 'atlassian.net' in self.settings.jira_url.lower()
            
            # Create JIRA client with PAT token authentication
            # For JIRA Server, use token_auth
            # For JIRA Cloud, PAT tokens work with basic_auth using email
            if is_cloud:
                self.logger.info("Detected JIRA Cloud instance")
                # For Cloud, PAT tokens are used with basic auth (email, token)
                # However, if only PAT is provided, we use token_auth
                self.jira_client = JIRA(
                    server=self.settings.jira_url,
                    token_auth=self.settings.jira_pat_token
                )
            else:
                self.logger.info("Detected JIRA Server instance")
                # For Server, use token_auth with PAT
                self.jira_client = JIRA(
                    server=self.settings.jira_url,
                    token_auth=self.settings.jira_pat_token
                )
            
            self.logger.info("Successfully connected to JIRA")
            return self.jira_client
            
        except JIRAError as e:
            self.logger.error(f"Failed to connect to JIRA: {e.text}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error connecting to JIRA: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test JIRA connection and authentication.
        
        Attempts to connect to JIRA and retrieve server information
        to verify that authentication is working correctly.
        
        Returns:
            True if connection is successful, False otherwise
            
        Example:
            >>> jira_service = JiraService(settings)
            >>> if jira_service.test_connection():
            ...     print("Connected to JIRA successfully")
        """
        try:
            client = self._get_client()
            
            # Try to get server info to verify connection
            server_info = client.server_info()
            self.logger.info(f"Connected to JIRA Server version {server_info.get('version', 'unknown')}")
            
            # Try to get current user to verify authentication
            current_user = client.current_user()
            self.logger.info(f"Authenticated as user: {current_user}")
            
            return True
            
        except JIRAError as e:
            self.logger.error(f"JIRA connection test failed: {e.text}")
            return False
        except Exception as e:
            self.logger.error(f"Connection test failed with unexpected error: {str(e)}")
            return False
    
    def _retry_on_failure(self, func, *args, **kwargs) -> Any:
        """
        Execute a function with retry logic for transient failures.
        
        Implements exponential backoff retry strategy for handling
        temporary network issues or rate limiting.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except JIRAError as e:
                last_exception = e
                
                # Don't retry on authentication or permission errors
                if e.status_code in [401, 403]:
                    self.logger.error(f"Authentication/Permission error: {e.text}")
                    raise
                
                # Don't retry on not found errors
                if e.status_code == 404:
                    self.logger.error(f"Resource not found: {e.text}")
                    raise
                
                # Retry on rate limiting or server errors
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e.text}. "
                        f"Retrying in {delay} seconds..."
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(f"All retry attempts failed: {e.text}")
                    raise
            except Exception as e:
                last_exception = e
                self.logger.error(f"Unexpected error: {str(e)}")
                raise
        
        # This should not be reached, but just in case
        if last_exception:
            raise last_exception
    
    def get_new_tickets(self, max_results: int = 50) -> List[Ticket]:
        """
        Fetch new unassigned tickets from L3/L4 queue using JQL query.
        
        Retrieves tickets based on the configured JQL query in settings.
        Typically fetches unassigned tickets from the support queue.
        
        Args:
            max_results: Maximum number of tickets to fetch (default: 50)
            
        Returns:
            List of Ticket objects representing the fetched tickets
            
        Raises:
            JIRAError: If the JQL query is invalid or JIRA API fails
            
        Example:
            >>> tickets = jira_service.get_new_tickets(max_results=10)
            >>> for ticket in tickets:
            ...     print(f"{ticket.key}: {ticket.summary}")
        """
        try:
            self.logger.info(f"Fetching new tickets with JQL: {self.settings.jira_queue_jql}")
            
            client = self._get_client()
            
            # Execute JQL query with retry logic
            jira_issues = self._retry_on_failure(
                client.search_issues,
                self.settings.jira_queue_jql,
                maxResults=max_results,
                fields='summary,description,comment,attachment,created,reporter,priority,assignee'
            )
            
            # Convert JIRA issues to Ticket objects
            tickets = []
            for jira_issue in jira_issues:
                try:
                    ticket = Ticket.from_jira_issue(jira_issue)
                    tickets.append(ticket)
                except Exception as e:
                    self.logger.error(f"Failed to parse ticket {jira_issue.key}: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully fetched {len(tickets)} tickets")
            return tickets
            
        except JIRAError as e:
            self.logger.error(f"Failed to fetch tickets: {e.text}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error fetching tickets: {str(e)}")
            raise
    
    def get_ticket_by_key(self, ticket_key: str) -> Optional[Ticket]:
        """
        Fetch a specific ticket by its key.
        
        Args:
            ticket_key: JIRA ticket key (e.g., 'PROJ-123')
            
        Returns:
            Ticket object if found, None if ticket doesn't exist
            
        Raises:
            JIRAError: If JIRA API fails (except for 404 not found)
            
        Example:
            >>> ticket = jira_service.get_ticket_by_key("PROJ-123")
            >>> if ticket:
            ...     print(f"Found ticket: {ticket.summary}")
        """
        try:
            self.logger.info(f"Fetching ticket: {ticket_key}")
            
            client = self._get_client()
            
            # Fetch issue with retry logic
            jira_issue = self._retry_on_failure(
                client.issue,
                ticket_key,
                fields='summary,description,comment,attachment,created,reporter,priority,assignee'
            )
            
            # Convert to Ticket object
            ticket = Ticket.from_jira_issue(jira_issue)
            
            self.logger.info(f"Successfully fetched ticket {ticket_key}")
            return ticket
            
        except JIRAError as e:
            if e.status_code == 404:
                self.logger.warning(f"Ticket {ticket_key} not found")
                return None
            self.logger.error(f"Failed to fetch ticket {ticket_key}: {e.text}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error fetching ticket {ticket_key}: {str(e)}")
            raise
    
    def get_ticket_comments(self, ticket_key: str) -> List[str]:
        """
        Get all comments for a ticket.
        
        Args:
            ticket_key: JIRA ticket key (e.g., 'PROJ-123')
            
        Returns:
            List of comment text strings
            
        Raises:
            JIRAError: If ticket doesn't exist or JIRA API fails
            
        Example:
            >>> comments = jira_service.get_ticket_comments("PROJ-123")
            >>> for comment in comments:
            ...     print(f"Comment: {comment}")
        """
        try:
            self.logger.info(f"Fetching comments for ticket: {ticket_key}")
            
            client = self._get_client()
            
            # Fetch comments with retry logic
            comments = self._retry_on_failure(
                client.comments,
                ticket_key
            )
            
            # Extract comment text
            comment_texts = [comment.body for comment in comments]
            
            self.logger.info(f"Successfully fetched {len(comment_texts)} comments for {ticket_key}")
            return comment_texts
            
        except JIRAError as e:
            self.logger.error(f"Failed to fetch comments for {ticket_key}: {e.text}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error fetching comments for {ticket_key}: {str(e)}")
            raise
    
    def get_ticket_attachments(self, ticket_key: str) -> List[Dict[str, Any]]:
        """
        Get attachment metadata for a ticket.
        
        Args:
            ticket_key: JIRA ticket key (e.g., 'PROJ-123')
            
        Returns:
            List of dictionaries containing attachment metadata:
            - filename: Name of the attachment
            - size: Size in bytes
            - mimeType: MIME type of the file
            - created: Creation timestamp
            - author: Username of who uploaded it
            
        Raises:
            JIRAError: If ticket doesn't exist or JIRA API fails
            
        Example:
            >>> attachments = jira_service.get_ticket_attachments("PROJ-123")
            >>> for att in attachments:
            ...     print(f"File: {att['filename']} ({att['size']} bytes)")
        """
        try:
            self.logger.info(f"Fetching attachments for ticket: {ticket_key}")
            
            client = self._get_client()
            
            # Fetch issue with attachments
            jira_issue = self._retry_on_failure(
                client.issue,
                ticket_key,
                fields='attachment'
            )
            
            # Extract attachment metadata
            attachments = []
            if hasattr(jira_issue.fields, 'attachment') and jira_issue.fields.attachment:
                for attachment in jira_issue.fields.attachment:
                    attachments.append({
                        'filename': attachment.filename,
                        'size': attachment.size,
                        'mimeType': attachment.mimeType,
                        'created': attachment.created,
                        'author': attachment.author.displayName if hasattr(attachment.author, 'displayName') else 'Unknown'
                    })
            
            self.logger.info(f"Successfully fetched {len(attachments)} attachments for {ticket_key}")
            return attachments
            
        except JIRAError as e:
            self.logger.error(f"Failed to fetch attachments for {ticket_key}: {e.text}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error fetching attachments for {ticket_key}: {str(e)}")
            raise
    
    def assign_ticket(self, ticket_key: str, assignee_username: str) -> bool:
        """
        Assign a ticket to a team member.
        
        Args:
            ticket_key: JIRA ticket key (e.g., 'PROJ-123')
            assignee_username: JIRA username of the assignee
            
        Returns:
            True if assignment was successful, False otherwise
            
        Raises:
            JIRAError: If ticket doesn't exist, user is invalid, or JIRA API fails
            
        Example:
            >>> success = jira_service.assign_ticket("PROJ-123", "john.doe")
            >>> if success:
            ...     print("Ticket assigned successfully")
        """
        try:
            self.logger.info(f"Assigning ticket {ticket_key} to {assignee_username}")
            
            client = self._get_client()
            
            # Assign ticket with retry logic
            self._retry_on_failure(
                client.assign_issue,
                ticket_key,
                assignee_username
            )
            
            self.logger.info(f"Successfully assigned {ticket_key} to {assignee_username}")
            return True
            
        except JIRAError as e:
            self.logger.error(f"Failed to assign {ticket_key} to {assignee_username}: {e.text}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error assigning {ticket_key}: {str(e)}")
            raise
    
    def add_comment(self, ticket_key: str, comment_text: str) -> bool:
        """
        Add a comment to a ticket.
        
        Args:
            ticket_key: JIRA ticket key (e.g., 'PROJ-123')
            comment_text: Text content of the comment
            
        Returns:
            True if comment was added successfully, False otherwise
            
        Raises:
            JIRAError: If ticket doesn't exist or JIRA API fails
            
        Example:
            >>> success = jira_service.add_comment(
            ...     "PROJ-123",
            ...     "Assigned to John for TRIRIGA expertise"
            ... )
        """
        try:
            self.logger.info(f"Adding comment to ticket {ticket_key}")
            
            client = self._get_client()
            
            # Add comment with retry logic
            self._retry_on_failure(
                client.add_comment,
                ticket_key,
                comment_text
            )
            
            self.logger.info(f"Successfully added comment to {ticket_key}")
            return True
            
        except JIRAError as e:
            self.logger.error(f"Failed to add comment to {ticket_key}: {e.text}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error adding comment to {ticket_key}: {str(e)}")
            raise
    
    def update_ticket_field(self, ticket_key: str, field_name: str, value: Any) -> bool:
        """
        Update a custom field on a ticket.
        
        Args:
            ticket_key: JIRA ticket key (e.g., 'PROJ-123')
            field_name: Name of the field to update
            value: New value for the field
            
        Returns:
            True if field was updated successfully, False otherwise
            
        Raises:
            JIRAError: If ticket doesn't exist, field is invalid, or JIRA API fails
            
        Example:
            >>> success = jira_service.update_ticket_field(
            ...     "PROJ-123",
            ...     "customfield_10001",
            ...     "High Priority"
            ... )
        """
        try:
            self.logger.info(f"Updating field '{field_name}' on ticket {ticket_key}")
            
            client = self._get_client()
            
            # Get the issue first
            issue = self._retry_on_failure(client.issue, ticket_key)
            
            # Update the field with retry logic
            self._retry_on_failure(
                issue.update,
                fields={field_name: value}
            )
            
            self.logger.info(f"Successfully updated field '{field_name}' on {ticket_key}")
            return True
            
        except JIRAError as e:
            self.logger.error(f"Failed to update field '{field_name}' on {ticket_key}: {e.text}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error updating field on {ticket_key}: {str(e)}")
            raise
    
    def parse_jira_issue(self, jira_issue: Any) -> Ticket:
        """
        Convert JIRA issue object to Ticket model.
        
        This is a convenience method that delegates to Ticket.from_jira_issue().
        
        Args:
            jira_issue: JIRA issue object from the JIRA API
            
        Returns:
            Ticket instance populated with data from the JIRA issue
            
        Raises:
            AttributeError: If required fields are missing from jira_issue
            
        Example:
            >>> jira_issue = client.issue("PROJ-123")
            >>> ticket = jira_service.parse_jira_issue(jira_issue)
        """
        try:
            return Ticket.from_jira_issue(jira_issue)
        except Exception as e:
            self.logger.error(f"Failed to parse JIRA issue: {str(e)}")
            raise
    
    def get_queue_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the queue.
        
        Provides information about:
        - Total number of tickets in queue
        - Breakdown by priority
        - Breakdown by status
        - Average age of tickets
        
        Returns:
            Dictionary containing queue statistics
            
        Example:
            >>> stats = jira_service.get_queue_statistics()
            >>> print(f"Total tickets: {stats['total_tickets']}")
            >>> print(f"High priority: {stats['by_priority']['High']}")
        """
        try:
            self.logger.info("Fetching queue statistics")
            
            client = self._get_client()
            
            # Fetch all tickets from queue
            jira_issues = self._retry_on_failure(
                client.search_issues,
                self.settings.jira_queue_jql,
                maxResults=1000,  # Get more for statistics
                fields='priority,status,created'
            )
            
            # Calculate statistics
            total_tickets = len(jira_issues)
            
            # Count by priority
            by_priority: Dict[str, int] = {}
            for issue in jira_issues:
                if hasattr(issue.fields, 'priority') and issue.fields.priority:
                    priority = issue.fields.priority.name
                    by_priority[priority] = by_priority.get(priority, 0) + 1
            
            # Count by status
            by_status: Dict[str, int] = {}
            for issue in jira_issues:
                if hasattr(issue.fields, 'status') and issue.fields.status:
                    status = issue.fields.status.name
                    by_status[status] = by_status.get(status, 0) + 1
            
            # Calculate average age
            from datetime import datetime, timezone
            total_age_days = 0
            for issue in jira_issues:
                if hasattr(issue.fields, 'created'):
                    try:
                        created = datetime.fromisoformat(
                            issue.fields.created.replace('Z', '+00:00')
                        )
                        age = (datetime.now(timezone.utc) - created).days
                        total_age_days += age
                    except (ValueError, AttributeError):
                        continue
            
            avg_age_days = total_age_days / total_tickets if total_tickets > 0 else 0
            
            statistics = {
                'total_tickets': total_tickets,
                'by_priority': by_priority,
                'by_status': by_status,
                'average_age_days': round(avg_age_days, 1)
            }
            
            self.logger.info(f"Queue statistics: {total_tickets} tickets, avg age {avg_age_days:.1f} days")
            return statistics
            
        except JIRAError as e:
            self.logger.error(f"Failed to fetch queue statistics: {e.text}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error fetching queue statistics: {str(e)}")
            raise


# Made with Bob