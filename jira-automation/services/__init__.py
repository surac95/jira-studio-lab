"""
Services package for JIRA automation system.

This package contains service classes for interacting with external systems:
- JiraService: JIRA API integration
- AIService: Mistral AI integration for ticket classification and summarization
- SlackService: Slack notifications
- WorkloadService: Team workload management
"""

from services.jira_service import JiraService
from services.ai_service import AIService
from services.slack_service import SlackService
from services.workload_service import WorkloadService

__all__ = ['JiraService', 'AIService', 'SlackService', 'WorkloadService']

# Made with Bob
