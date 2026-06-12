"""
Slack notification service for JIRA automation system.

This module provides Slack integration for sending ticket notifications,
error alerts, and daily summaries to team channels.
"""

import time
from typing import Dict, Any, List, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from config.settings import Settings
from models.ticket import Ticket
from models.team_member import TeamMember
from utils.logger import get_logger


class SlackService:
    """
    Service for sending notifications to Slack channels.
    
    This service provides methods for sending formatted notifications about
    ticket assignments, errors, and daily summaries using Slack's Block Kit.
    
    Attributes:
        settings: Application settings instance
        client: Slack WebClient instance
        channel_id: Slack channel ID for notifications
        logger: Logger instance for this service
    """
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    RETRY_BACKOFF = 2  # exponential backoff multiplier
    
    # Urgency emoji mapping
    URGENCY_EMOJI = {
        'low': '🟢',
        'medium': '🟡',
        'high': '🔴'
    }
    
    # Category emoji mapping
    CATEGORY_EMOJI = {
        'TRIRIGA': '🏢',
        'APIC': '🔌',
        'APPC': '💻'
    }
    
    def __init__(self, settings: Settings):
        """
        Initialize the Slack service with bot token and channel.
        
        Args:
            settings: Settings instance containing Slack configuration
            
        Raises:
            ValueError: If Slack bot token or channel ID is not configured
        """
        self.settings = settings
        self.logger = get_logger(__name__)
        
        # Validate configuration
        if not settings.slack_bot_token:
            raise ValueError("Slack bot token is not configured")
        if not settings.slack_channel_id:
            raise ValueError("Slack channel ID is not configured")
        
        self.channel_id = settings.slack_channel_id
        
        # Initialize Slack client
        try:
            self.client = WebClient(token=settings.slack_bot_token)
            self.logger.info("Slack client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Slack client: {e}")
            raise
    
    def send_ticket_notification(
        self,
        ticket: Ticket,
        analysis: Dict[str, Any],
        assignee: TeamMember
    ) -> bool:
        """
        Send a formatted notification about a new ticket assignment.
        
        Creates a rich Slack message with ticket details, AI analysis,
        and assignee information using Slack Block Kit.
        
        Args:
            ticket: Ticket object with ticket details
            analysis: AI analysis dictionary containing:
                - category: Classification category
                - confidence: Confidence score
                - summary: AI-generated summary
                - key_points: List of key points
                - urgency: Urgency level
            assignee: TeamMember object for the assigned team member
            
        Returns:
            True if notification sent successfully, False otherwise
            
        Example:
            >>> slack_service = SlackService(settings)
            >>> ticket = Ticket(key="PROJ-123", summary="Issue")
            >>> analysis = {"category": "TRIRIGA", "confidence": 0.95, ...}
            >>> assignee = TeamMember(name="John Doe", ...)
            >>> slack_service.send_ticket_notification(ticket, analysis, assignee)
        """
        self.logger.info(f"Sending ticket notification for {ticket.key}")
        
        try:
            # Format the message
            blocks = self._format_ticket_message(ticket, analysis, assignee)
            
            # Send with retry logic
            response = self._send_message_with_retry(
                channel=self.channel_id,
                blocks=blocks,
                text=f"New ticket assigned: {ticket.key}"  # Fallback text
            )
            
            if response:
                self.logger.info(
                    f"Ticket notification sent successfully for {ticket.key}"
                )
                return True
            else:
                self.logger.error(
                    f"Failed to send ticket notification for {ticket.key}"
                )
                return False
                
        except Exception as e:
            self.logger.error(
                f"Error sending ticket notification for {ticket.key}: {e}"
            )
            return False
    
    def send_error_notification(
        self,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send an error alert notification to the Slack channel.
        
        Args:
            error_message: Description of the error
            context: Optional dictionary with additional context information
            
        Returns:
            True if notification sent successfully, False otherwise
            
        Example:
            >>> slack_service = SlackService(settings)
            >>> slack_service.send_error_notification(
            ...     "Failed to process ticket",
            ...     {"ticket_key": "PROJ-123", "error": "API timeout"}
            ... )
        """
        self.logger.info("Sending error notification")
        
        try:
            # Format the error message
            blocks = self._format_error_message(error_message, context)
            
            # Send with retry logic
            response = self._send_message_with_retry(
                channel=self.channel_id,
                blocks=blocks,
                text=f"Error: {error_message}"  # Fallback text
            )
            
            if response:
                self.logger.info("Error notification sent successfully")
                return True
            else:
                self.logger.error("Failed to send error notification")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")
            return False
    
    def send_daily_summary(self, statistics: Dict[str, Any]) -> bool:
        """
        Send a daily summary of tickets processed and assignments made.
        
        Args:
            statistics: Dictionary containing summary statistics:
                - tickets_processed: Number of tickets processed
                - tickets_assigned: Number of tickets assigned
                - by_category: Breakdown by category
                - team_capacity: Team capacity information
                
        Returns:
            True if notification sent successfully, False otherwise
            
        Example:
            >>> slack_service = SlackService(settings)
            >>> stats = {
            ...     "tickets_processed": 15,
            ...     "tickets_assigned": 12,
            ...     "by_category": {"TRIRIGA": 5, "APIC": 4, "APPC": 3}
            ... }
            >>> slack_service.send_daily_summary(stats)
        """
        self.logger.info("Sending daily summary")
        
        try:
            # Format the summary message
            blocks = self._format_daily_summary(statistics)
            
            # Send with retry logic
            response = self._send_message_with_retry(
                channel=self.channel_id,
                blocks=blocks,
                text="Daily Summary"  # Fallback text
            )
            
            if response:
                self.logger.info("Daily summary sent successfully")
                return True
            else:
                self.logger.error("Failed to send daily summary")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending daily summary: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test the Slack connection by calling the auth.test API.
        
        Returns:
            True if connection is successful, False otherwise
            
        Example:
            >>> slack_service = SlackService(settings)
            >>> if slack_service.test_connection():
            ...     print("Slack connection OK")
        """
        try:
            self.logger.info("Testing Slack connection")
            response = self.client.auth_test()
            
            if response['ok']:
                self.logger.info(
                    f"Slack connection successful. Bot: {response.get('user', 'unknown')}"
                )
                return True
            else:
                self.logger.error("Slack connection test failed")
                return False
                
        except SlackApiError as e:
            self.logger.error(f"Slack API error during connection test: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error testing Slack connection: {e}")
            return False
    
    def get_channel_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the configured Slack channel.
        
        Returns:
            Dictionary with channel information if successful, None otherwise
            
        Example:
            >>> slack_service = SlackService(settings)
            >>> info = slack_service.get_channel_info()
            >>> if info:
            ...     print(f"Channel: {info['name']}")
        """
        try:
            self.logger.info(f"Getting info for channel {self.channel_id}")
            response = self.client.conversations_info(channel=self.channel_id)
            
            if response['ok']:
                channel = response['channel']
                info = {
                    'id': channel['id'],
                    'name': channel.get('name', 'unknown'),
                    'is_channel': channel.get('is_channel', False),
                    'is_private': channel.get('is_private', False),
                    'num_members': channel.get('num_members', 0)
                }
                self.logger.info(f"Channel info retrieved: {info['name']}")
                return info
            else:
                self.logger.error("Failed to get channel info")
                return None
                
        except SlackApiError as e:
            self.logger.error(f"Slack API error getting channel info: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting channel info: {e}")
            return None
    
    def _format_ticket_message(
        self,
        ticket: Ticket,
        analysis: Dict[str, Any],
        assignee: TeamMember
    ) -> List[Dict[str, Any]]:
        """
        Format a ticket notification message using Slack Block Kit.
        
        Args:
            ticket: Ticket object
            analysis: AI analysis dictionary
            assignee: TeamMember object
            
        Returns:
            List of Slack block dictionaries
        """
        category = analysis.get('category', 'UNKNOWN')
        confidence = analysis.get('confidence', 0.0)
        urgency = analysis.get('urgency', 'medium')
        summary = analysis.get('summary', ticket.summary)
        key_points = analysis.get('key_points', [])
        
        # Get emoji indicators
        urgency_emoji = self.URGENCY_EMOJI.get(urgency, '⚪')
        category_emoji = self.CATEGORY_EMOJI.get(category, '📋')
        
        # Build JIRA URL
        jira_url = f"{self.settings.jira_url}/browse/{ticket.key}"
        
        # Build blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎫 New Ticket Assigned: {ticket.key}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Ticket:*\n<{jira_url}|{ticket.key}>"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Assigned To:*\n{assignee.name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Category:*\n{category_emoji} {category}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Urgency:*\n{urgency_emoji} {urgency.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Confidence:*\n{confidence:.0%}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Priority:*\n{ticket.priority}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{ticket.summary}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*AI Analysis:*\n{summary}"
                }
            }
        ]
        
        # Add key points if available
        if key_points:
            key_points_text = "\n".join([f"• {point}" for point in key_points])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Key Points:*\n{key_points_text}"
                }
            })
        
        # Add divider
        blocks.append({"type": "divider"})
        
        # Add interactive buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔍 Get Deep Analysis",
                        "emoji": True
                    },
                    "action_id": "deep_analysis",
                    "value": ticket.key,
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 View in JIRA",
                        "emoji": True
                    },
                    "url": jira_url,
                    "action_id": "view_jira"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔄 Re-analyze",
                        "emoji": True
                    },
                    "action_id": "reanalyze",
                    "value": ticket.key
                }
            ]
        })
        
        return blocks
    
    def _format_error_message(
        self,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Format an error notification message using Slack Block Kit.
        
        Args:
            error_message: Error description
            context: Optional context dictionary
            
        Returns:
            List of Slack block dictionaries
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⚠️ Error Alert",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error:*\n```{error_message}```"
                }
            }
        ]
        
        # Add context if provided
        if context:
            context_text = "\n".join([
                f"*{key}:* {value}"
                for key, value in context.items()
            ])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Context:*\n{context_text}"
                }
            })
        
        blocks.append({"type": "divider"})
        
        return blocks
    
    def _format_daily_summary(
        self,
        statistics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Format a daily summary message using Slack Block Kit.
        
        Args:
            statistics: Statistics dictionary
            
        Returns:
            List of Slack block dictionaries
        """
        tickets_processed = statistics.get('tickets_processed', 0)
        tickets_assigned = statistics.get('tickets_assigned', 0)
        by_category = statistics.get('by_category', {})
        team_capacity = statistics.get('team_capacity', {})
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Daily Summary",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Tickets Processed:*\n{tickets_processed}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Tickets Assigned:*\n{tickets_assigned}"
                    }
                ]
            }
        ]
        
        # Add category breakdown if available
        if by_category:
            category_text = "\n".join([
                f"{self.CATEGORY_EMOJI.get(cat, '📋')} *{cat}:* {count}"
                for cat, count in by_category.items()
            ])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*By Category:*\n{category_text}"
                }
            })
        
        # Add team capacity if available
        if team_capacity:
            capacity_pct = team_capacity.get('capacity_percentage', 0)
            used = team_capacity.get('used_capacity', 0)
            total = team_capacity.get('total_capacity', 0)
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Team Capacity:*\n{used}/{total} ({capacity_pct:.1f}%)"
                }
            })
        
        blocks.append({"type": "divider"})
        
        return blocks
    
    def _send_message_with_retry(
        self,
        channel: str,
        blocks: List[Dict[str, Any]],
        text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Send a Slack message with retry logic for transient failures.
        
        Args:
            channel: Channel ID to send to
            blocks: List of Slack block dictionaries
            text: Fallback text for notifications
            
        Returns:
            Response dictionary if successful, None otherwise
        """
        last_exception: Optional[Exception] = None
        delay = self.RETRY_DELAY
        
        for attempt in range(self.MAX_RETRIES):
            try:
                self.logger.debug(
                    f"Sending Slack message (attempt {attempt + 1}/{self.MAX_RETRIES})"
                )
                
                response = self.client.chat_postMessage(
                    channel=channel,
                    blocks=blocks,
                    text=text
                )
                
                if response['ok']:
                    self.logger.debug("Slack message sent successfully")
                    return response
                else:
                    raise ValueError(f"Slack API returned ok=False: {response}")
                    
            except SlackApiError as e:
                last_exception = e
                
                # Check if error is retryable
                if e.response.status_code == 429:  # Rate limit
                    retry_after = int(e.response.headers.get('Retry-After', delay))
                    self.logger.warning(
                        f"Rate limited. Retrying after {retry_after} seconds"
                    )
                    time.sleep(retry_after)
                    continue
                elif e.response.status_code >= 500:  # Server error
                    self.logger.warning(
                        f"Slack server error (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}"
                    )
                else:
                    # Client error - don't retry
                    self.logger.error(f"Slack client error: {e}")
                    return None
                    
            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"Slack message failed (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}"
                )
            
            # Don't retry on the last attempt
            if attempt < self.MAX_RETRIES - 1:
                self.logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= self.RETRY_BACKOFF
        
        # All retries failed
        if last_exception:
            self.logger.error(f"All Slack retry attempts failed: {last_exception}")
        else:
            self.logger.error("All Slack retry attempts failed with unknown error")
        
        return None
    
    def __repr__(self) -> str:
        """String representation of SlackService."""
        return f"SlackService(channel_id='{self.channel_id}')"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"SlackService: channel {self.channel_id}"


# Made with Bob
    
    def send_deep_analysis_response(
        self,
        ticket_key: str,
        deep_analysis: Dict[str, Any],
        response_url: str
    ) -> bool:
        """
        Send deep analysis response to Slack using response_url.
        
        This method is called when a user clicks the "Get Deep Analysis" button.
        It sends a detailed analysis as a response to the button interaction.
        
        Args:
            ticket_key: JIRA ticket key
            deep_analysis: Deep analysis dictionary from AI service
            response_url: Slack response URL from button interaction
            
        Returns:
            True if response sent successfully, False otherwise
        """
        self.logger.info(f"Sending deep analysis response for {ticket_key}")
        
        try:
            # Format the deep analysis message
            blocks = self._format_deep_analysis(ticket_key, deep_analysis)
            
            # Send response using response_url
            import requests
            response = requests.post(
                response_url,
                json={
                    "replace_original": False,  # Post as new message
                    "blocks": blocks,
                    "text": f"Deep Analysis for {ticket_key}"
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.logger.info(f"Deep analysis response sent for {ticket_key}")
                return True
            else:
                self.logger.error(
                    f"Failed to send deep analysis: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending deep analysis response: {e}")
            return False
    
    def _format_deep_analysis(
        self,
        ticket_key: str,
        deep_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Format deep analysis message using Slack Block Kit.
        
        Args:
            ticket_key: JIRA ticket key
            deep_analysis: Deep analysis dictionary
            
        Returns:
            List of Slack block dictionaries
        """
        # Build JIRA URL
        jira_url = f"{self.settings.jira_url}/browse/{ticket_key}"
        
        # Extract analysis components
        root_cause = deep_analysis.get('root_cause', 'Analysis in progress...')
        solutions = deep_analysis.get('solutions', [])
        impact = deep_analysis.get('impact', 'Not assessed')
        next_steps = deep_analysis.get('next_steps', [])
        estimated_time = deep_analysis.get('estimated_resolution_time', 'Unknown')
        
        # Build blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🤖 AI Deep Analysis: {ticket_key}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔍 Root Cause Analysis:*\n{root_cause}"
                }
            }
        ]
        
        # Add solutions if available
        if solutions:
            solutions_text = "\n".join([
                f"{i+1}. {sol}" for i, sol in enumerate(solutions)
            ])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*💡 Recommended Solutions:*\n{solutions_text}"
                }
            })
        
        # Add impact assessment
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*⚠️ Impact Assessment:*\n{impact}"
            }
        })
        
        # Add next steps if available
        if next_steps:
            steps_text = "\n".join([
                f"• {step}" for step in next_steps
            ])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🎯 Next Steps:*\n{steps_text}"
                }
            })
        
        # Add estimated resolution time
        blocks.append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*📊 Estimated Resolution:*\n{estimated_time}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*💰 Analysis Cost:*\n~$0.004"
                }
            ]
        })
        
        # Add divider and action buttons
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 View in JIRA",
                        "emoji": True
                    },
                    "url": jira_url,
                    "action_id": "view_jira_from_analysis"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔄 Re-analyze",
                        "emoji": True
                    },
                    "action_id": "reanalyze_deep",
                    "value": ticket_key
                }
            ]
        })
        
        return blocks
