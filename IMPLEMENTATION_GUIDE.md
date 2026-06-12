# Implementation Guide
## JIRA Incident Ticket Automation System

This guide provides step-by-step instructions for implementing the AI-powered JIRA ticket automation system based on the architecture defined in [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## Table of Contents

1. [Implementation Phases](#implementation-phases)
2. [Phase 1: Core Infrastructure](#phase-1-core-infrastructure)
3. [Phase 2: JIRA Integration](#phase-2-jira-integration)
4. [Phase 3: AI Services](#phase-3-ai-services)
5. [Phase 4: Assignment Logic](#phase-4-assignment-logic)
6. [Phase 5: Slack Integration](#phase-5-slack-integration)
7. [Phase 6: Integration & Testing](#phase-6-integration--testing)
8. [Phase 7: Deployment](#phase-7-deployment)
9. [Code Examples](#code-examples)
10. [Testing Checklist](#testing-checklist)

---

## Implementation Phases

The implementation is divided into 7 phases, each building upon the previous:

```
Phase 1: Core Infrastructure (Configuration, Logging, Models)
    ↓
Phase 2: JIRA Integration (API client, ticket fetching)
    ↓
Phase 3: AI Services (Classification, Summarization)
    ↓
Phase 4: Assignment Logic (Workload management)
    ↓
Phase 5: Slack Integration (Notifications)
    ↓
Phase 6: Integration & Testing (End-to-end workflow)
    ↓
Phase 7: Deployment (Production setup)
```

**Estimated Timeline**: 2-3 weeks for full implementation

---

## Phase 1: Core Infrastructure

**Duration**: 2-3 days  
**Goal**: Set up project structure, configuration management, logging, and data models

### Step 1.1: Project Setup

```bash
# Create project directory
mkdir jira-automation
cd jira-automation

# Initialize git repository
git init

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Create directory structure
mkdir -p config services models utils tests logs
touch config/__init__.py services/__init__.py models/__init__.py utils/__init__.py tests/__init__.py
```

### Step 1.2: Create requirements.txt

```txt
# Core Dependencies
jira==3.5.2
mistralai==0.1.0
slack-sdk==3.23.0
requests==2.31.0
python-dotenv==1.0.0

# Data Handling
pydantic==2.5.0

# Development Dependencies
pytest==7.4.3
pytest-mock==3.12.0
pytest-cov==4.1.0
pylint==3.0.3
black==23.12.1
mypy==1.7.1
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### Step 1.3: Implement Configuration Manager

**File**: [`config/config.py`](config/config.py)

```python
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Centralized configuration management"""
    
    # JIRA Configuration
    JIRA_SERVER_URL: str = os.getenv("JIRA_SERVER_URL", "")
    JIRA_PAT_TOKEN: str = os.getenv("JIRA_PAT_TOKEN", "")
    JIRA_QUEUE_FILTER: str = os.getenv("JIRA_QUEUE_FILTER", "L3/L4")
    JIRA_PROJECT_KEY: str = os.getenv("JIRA_PROJECT_KEY", "PROJ")
    
    # Mistral AI Configuration
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    MISTRAL_MODEL: str = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
    MISTRAL_MAX_TOKENS: int = int(os.getenv("MISTRAL_MAX_TOKENS", "1000"))
    MISTRAL_TEMPERATURE: float = float(os.getenv("MISTRAL_TEMPERATURE", "0.3"))
    
    # Slack Configuration
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_CHANNEL_ID: str = os.getenv("SLACK_CHANNEL_ID", "")
    SLACK_ERROR_CHANNEL_ID: Optional[str] = os.getenv("SLACK_ERROR_CHANNEL_ID")
    
    # Team Configuration
    TEAM_CONFIG_PATH: str = os.getenv("TEAM_CONFIG_PATH", "config/team.json")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/automation.log")
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", "10485760"))
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # Execution Configuration
    DRY_RUN: bool = os.getenv("DRY_RUN", "false").lower() == "true"
    MAX_TICKETS_PER_RUN: int = int(os.getenv("MAX_TICKETS_PER_RUN", "50"))
    
    @classmethod
    def validate(cls) -> None:
        """Validate all required configuration is present"""
        required_fields = {
            "JIRA_SERVER_URL": cls.JIRA_SERVER_URL,
            "JIRA_PAT_TOKEN": cls.JIRA_PAT_TOKEN,
            "MISTRAL_API_KEY": cls.MISTRAL_API_KEY,
            "SLACK_BOT_TOKEN": cls.SLACK_BOT_TOKEN,
            "SLACK_CHANNEL_ID": cls.SLACK_CHANNEL_ID,
        }
        
        missing = [key for key, value in required_fields.items() if not value]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
    
    @classmethod
    def get_jql_query(cls) -> str:
        """Build JQL query for fetching unassigned tickets"""
        return f"""
            project = {cls.JIRA_PROJECT_KEY}
            AND status IN ("Open", "New", "To Do")
            AND assignee is EMPTY
            AND (labels = "L3" OR labels = "L4")
            AND created >= -1h
            ORDER BY priority DESC, created ASC
        """
```

### Step 1.4: Implement Logger

**File**: [`utils/logger.py`](utils/logger.py)

```python
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config.config import Config

def setup_logger(name: str = "jira_automation") -> logging.Logger:
    """Configure and return logger instance"""
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(detailed_formatter)
    
    # File handler with rotation
    log_file = Path(Config.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        Config.LOG_FILE,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Create default logger
logger = setup_logger()
```

### Step 1.5: Implement Data Models

**File**: [`models/ticket.py`](models/ticket.py)

```python
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class Attachment:
    """Represents a ticket attachment"""
    filename: str
    size: int
    content_type: str
    url: str

@dataclass
class Comment:
    """Represents a ticket comment"""
    author: str
    body: str
    created: datetime

@dataclass
class Ticket:
    """Represents a JIRA ticket"""
    id: str
    key: str
    summary: str
    description: str
    priority: str
    status: str
    created: datetime
    updated: datetime
    comments: List[Comment] = field(default_factory=list)
    attachments: List[Attachment] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    
    def get_full_content(self) -> str:
        """Combine all ticket content for AI processing"""
        content = f"Summary: {self.summary}\n\n"
        content += f"Description: {self.description or 'No description'}\n\n"
        
        if self.comments:
            content += "Recent Comments:\n"
            for comment in self.comments[-5:]:  # Last 5 comments
                content += f"- {comment.author}: {comment.body}\n"
            content += "\n"
        
        if self.attachments:
            content += f"Attachments ({len(self.attachments)} files):\n"
            for att in self.attachments:
                content += f"- {att.filename} ({att.content_type})\n"
        
        return content

@dataclass
class TeamMember:
    """Represents a team member"""
    username: str
    name: str
    email: str
    specializations: List[str]
    max_tickets: int = 10
    active: bool = True

@dataclass
class Classification:
    """Represents AI classification result"""
    category: str  # TRIRIGA, APIC, or APPC
    confidence: float
    reasoning: Optional[str] = None
    
    def is_confident(self, threshold: float = 0.7) -> bool:
        """Check if classification confidence meets threshold"""
        return self.confidence >= threshold
```

**Deliverables for Phase 1**:
- ✅ Project structure created
- ✅ Configuration management implemented
- ✅ Logging system configured
- ✅ Data models defined
- ✅ Dependencies installed

---

## Phase 2: JIRA Integration

**Duration**: 3-4 days  
**Goal**: Implement JIRA API client for fetching and updating tickets

### Step 2.1: Implement JIRA Service

**File**: [`services/jira_service.py`](services/jira_service.py)

```python
from typing import List, Dict, Optional
from jira import JIRA
from jira.exceptions import JIRAError
from datetime import datetime

from models.ticket import Ticket, Comment, Attachment
from config.config import Config
from utils.logger import logger

class JiraService:
    """Service for JIRA API interactions"""
    
    def __init__(self):
        """Initialize JIRA client with PAT authentication"""
        try:
            self.client = JIRA(
                server=Config.JIRA_SERVER_URL,
                token_auth=Config.JIRA_PAT_TOKEN
            )
            logger.info("JIRA client initialized successfully")
        except JIRAError as e:
            logger.error(f"Failed to initialize JIRA client: {e}")
            raise
    
    def get_unassigned_tickets(self) -> List[Ticket]:
        """
        Fetch unassigned tickets from L3/L4 queue
        
        Returns:
            List of Ticket objects
        """
        try:
            jql = Config.get_jql_query()
            logger.info(f"Fetching tickets with JQL: {jql}")
            
            issues = self.client.search_issues(
                jql,
                maxResults=Config.MAX_TICKETS_PER_RUN,
                fields='summary,description,priority,status,created,updated,comment,attachment,labels'
            )
            
            tickets = [self._convert_to_ticket(issue) for issue in issues]
            logger.info(f"Found {len(tickets)} unassigned tickets")
            
            return tickets
            
        except JIRAError as e:
            logger.error(f"Failed to fetch tickets: {e}")
            raise
    
    def _convert_to_ticket(self, issue) -> Ticket:
        """Convert JIRA issue to Ticket model"""
        
        # Parse comments
        comments = []
        if hasattr(issue.fields, 'comment') and issue.fields.comment.comments:
            for comment in issue.fields.comment.comments:
                comments.append(Comment(
                    author=comment.author.displayName,
                    body=comment.body,
                    created=datetime.strptime(comment.created, '%Y-%m-%dT%H:%M:%S.%f%z')
                ))
        
        # Parse attachments
        attachments = []
        if hasattr(issue.fields, 'attachment'):
            for att in issue.fields.attachment:
                attachments.append(Attachment(
                    filename=att.filename,
                    size=att.size,
                    content_type=att.mimeType,
                    url=att.content
                ))
        
        return Ticket(
            id=issue.id,
            key=issue.key,
            summary=issue.fields.summary,
            description=issue.fields.description or "",
            priority=issue.fields.priority.name,
            status=issue.fields.status.name,
            created=datetime.strptime(issue.fields.created, '%Y-%m-%dT%H:%M:%S.%f%z'),
            updated=datetime.strptime(issue.fields.updated, '%Y-%m-%dT%H:%M:%S.%f%z'),
            comments=comments,
            attachments=attachments,
            labels=issue.fields.labels or []
        )
    
    def assign_ticket(self, ticket_key: str, assignee_username: str) -> bool:
        """
        Assign ticket to team member
        
        Args:
            ticket_key: JIRA ticket key (e.g., PROJ-123)
            assignee_username: Username of assignee
            
        Returns:
            True if successful, False otherwise
        """
        if Config.DRY_RUN:
            logger.info(f"[DRY RUN] Would assign {ticket_key} to {assignee_username}")
            return True
        
        try:
            issue = self.client.issue(ticket_key)
            issue.update(assignee={'name': assignee_username})
            logger.info(f"Assigned {ticket_key} to {assignee_username}")
            return True
            
        except JIRAError as e:
            logger.error(f"Failed to assign {ticket_key}: {e}")
            return False
    
    def add_comment(self, ticket_key: str, comment: str) -> bool:
        """
        Add comment to ticket
        
        Args:
            ticket_key: JIRA ticket key
            comment: Comment text
            
        Returns:
            True if successful, False otherwise
        """
        if Config.DRY_RUN:
            logger.info(f"[DRY RUN] Would add comment to {ticket_key}")
            return True
        
        try:
            self.client.add_comment(ticket_key, comment)
            logger.info(f"Added comment to {ticket_key}")
            return True
            
        except JIRAError as e:
            logger.error(f"Failed to add comment to {ticket_key}: {e}")
            return False
    
    def get_team_workload(self) -> Dict[str, int]:
        """
        Get current workload for all team members
        
        Returns:
            Dictionary mapping username to ticket count
        """
        try:
            # Query for assigned tickets in current sprint/period
            jql = f"""
                project = {Config.JIRA_PROJECT_KEY}
                AND status NOT IN ("Done", "Closed", "Resolved")
                AND assignee is not EMPTY
            """
            
            issues = self.client.search_issues(jql, maxResults=1000, fields='assignee')
            
            workload = {}
            for issue in issues:
                if issue.fields.assignee:
                    username = issue.fields.assignee.name
                    workload[username] = workload.get(username, 0) + 1
            
            logger.info(f"Current team workload: {workload}")
            return workload
            
        except JIRAError as e:
            logger.error(f"Failed to get team workload: {e}")
            return {}
```

### Step 2.2: Test JIRA Integration

**File**: [`tests/test_jira_service.py`](tests/test_jira_service.py)

```python
import pytest
from unittest.mock import Mock, patch
from services.jira_service import JiraService
from models.ticket import Ticket

@pytest.fixture
def jira_service():
    with patch('services.jira_service.JIRA'):
        return JiraService()

def test_get_unassigned_tickets(jira_service):
    # Mock JIRA response
    mock_issue = Mock()
    mock_issue.id = "12345"
    mock_issue.key = "PROJ-123"
    mock_issue.fields.summary = "Test ticket"
    mock_issue.fields.description = "Test description"
    mock_issue.fields.priority.name = "High"
    mock_issue.fields.status.name = "Open"
    mock_issue.fields.created = "2026-06-10T10:00:00.000+0000"
    mock_issue.fields.updated = "2026-06-10T10:00:00.000+0000"
    mock_issue.fields.comment.comments = []
    mock_issue.fields.attachment = []
    mock_issue.fields.labels = ["L3"]
    
    jira_service.client.search_issues = Mock(return_value=[mock_issue])
    
    tickets = jira_service.get_unassigned_tickets()
    
    assert len(tickets) == 1
    assert tickets[0].key == "PROJ-123"
    assert tickets[0].summary == "Test ticket"

def test_assign_ticket(jira_service):
    mock_issue = Mock()
    jira_service.client.issue = Mock(return_value=mock_issue)
    
    result = jira_service.assign_ticket("PROJ-123", "john.doe")
    
    assert result is True
    mock_issue.update.assert_called_once()
```

**Deliverables for Phase 2**:
- ✅ JIRA service implemented
- ✅ Ticket fetching working
- ✅ Ticket assignment working
- ✅ Workload retrieval working
- ✅ Unit tests passing

---

## Phase 3: AI Services

**Duration**: 3-4 days  
**Goal**: Implement Mistral AI integration for classification and summarization

### Step 3.1: Implement Mistral AI Service

**File**: [`services/mistral_service.py`](services/mistral_service.py)

```python
import json
from typing import Optional
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

from models.ticket import Ticket, Classification
from config.config import Config
from utils.logger import logger

class MistralAIService:
    """Service for Mistral AI interactions"""
    
    def __init__(self):
        """Initialize Mistral AI client"""
        self.client = MistralClient(api_key=Config.MISTRAL_API_KEY)
        self.model = Config.MISTRAL_MODEL
        logger.info("Mistral AI client initialized")
    
    def classify_ticket(self, ticket: Ticket) -> Classification:
        """
        Classify ticket into TRIRIGA, APIC, or APPC
        
        Args:
            ticket: Ticket object to classify
            
        Returns:
            Classification object with category and confidence
        """
        try:
            prompt = self._build_classification_prompt(ticket)
            
            messages = [
                ChatMessage(role="user", content=prompt)
            ]
            
            response = self.client.chat(
                model=self.model,
                messages=messages,
                temperature=Config.MISTRAL_TEMPERATURE,
                max_tokens=Config.MISTRAL_MAX_TOKENS
            )
            
            result = self._parse_classification_response(response.choices[0].message.content)
            
            logger.info(f"Classified {ticket.key} as {result.category} (confidence: {result.confidence})")
            return result
            
        except Exception as e:
            logger.error(f"Failed to classify ticket {ticket.key}: {e}")
            # Return default classification on error
            return Classification(category="APPC", confidence=0.5, reasoning="Classification failed")
    
    def _build_classification_prompt(self, ticket: Ticket) -> str:
        """Build prompt for ticket classification"""
        return f"""You are a support ticket classifier for an IT support team.

Classify the following ticket into exactly ONE category:

**TRIRIGA**: Real estate management, facility operations, space planning, building management, property management, lease management, workplace services

**APIC**: API connectivity issues, integration problems, web services, REST/SOAP APIs, API authentication, API endpoints, middleware, data synchronization

**APPC**: Application configuration, customization, user settings, permissions, roles, application setup, feature configuration, system preferences

Ticket Information:
- Key: {ticket.key}
- Summary: {ticket.summary}
- Description: {ticket.description[:500]}
- Priority: {ticket.priority}
- Labels: {', '.join(ticket.labels)}

{f"Recent Comments: {ticket.comments[-2:][0].body[:200] if ticket.comments else 'None'}" if ticket.comments else ""}

Respond with ONLY valid JSON in this exact format:
{{
  "classification": "TRIRIGA|APIC|APPC",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""
    
    def _parse_classification_response(self, response: str) -> Classification:
        """Parse AI response into Classification object"""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            data = json.loads(json_str)
            
            return Classification(
                category=data['classification'],
                confidence=float(data['confidence']),
                reasoning=data.get('reasoning')
            )
        except Exception as e:
            logger.error(f"Failed to parse classification response: {e}")
            return Classification(category="APPC", confidence=0.5, reasoning="Parse error")
    
    def summarize_ticket(self, ticket: Ticket) -> str:
        """
        Generate concise summary of ticket
        
        Args:
            ticket: Ticket object to summarize
            
        Returns:
            Summary string (2-3 sentences)
        """
        try:
            prompt = self._build_summarization_prompt(ticket)
            
            messages = [
                ChatMessage(role="user", content=prompt)
            ]
            
            response = self.client.chat(
                model=self.model,
                messages=messages,
                temperature=0.5,
                max_tokens=200
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"Generated summary for {ticket.key}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to summarize ticket {ticket.key}: {e}")
            return f"Summary unavailable. Please review ticket {ticket.key} for details."
    
    def _build_summarization_prompt(self, ticket: Ticket) -> str:
        """Build prompt for ticket summarization"""
        content = ticket.get_full_content()
        
        return f"""Summarize the following support ticket in 2-3 clear, concise sentences. Focus on:
1. The main issue or request
2. Key details that help understand the problem
3. Any important context from comments or attachments

Ticket Content:
{content[:1000]}

Provide a professional summary suitable for a team notification."""
```

**Deliverables for Phase 3**:
- ✅ Mistral AI service implemented
- ✅ Classification working with good accuracy
- ✅ Summarization generating useful summaries
- ✅ Error handling for API failures
- ✅ Unit tests passing

---

## Phase 4: Assignment Logic

**Duration**: 2-3 days  
**Goal**: Implement intelligent workload-based assignment

### Step 4.1: Implement Workload Manager

**File**: [`services/workload_manager.py`](services/workload_manager.py)

```python
import json
from typing import List, Dict, Optional
from pathlib import Path

from models.ticket import TeamMember, Classification
from services.jira_service import JiraService
from config.config import Config
from utils.logger import logger

class WorkloadManager:
    """Manages ticket assignment based on workload and specialization"""
    
    def __init__(self, jira_service: JiraService):
        """
        Initialize workload manager
        
        Args:
            jira_service: JiraService instance for workload queries
        """
        self.jira_service = jira_service
        self.team_members = self._load_team_config()
        logger.info(f"Loaded {len(self.team_members)} team members")
    
    def _load_team_config(self) -> List[TeamMember]:
        """Load team configuration from JSON file"""
        config_path = Path(Config.TEAM_CONFIG_PATH)
        
        if not config_path.exists():
            logger.error(f"Team config not found: {config_path}")
            raise FileNotFoundError(f"Team config not found: {config_path}")
        
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        members = []
        for member_data in data['members']:
            if member_data.get('active', True):
                members.append(TeamMember(**member_data))
        
        return members
    
    def get_best_assignee(self, classification: Classification) -> Optional[str]:
        """
        Determine best assignee based on specialization and workload
        
        Args:
            classification: Classification result for the ticket
            
        Returns:
            Username of best assignee, or None if no one available
        """
        category = classification.category
        
        # Filter by specialization
        specialized_members = [
            m for m in self.team_members 
            if category in m.specializations
        ]
        
        if not specialized_members:
            logger.warning(f"No team members specialized in {category}")
            specialized_members = self.team_members  # Fallback to all members
        
        # Get current workload
        workload = self.jira_service.get_team_workload()
        
        # Find member with lowest workload
        best_member = None
        lowest_load = float('inf')
        
        for member in specialized_members:
            current_load = workload.get(member.username, 0)
            
            # Check if member has capacity
            if current_load >= member.max_tickets:
                logger.debug(f"{member.username} at capacity ({current_load}/{member.max_tickets})")
                continue
            
            # Select member with lowest load
            if current_load < lowest_load:
                lowest_load = current_load
                best_member = member
        
        if best_member:
            logger.info(f"Selected {best_member.username} for {category} (current load: {lowest_load})")
            return best_member.username
        else:
            logger.warning(f"No available team members for {category}")
            return None
    
    def get_workload_summary(self) -> Dict[str, Dict]:
        """
        Get workload summary for all team members
        
        Returns:
            Dictionary with workload details per member
        """
        workload = self.jira_service.get_team_workload()
        
        summary = {}
        for member in self.team_members:
            current = workload.get(member.username, 0)
            summary[member.username] = {
                'name': member.name,
                'current_tickets': current,
                'max_tickets': member.max_tickets,
                'available_capacity': member.max_tickets - current,
                'specializations': member.specializations
            }
        
        return summary
```

**Deliverables for Phase 4**:
- ✅ Workload manager implemented
- ✅ Assignment algorithm working correctly
- ✅ Specialization matching functional
- ✅ Capacity limits respected
- ✅ Unit tests passing

---

## Phase 5: Slack Integration

**Duration**: 2 days  
**Goal**: Implement Slack notifications

### Step 5.1: Implement Slack Service

**File**: [`services/slack_service.py`](services/slack_service.py)

```python
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from models.ticket import Ticket, Classification
from config.config import Config
from utils.logger import logger

class SlackService:
    """Service for Slack notifications"""
    
    def __init__(self):
        """Initialize Slack client"""
        self.client = WebClient(token=Config.SLACK_BOT_TOKEN)
        self.channel_id = Config.SLACK_CHANNEL_ID
        logger.info("Slack client initialized")
    
    def send_notification(
        self,
        ticket: Ticket,
        classification: Classification,
        assignee: str,
        summary: str
    ) -> bool:
        """
        Send ticket assignment notification to Slack
        
        Args:
            ticket: Ticket object
            classification: Classification result
            assignee: Username of assignee
            summary: AI-generated summary
            
        Returns:
            True if successful, False otherwise
        """
        if Config.DRY_RUN:
            logger.info(f"[DRY RUN] Would send Slack notification for {ticket.key}")
            return True
        
        try:
            message = self._format_message(ticket, classification, assignee, summary)
            
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                text=f"New ticket assigned: {ticket.key}",
                blocks=message
            )
            
            logger.info(f"Sent Slack notification for {ticket.key}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def _format_message(
        self,
        ticket: Ticket,
        classification: Classification,
        assignee: str,
        summary: str
    ) -> list:
        """Format Slack message with blocks"""
        
        ticket_url = f"{Config.JIRA_SERVER_URL}/browse/{ticket.key}"
        
        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎫 New Ticket Assigned"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Ticket:*\n<{ticket_url}|{ticket.key}>"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Classification:*\n{classification.category}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Assigned To:*\n@{assignee}"
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
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_Automated by JIRA Ticket Bot • Confidence: {classification.confidence:.0%}_"
                    }
                ]
            }
        ]
    
    def send_error_notification(self, error_message: str) -> bool:
        """Send error alert to Slack"""
        if not Config.SLACK_ERROR_CHANNEL_ID:
            return False
        
        try:
            self.client.chat_postMessage(
                channel=Config.SLACK_ERROR_CHANNEL_ID,
                text=f"⚠️ JIRA Automation Error: {error_message}"
            )
            return True
        except SlackApiError as e:
            logger.error(f"Failed to send error notification: {e}")
            return False
```

**Deliverables for Phase 5**:
- ✅ Slack service implemented
- ✅ Notifications sending successfully
- ✅ Message formatting looks good
- ✅ Error notifications working
- ✅ Unit tests passing

---

## Phase 6: Integration & Testing

**Duration**: 3-4 days  
**Goal**: Integrate all components and test end-to-end

### Step 6.1: Implement Main Orchestrator

**File**: [`main.py`](main.py)

```python
#!/usr/bin/env python3
"""
JIRA Incident Ticket Automation System
Main orchestrator for ticket processing workflow
"""

import sys
import argparse
from typing import List

from config.config import Config
from services.jira_service import JiraService
from services.mistral_service import MistralAIService
from services.workload_manager import WorkloadManager
from services.slack_service import SlackService
from models.ticket import Ticket
from utils.logger import logger

def process_ticket(
    ticket: Ticket,
    jira_service: JiraService,
    ai_service: MistralAIService,
    workload_manager: WorkloadManager,
    slack_service: SlackService
) -> bool:
    """
    Process a single ticket through the automation pipeline
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Processing ticket {ticket.key}")
        
        # Step 1: Classify ticket
        classification = ai_service.classify_ticket(ticket)
        
        if not classification.is_confident():
            logger.warning(f"Low confidence classification for {ticket.key}: {classification.confidence}")
        
        # Step 2: Generate summary
        summary = ai_service.summarize_ticket(ticket)
        
        # Step 3: Get best assignee
        assignee = workload_manager.get_best_assignee(classification)
        
        if not assignee:
            logger.error(f"No available assignee for {ticket.key}")
            return False
        
        # Step 4: Assign ticket in JIRA
        if not jira_service.assign_ticket(ticket.key, assignee):
            logger.error(f"Failed to assign {ticket.key}")
            return False
        
        # Step 5: Add automation comment
        comment = f"Automatically classified as {classification.category} and assigned to {assignee}"
        jira_service.add_comment(ticket.key, comment)
        
        # Step 6: Send Slack notification
        slack_service.send_notification(ticket, classification, assignee, summary)
        
        logger.info(f"Successfully processed {ticket.key}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing ticket {ticket.key}: {e}", exc_info=True)
        return False

def main():
    """Main execution function"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='JIRA Ticket Automation')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()
    
    if args.dry_run:
        Config.DRY_RUN = True
        logger.info("Running in DRY RUN mode")
    
    if args.debug:
        Config.LOG_LEVEL = "DEBUG"
        logger.setLevel("DEBUG")
    
    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated successfully")
        
        # Initialize services
        logger.info("Initializing services...")
        jira_service = JiraService()
        ai_service = MistralAIService()
        workload_manager = WorkloadManager(jira_service)
        slack_service = SlackService()
        
        # Fetch unassigned tickets
        logger.info("Fetching unassigned tickets...")
        tickets = jira_service.get_unassigned_tickets()
        
        if not tickets:
            logger.info("No unassigned tickets found")
            return 0
        
        logger.info(f"Found {len(tickets)} tickets to process")
        
        # Process each ticket
        success_count = 0
        failure_count = 0
        
        for ticket in tickets:
            if process_ticket(ticket, jira_service, ai_service, workload_manager, slack_service):
                success_count += 1
            else:
                failure_count += 1
        
        # Log summary
        logger.info(f"Processing complete: {success_count} successful, {failure_count} failed")
        
        # Send summary to Slack if there were failures
        if failure_count > 0:
            slack_service.send_error_notification(
                f"Processed {len(tickets)} tickets: {success_count} successful, {failure_count} failed"
            )
        
        return 0 if failure_count == 0 else 1
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

**Deliverables for Phase 6**:
- ✅ Main orchestrator implemented
- ✅ End-to-end workflow functional
- ✅ Error handling comprehensive
- ✅ Integration tests passing
- ✅ Dry-run mode working

---

## Phase 7: Deployment

**Duration**: 2-3 days  
**Goal**: Deploy to production environment

### Step 7.1: Production Setup

Follow the deployment guide in [`ARCHITECTURE.md`](ARCHITECTURE.md) Section 10.

**Key Steps**:
1. Set up production server
2. Install dependencies
3. Configure environment variables
4. Set up systemd timer or cron
5. Configure log rotation
6. Test in production
7. Monitor initial runs

**Deliverables for Phase 7**:
- ✅ Application deployed to production
- ✅ Cron/timer configured and running
- ✅ Monitoring in place
- ✅ Documentation complete
- ✅ Team trained on system

---

## Code Examples

### Example: Complete Workflow Test

```python
def test_complete_workflow():
    """Test the complete ticket processing workflow"""
    
    # Setup
    jira_service = JiraService()
    ai_service = MistralAIService()
    workload_manager = WorkloadManager(jira_service)
    slack_service = SlackService()
    
    # Get tickets
    tickets = jira_service.get_unassigned_tickets()
    assert len(tickets) > 0
    
    # Process first ticket
    ticket = tickets[0]
    
    # Classify
    classification = ai_service.classify_ticket(ticket)
    assert classification.category in ["TRIRIGA", "APIC", "APPC"]
    
    # Summarize
    summary = ai_service.summarize_ticket(ticket)
    assert len(summary) > 0
    
    # Assign
    assignee = workload_manager.get_best_assignee(classification)
    assert assignee is not None
    
    # Update JIRA
    success = jira_service.assign_ticket(ticket.key, assignee)
    assert success is True
    
    # Notify
    success = slack_service.send_notification(ticket, classification, assignee, summary)
    assert success is True
```

---

## Testing Checklist

### Unit Tests
- [ ] Config validation
- [ ] Logger initialization
- [ ] Data model creation
- [ ] JIRA ticket fetching
- [ ] JIRA ticket assignment
- [ ] AI classification
- [ ] AI summarization
- [ ] Workload calculation
- [ ] Assignment algorithm
- [ ] Slack message formatting
- [ ] Slack notification sending

### Integration Tests
- [ ] JIRA + Workload Manager
- [ ] AI + JIRA
- [ ] Complete workflow
- [ ] Error handling paths
- [ ] Dry-run mode

### Manual Tests
- [ ] Connect to JIRA with PAT
- [ ] Fetch real tickets
- [ ] Classify real tickets
- [ ] Assign to real users
- [ ] Send to real Slack channel
- [ ] Verify in JIRA UI
- [ ] Check Slack messages
- [ ] Review logs
- [ ] Test error scenarios
- [ ] Verify cron execution

### Performance Tests
- [ ] Process 10 tickets
- [ ] Process 50 tickets
- [ ] Measure execution time
- [ ] Check memory usage
- [ ] Verify API rate limits

---

## Next Steps

After completing implementation:

1. **Monitor Initial Runs**
   - Watch logs closely for first week
   - Verify assignment accuracy
   - Check AI classification quality
   - Gather team feedback

2. **Optimize**
   - Tune AI prompts based on results
   - Adjust assignment algorithm if needed
   - Optimize performance bottlenecks

3. **Enhance**
   - Add metrics dashboard
   - Implement advanced features
   - Improve error recovery
   - Add more automation rules

4. **Document**
   - Create runbooks
   - Document common issues
   - Update team procedures
   - Train new team members

---

**End of Implementation Guide**