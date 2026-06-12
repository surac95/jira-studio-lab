# AI-Powered JIRA Incident Ticket Automation System
## Technical Architecture Specification

**Version:** 1.0  
**Date:** 2026-06-10  
**Project:** JIRA L3/L4 Support Queue Automation

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [System Architecture Overview](#system-architecture-overview)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Project Structure](#project-structure)
7. [Configuration Management](#configuration-management)
8. [Security Considerations](#security-considerations)
9. [Error Handling & Logging](#error-handling--logging)
10. [Deployment Strategy](#deployment-strategy)
11. [Testing Strategy](#testing-strategy)
12. [Future Enhancements](#future-enhancements)

---

## Executive Summary

This document outlines the architecture for an AI-powered automation system that monitors JIRA L3/L4 support queues, classifies incidents using Mistral AI, assigns tickets based on team workload, and notifies the team via Slack. The system runs as a scheduled cron job every 15 minutes.

**Key Features:**
- Automated JIRA ticket monitoring and assignment
- AI-powered classification (TRIRIGA, APIC, APPC)
- Workload-balanced assignment using JIRA dashboard data
- AI-generated ticket summaries
- Slack notifications for team awareness
- Stateless operation with JIRA as source of truth

---

## System Architecture Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CRON SCHEDULER                          │
│                    (Every 15 minutes)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MAIN ORCHESTRATOR                             │
│                  (main.py - Entry Point)                        │
└───┬─────────────┬─────────────┬─────────────┬──────────────────┘
    │             │             │             │
    ▼             ▼             ▼             ▼
┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐
│  JIRA   │ │ Mistral  │ │ Workload │ │    Slack    │
│ Service │ │   AI     │ │ Manager  │ │   Service   │
│         │ │ Service  │ │          │ │             │
└────┬────┘ └────┬─────┘ └────┬─────┘ └──────┬──────┘
     │           │            │               │
     ▼           ▼            ▼               ▼
┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐
│  JIRA   │ │ Mistral  │ │   JIRA   │ │    Slack    │
│ Server  │ │   API    │ │Dashboard │ │     API     │
└─────────┘ └──────────┘ └──────────┘ └─────────────┘
```

### Architecture Principles

1. **Stateless Design**: No local database; JIRA is the single source of truth
2. **Modularity**: Each service is independent and testable
3. **Fail-Safe**: Errors in one ticket don't affect others
4. **Idempotency**: Safe to run multiple times without side effects
5. **Security-First**: All credentials via environment variables
6. **Observability**: Comprehensive logging for debugging

---

## Component Architecture

### 1. Main Orchestrator (`main.py`)

**Responsibility**: Entry point that coordinates the entire workflow

**Key Functions**:
- Initialize all service components
- Fetch unassigned tickets from JIRA queue
- Process each ticket through the pipeline
- Handle global error scenarios
- Manage execution lifecycle

**Pseudocode Flow**:
```python
def main():
    # Initialize services
    jira_service = JiraService()
    ai_service = MistralAIService()
    workload_manager = WorkloadManager()
    slack_service = SlackService()
    
    # Fetch unassigned tickets
    tickets = jira_service.get_unassigned_tickets()
    
    # Process each ticket
    for ticket in tickets:
        try:
            # Classify ticket
            classification = ai_service.classify_ticket(ticket)
            
            # Generate summary
            summary = ai_service.summarize_ticket(ticket)
            
            # Get best assignee
            assignee = workload_manager.get_best_assignee(classification)
            
            # Assign ticket
            jira_service.assign_ticket(ticket.id, assignee)
            
            # Notify team
            slack_service.send_notification(ticket, classification, assignee, summary)
            
        except Exception as e:
            logger.error(f"Failed to process ticket {ticket.id}: {e}")
            continue
```

---

### 2. JIRA Service (`services/jira_service.py`)

**Responsibility**: All JIRA API interactions

**Key Methods**:

```python
class JiraService:
    def __init__(self, server_url, pat_token):
        """Initialize JIRA client with PAT authentication"""
        
    def get_unassigned_tickets(self, queue_filter="L3/L4"):
        """
        Fetch unassigned tickets from L3/L4 queue
        Returns: List[Ticket]
        JQL: project = XYZ AND status = "Open" AND assignee is EMPTY 
             AND (labels = "L3" OR labels = "L4")
        """
        
    def get_ticket_details(self, ticket_id):
        """
        Fetch complete ticket information
        Returns: Ticket object with summary, description, comments, attachments
        """
        
    def assign_ticket(self, ticket_id, assignee_username):
        """
        Assign ticket to team member
        Updates assignee field in JIRA
        """
        
    def get_team_workload(self):
        """
        Query JIRA dashboard API for current team workload
        Returns: Dict[username, ticket_count]
        Uses: JIRA Dashboard API or Gadget REST API
        """
        
    def add_comment(self, ticket_id, comment):
        """
        Add automation comment to ticket
        Used for audit trail
        """
```

**JIRA Dashboard Integration**:
- Use JIRA REST API to query dashboard gadget data
- Endpoint: `/rest/api/2/search` with JQL for team member assignments
- Alternative: `/rest/dashboards/1.0/` API for dashboard data
- Parse workload from assigned ticket counts per user

---

### 3. Mistral AI Service (`services/mistral_service.py`)

**Responsibility**: AI-powered classification and summarization

**Key Methods**:

```python
class MistralAIService:
    def __init__(self, api_key):
        """Initialize Mistral AI client"""
        
    def classify_ticket(self, ticket):
        """
        Classify ticket into TRIRIGA, APIC, or APPC
        
        Args:
            ticket: Ticket object with summary, description, comments
            
        Returns:
            classification: str (TRIRIGA, APIC, or APPC)
            confidence: float (0-1)
            
        Prompt Strategy:
        - Include ticket summary, description, and recent comments
        - Use few-shot learning with examples
        - Request structured JSON response
        """
        
    def summarize_ticket(self, ticket):
        """
        Generate concise ticket summary
        
        Args:
            ticket: Ticket object with all details
            
        Returns:
            summary: str (2-3 sentences)
            
        Includes:
        - Main issue description
        - Key details from comments
        - Attachment information (count, types)
        """
        
    def _build_classification_prompt(self, ticket):
        """
        Build prompt for classification
        
        Template:
        You are a support ticket classifier. Classify the following ticket
        into one of these categories: TRIRIGA, APIC, or APPC.
        
        TRIRIGA: Real estate and facility management issues
        APIC: API connectivity and integration issues  
        APPC: Application configuration and customization issues
        
        Ticket Summary: {summary}
        Description: {description}
        Recent Comments: {comments}
        
        Respond with JSON: {"classification": "CATEGORY", "confidence": 0.95}
        """
```

**AI Prompt Engineering Best Practices**:
- Clear category definitions with examples
- Structured output format (JSON)
- Include confidence scores for validation
- Handle edge cases (unclear tickets)

---

### 4. Workload Manager (`services/workload_manager.py`)

**Responsibility**: Intelligent ticket assignment based on workload and specialization

**Key Methods**:

```python
class WorkloadManager:
    def __init__(self, jira_service, team_config):
        """
        Initialize with JIRA service and team configuration
        
        team_config structure:
        {
            "members": [
                {
                    "username": "john.doe",
                    "name": "John Doe",
                    "specializations": ["TRIRIGA", "APIC"],
                    "max_tickets": 10
                },
                ...
            ]
        }
        """
        
    def get_best_assignee(self, classification):
        """
        Determine best assignee based on:
        1. Specialization match
        2. Current workload
        3. Availability
        
        Algorithm:
        - Filter team members by specialization
        - Get current workload from JIRA
        - Select member with lowest workload
        - Respect max_tickets limit
        
        Returns: username (str)
        """
        
    def get_current_workload(self):
        """
        Fetch current workload for all team members
        Returns: Dict[username, ticket_count]
        """
        
    def is_available(self, username):
        """
        Check if team member is available
        - Not at max capacity
        - Not on leave (future enhancement)
        """
```

**Assignment Algorithm**:
```
1. Filter team members by specialization (TRIRIGA/APIC/APPC)
2. Get current ticket count for each member from JIRA
3. Calculate available capacity (max_tickets - current_count)
4. Select member with highest available capacity
5. If tie, use round-robin or random selection
6. If no one available, assign to team lead or queue
```

---

### 5. Slack Service (`services/slack_service.py`)

**Responsibility**: Send notifications to Slack channel

**Key Methods**:

```python
class SlackService:
    def __init__(self, bot_token, channel_id):
        """Initialize Slack client with bot token"""
        
    def send_notification(self, ticket, classification, assignee, summary):
        """
        Send ticket assignment notification
        
        Message Format:
        🎫 New Ticket Assigned
        
        Ticket: [PROJ-123] Brief ticket summary
        Classification: TRIRIGA
        Assigned To: @john.doe
        Priority: High
        
        Summary:
        AI-generated summary of the ticket...
        
        Link: https://jira.issworld.com/browse/PROJ-123
        """
        
    def send_error_notification(self, error_message):
        """
        Send error alerts to monitoring channel
        Used for critical failures
        """
        
    def _format_message(self, ticket, classification, assignee, summary):
        """
        Format Slack message with proper structure
        Uses Slack Block Kit for better formatting
        """
```

**Slack Message Template**:
```
🎫 *New Ticket Assigned*

*Ticket:* <https://jira.issworld.com/browse/PROJ-123|PROJ-123> - Brief summary
*Classification:* TRIRIGA
*Assigned To:* @john.doe
*Priority:* High
*Created:* 2026-06-10 10:30 AM

*AI Summary:*
The ticket describes an issue with facility management system...

---
_Automated by JIRA Ticket Bot_
```

---

### 6. Configuration Manager (`config/config.py`)

**Responsibility**: Centralized configuration management

**Key Components**:

```python
class Config:
    """Configuration loaded from environment variables"""
    
    # JIRA Configuration
    JIRA_SERVER_URL = os.getenv("JIRA_SERVER_URL")
    JIRA_PAT_TOKEN = os.getenv("JIRA_PAT_TOKEN")
    JIRA_QUEUE_FILTER = os.getenv("JIRA_QUEUE_FILTER", "L3/L4")
    
    # Mistral AI Configuration
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
    
    # Slack Configuration
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
    
    # Team Configuration
    TEAM_CONFIG_PATH = os.getenv("TEAM_CONFIG_PATH", "config/team.json")
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/automation.log")
    
    @classmethod
    def validate(cls):
        """Validate all required configuration is present"""
        required = [
            "JIRA_SERVER_URL",
            "JIRA_PAT_TOKEN",
            "MISTRAL_API_KEY",
            "SLACK_BOT_TOKEN",
            "SLACK_CHANNEL_ID"
        ]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required config: {missing}")
```

---

### 7. Models (`models/ticket.py`)

**Responsibility**: Data models for type safety and clarity

```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Attachment:
    filename: str
    size: int
    content_type: str
    url: str

@dataclass
class Comment:
    author: str
    body: str
    created: datetime

@dataclass
class Ticket:
    id: str
    key: str
    summary: str
    description: str
    priority: str
    status: str
    created: datetime
    updated: datetime
    comments: List[Comment]
    attachments: List[Attachment]
    labels: List[str]
    
    def get_full_content(self) -> str:
        """Combine all ticket content for AI processing"""
        content = f"Summary: {self.summary}\n\n"
        content += f"Description: {self.description}\n\n"
        
        if self.comments:
            content += "Comments:\n"
            for comment in self.comments[-5:]:  # Last 5 comments
                content += f"- {comment.author}: {comment.body}\n"
        
        if self.attachments:
            content += f"\nAttachments: {len(self.attachments)} files\n"
            for att in self.attachments:
                content += f"- {att.filename} ({att.content_type})\n"
        
        return content

@dataclass
class TeamMember:
    username: str
    name: str
    specializations: List[str]
    max_tickets: int = 10

@dataclass
class Classification:
    category: str  # TRIRIGA, APIC, or APPC
    confidence: float
    reasoning: Optional[str] = None
```

---

## Data Flow

### Sequence Diagram: Ticket Processing Flow

```
┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐
│ Cron │   │ Main │   │ JIRA │   │  AI  │   │ Work │   │Slack │
└──┬───┘   └──┬───┘   └──┬───┘   └──┬───┘   └──┬───┘   └──┬───┘
   │          │          │          │          │          │
   │ Trigger  │          │          │          │          │
   ├─────────>│          │          │          │          │
   │          │          │          │          │          │
   │          │ Get Unassigned      │          │          │
   │          ├─────────>│          │          │          │
   │          │          │          │          │          │
   │          │ Tickets  │          │          │          │
   │          │<─────────┤          │          │          │
   │          │          │          │          │          │
   │          │ For Each Ticket     │          │          │
   │          │──────────┐          │          │          │
   │          │          │          │          │          │
   │          │ Get Details         │          │          │
   │          ├─────────>│          │          │          │
   │          │<─────────┤          │          │          │
   │          │          │          │          │          │
   │          │ Classify Ticket     │          │          │
   │          ├────────────────────>│          │          │
   │          │<────────────────────┤          │          │
   │          │          │          │          │          │
   │          │ Summarize Ticket    │          │          │
   │          ├────────────────────>│          │          │
   │          │<────────────────────┤          │          │
   │          │          │          │          │          │
   │          │ Get Best Assignee   │          │          │
   │          ├───────────────────────────────>│          │
   │          │          │          │          │          │
   │          │          │ Get Workload        │          │
   │          │          │<─────────┤          │          │
   │          │          │──────────>          │          │
   │          │          │          │          │          │
   │          │<───────────────────────────────┤          │
   │          │          │          │          │          │
   │          │ Assign Ticket       │          │          │
   │          ├─────────>│          │          │          │
   │          │<─────────┤          │          │          │
   │          │          │          │          │          │
   │          │ Send Notification   │          │          │
   │          ├──────────────────────────────────────────>│
   │          │<──────────────────────────────────────────┤
   │          │          │          │          │          │
   │          │<─────────┘          │          │          │
   │          │          │          │          │          │
```

### Data Flow Description

1. **Trigger Phase** (Every 15 minutes)
   - Cron job triggers main orchestrator
   - System initializes all service components
   - Configuration validation occurs

2. **Discovery Phase**
   - JIRA Service queries for unassigned tickets in L3/L4 queue
   - Filters tickets by status and labels
   - Returns list of ticket IDs

3. **Processing Phase** (Per Ticket)
   - **Fetch Details**: Get complete ticket information (summary, description, comments, attachments)
   - **Classification**: Send ticket content to Mistral AI for categorization
   - **Summarization**: Generate AI summary of ticket content
   - **Assignment**: Workload Manager determines best assignee based on specialization and current load
   - **Update**: JIRA Service assigns ticket to selected team member
   - **Notification**: Slack Service sends notification to team channel

4. **Completion Phase**
   - Log execution summary
   - Report any errors encountered
   - Clean up resources

### Error Handling Flow

```
Error Occurs
    │
    ├─> Log Error Details
    │
    ├─> Continue to Next Ticket (Fail-Safe)
    │
    ├─> If Critical Error (API Down)
    │   └─> Send Slack Alert
    │       └─> Exit Gracefully
    │
    └─> If Ticket Error (Invalid Data)
        └─> Add Comment to Ticket
            └─> Continue Processing
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.10+ | Main implementation language |
| **JIRA Client** | `jira` library | 3.5+ | JIRA REST API interaction |
| **AI Service** | Mistral AI API | Latest | Classification and summarization |
| **Slack Client** | `slack-sdk` | 3.23+ | Slack notifications |
| **HTTP Client** | `requests` | 2.31+ | API calls |
| **Environment** | `python-dotenv` | 1.0+ | Environment variable management |
| **Logging** | `logging` (stdlib) | - | Application logging |
| **Scheduling** | System cron | - | Job scheduling |

### Development & Testing

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Testing** | `pytest` | Unit and integration tests |
| **Mocking** | `pytest-mock` | Mock external services |
| **Code Quality** | `pylint`, `black` | Linting and formatting |
| **Type Checking** | `mypy` | Static type checking |
| **Coverage** | `pytest-cov` | Code coverage reporting |

### Dependencies

**requirements.txt**:
```
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

---

## Project Structure

```
jira-automation/
│
├── config/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   └── team.json              # Team member configuration
│
├── services/
│   ├── __init__.py
│   ├── jira_service.py        # JIRA API interactions
│   ├── mistral_service.py     # Mistral AI integration
│   ├── workload_manager.py    # Assignment logic
│   └── slack_service.py       # Slack notifications
│
├── models/
│   ├── __init__.py
│   └── ticket.py              # Data models
│
├── utils/
│   ├── __init__.py
│   ├── logger.py              # Logging configuration
│   └── validators.py          # Input validation
│
├── tests/
│   ├── __init__.py
│   ├── test_jira_service.py
│   ├── test_mistral_service.py
│   ├── test_workload_manager.py
│   ├── test_slack_service.py
│   └── fixtures/
│       └── sample_tickets.json
│
├── logs/
│   └── .gitkeep
│
├── main.py                    # Entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment variables
├── .gitignore
├── README.md
└── ARCHITECTURE.md           # This document
```

### File Descriptions

**`main.py`**: Entry point that orchestrates the entire workflow
**`config/config.py`**: Centralized configuration from environment variables
**`config/team.json`**: Team member definitions and specializations
**`services/jira_service.py`**: All JIRA API interactions
**`services/mistral_service.py`**: AI classification and summarization
**`services/workload_manager.py`**: Assignment algorithm implementation
**`services/slack_service.py`**: Slack notification handling
**`models/ticket.py`**: Data models for tickets and team members
**`utils/logger.py`**: Logging setup and configuration
**`utils/validators.py`**: Input validation utilities

---

## Configuration Management

### Environment Variables

Create a `.env` file in the project root:

```bash
# JIRA Configuration
JIRA_SERVER_URL=https://jira.issworld.com
JIRA_PAT_TOKEN=your_personal_access_token_here
JIRA_QUEUE_FILTER=L3/L4
JIRA_PROJECT_KEY=PROJ

# Mistral AI Configuration
MISTRAL_API_KEY=your_mistral_api_key_here
MISTRAL_MODEL=mistral-large-latest
MISTRAL_MAX_TOKENS=1000
MISTRAL_TEMPERATURE=0.3

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL_ID=C01234567890
SLACK_ERROR_CHANNEL_ID=C09876543210

# Team Configuration
TEAM_CONFIG_PATH=config/team.json

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/automation.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5

# Execution Configuration
DRY_RUN=false
MAX_TICKETS_PER_RUN=50
```

### Team Configuration (`config/team.json`)

```json
{
  "members": [
    {
      "username": "john.doe",
      "name": "John Doe",
      "email": "john.doe@company.com",
      "specializations": ["TRIRIGA", "APIC"],
      "max_tickets": 10,
      "active": true
    },
    {
      "username": "jane.smith",
      "name": "Jane Smith",
      "email": "jane.smith@company.com",
      "specializations": ["APPC"],
      "max_tickets": 8,
      "active": true
    },
    {
      "username": "bob.wilson",
      "name": "Bob Wilson",
      "email": "bob.wilson@company.com",
      "specializations": ["TRIRIGA", "APIC", "APPC"],
      "max_tickets": 12,
      "active": true
    }
  ],
  "fallback_assignee": "team.lead",
  "assignment_strategy": "workload_balanced"
}
```

### JIRA Query Configuration

The system uses JQL (JIRA Query Language) to find unassigned tickets:

```sql
project = PROJ 
AND status IN ("Open", "New", "To Do") 
AND assignee is EMPTY 
AND (labels = "L3" OR labels = "L4")
AND created >= -1h
ORDER BY priority DESC, created ASC
```

This can be customized via environment variables or configuration file.

---

## Security Considerations

### 1. Credential Management

**Best Practices**:
- ✅ Store all credentials in environment variables
- ✅ Never commit `.env` file to version control
- ✅ Use `.env.example` as template without real values
- ✅ Rotate tokens regularly (quarterly)
- ✅ Use least-privilege access for all tokens

**Token Requirements**:

| Token | Required Permissions |
|-------|---------------------|
| JIRA PAT | Read tickets, Update assignee, Add comments |
| Mistral API Key | API access for classification/summarization |
| Slack Bot Token | `chat:write`, `channels:read` |

### 2. API Security

```python
# Example: Secure API client initialization
class SecureAPIClient:
    def __init__(self, api_key: str):
        # Never log API keys
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'JIRA-Automation/1.0'
        })
    
    def __repr__(self):
        # Prevent accidental key exposure in logs
        return f"SecureAPIClient(api_key='***')"
```

### 3. Input Validation

- Validate all ticket data before processing
- Sanitize user input in comments
- Validate team member usernames
- Check classification results for valid categories

### 4. Error Information Disclosure

- Don't expose sensitive data in error messages
- Log detailed errors internally
- Send sanitized errors to Slack
- Mask credentials in all logs

### 5. Network Security

- Use HTTPS for all API calls
- Implement request timeouts
- Add retry logic with exponential backoff
- Validate SSL certificates

---

## Error Handling & Logging

### Logging Strategy

**Log Levels**:
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for recoverable issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical issues requiring immediate attention

**Log Format**:
```
2026-06-10 10:30:45,123 - INFO - [main] - Processing 5 unassigned tickets
2026-06-10 10:30:46,456 - INFO - [jira_service] - Fetched ticket PROJ-123
2026-06-10 10:30:47,789 - INFO - [mistral_service] - Classified PROJ-123 as TRIRIGA (confidence: 0.95)
2026-06-10 10:30:48,012 - INFO - [workload_manager] - Assigned PROJ-123 to john.doe
2026-06-10 10:30:49,345 - ERROR - [slack_service] - Failed to send notification: Connection timeout
```

### Error Handling Patterns

```python
# Pattern 1: Graceful Degradation
try:
    summary = ai_service.summarize_ticket(ticket)
except MistralAPIError as e:
    logger.warning(f"AI summarization failed: {e}")
    summary = f"Auto-summary unavailable. See ticket for details."

# Pattern 2: Retry with Backoff
@retry(max_attempts=3, backoff_factor=2)
def assign_ticket(ticket_id, assignee):
    try:
        jira_service.assign_ticket(ticket_id, assignee)
    except JIRAError as e:
        if e.status_code == 429:  # Rate limit
            raise  # Retry
        else:
            logger.error(f"Assignment failed: {e}")
            raise

# Pattern 3: Circuit Breaker
class CircuitBreaker:
    def __init__(self, failure_threshold=5):
        self.failure_count = 0
        self.threshold = failure_threshold
        self.is_open = False
    
    def call(self, func, *args, **kwargs):
        if self.is_open:
            raise CircuitBreakerOpen("Service unavailable")
        
        try:
            result = func(*args, **kwargs)
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.threshold:
                self.is_open = True
            raise
```

### Error Categories

| Error Type | Handling Strategy | Notification |
|------------|------------------|--------------|
| **Network Timeout** | Retry with backoff | Log warning |
| **API Rate Limit** | Wait and retry | Log info |
| **Invalid Credentials** | Fail fast, alert | Slack critical |
| **Ticket Not Found** | Skip, continue | Log warning |
| **AI Service Down** | Use fallback logic | Slack error |
| **Invalid Classification** | Manual review queue | Log error |
| **Slack Send Failure** | Log only, continue | Log error |

---

## Deployment Strategy

### 1. Server Requirements

**Minimum Specifications**:
- OS: Linux (Ubuntu 20.04+ or RHEL 8+)
- Python: 3.10 or higher
- RAM: 512 MB
- Disk: 1 GB
- Network: Outbound HTTPS access

### 2. Installation Steps

```bash
# 1. Clone repository
git clone <repository-url>
cd jira-automation

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with actual credentials

# 5. Configure team
cp config/team.json.example config/team.json
# Edit team.json with team members

# 6. Test configuration
python main.py --dry-run

# 7. Setup cron job
crontab -e
# Add: */15 * * * * cd /path/to/jira-automation && /path/to/venv/bin/python main.py >> logs/cron.log 2>&1
```

### 3. Cron Configuration

**Option 1: User Crontab**
```bash
# Run every 15 minutes
*/15 * * * * cd /home/user/jira-automation && /home/user/jira-automation/venv/bin/python /home/user/jira-automation/main.py >> /home/user/jira-automation/logs/cron.log 2>&1
```

**Option 2: System Crontab** (`/etc/cron.d/jira-automation`)
```bash
*/15 * * * * automation-user cd /opt/jira-automation && /opt/jira-automation/venv/bin/python /opt/jira-automation/main.py >> /opt/jira-automation/logs/cron.log 2>&1
```

**Option 3: Systemd Timer** (Recommended for production)

Create `/etc/systemd/system/jira-automation.service`:
```ini
[Unit]
Description=JIRA Ticket Automation
After=network.target

[Service]
Type=oneshot
User=automation-user
WorkingDirectory=/opt/jira-automation
Environment="PATH=/opt/jira-automation/venv/bin"
EnvironmentFile=/opt/jira-automation/.env
ExecStart=/opt/jira-automation/venv/bin/python /opt/jira-automation/main.py
StandardOutput=append:/opt/jira-automation/logs/automation.log
StandardError=append:/opt/jira-automation/logs/automation.log
```

Create `/etc/systemd/system/jira-automation.timer`:
```ini
[Unit]
Description=Run JIRA Automation every 15 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min
AccuracySec=1min

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable jira-automation.timer
sudo systemctl start jira-automation.timer
```

### 4. Monitoring & Maintenance

**Health Checks**:
```bash
# Check last execution
tail -f logs/automation.log

# Check cron status
systemctl status jira-automation.timer

# View execution history
journalctl -u jira-automation.service -n 50
```

**Log Rotation** (`/etc/logrotate.d/jira-automation`):
```
/opt/jira-automation/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 automation-user automation-user
    sharedscripts
    postrotate
        systemctl reload jira-automation.service > /dev/null 2>&1 || true
    endscript
}
```

### 5. Backup Strategy

**What to Backup**:
- Configuration files (`config/`)
- Environment variables (`.env`)
- Logs (last 30 days)
- Team configuration

**Backup Script**:
```bash
#!/bin/bash
BACKUP_DIR="/backup/jira-automation"
DATE=$(date +%Y%m%d_%H%M%S)

tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    config/ \
    .env \
    logs/

# Keep last 7 backups
ls -t "$BACKUP_DIR"/config_*.tar.gz | tail -n +8 | xargs rm -f
```

### 6. Disaster Recovery

**Recovery Steps**:
1. Restore configuration from backup
2. Verify environment variables
3. Test JIRA connectivity
4. Test AI service connectivity
5. Test Slack connectivity
6. Run in dry-run mode
7. Resume normal operation

---

## Testing Strategy

### 1. Unit Tests

Test individual components in isolation:

```python
# tests/test_mistral_service.py
import pytest
from services.mistral_service import MistralAIService
from models.ticket import Ticket

@pytest.fixture
def mistral_service():
    return MistralAIService(api_key="test_key")

@pytest.fixture
def sample_ticket():
    return Ticket(
        id="1",
        key="PROJ-123",
        summary="TRIRIGA login issue",
        description="Users cannot log into TRIRIGA",
        priority="High",
        status="Open",
        created=datetime.now(),
        updated=datetime.now(),
        comments=[],
        attachments=[],
        labels=["L3"]
    )

def test_classify_ticket_tririga(mistral_service, sample_ticket, mocker):
    # Mock API response
    mock_response = {"classification": "TRIRIGA", "confidence": 0.95}
    mocker.patch.object(mistral_service, '_call_api', return_value=mock_response)
    
    result = mistral_service.classify_ticket(sample_ticket)
    
    assert result.category == "TRIRIGA"
    assert result.confidence == 0.95

def test_classify_ticket_api_error(mistral_service, sample_ticket, mocker):
    # Mock API error
    mocker.patch.object(mistral_service, '_call_api', side_effect=Exception("API Error"))
    
    with pytest.raises(Exception):
        mistral_service.classify_ticket(sample_ticket)
```

### 2. Integration Tests

Test component interactions:

```python
# tests/test_integration.py
def test_end_to_end_ticket_processing(mocker):
    # Mock external services
    mock_jira = mocker.Mock()
    mock_ai = mocker.Mock()
    mock_slack = mocker.Mock()
    
    # Setup test data
    ticket = create_test_ticket()
    mock_jira.get_unassigned_tickets.return_value = [ticket]
    mock_ai.classify_ticket.return_value = Classification("TRIRIGA", 0.95)
    
    # Run main workflow
    main()
    
    # Verify interactions
    mock_jira.assign_ticket.assert_called_once()
    mock_slack.send_notification.assert_called_once()
```

### 3. Test Coverage Goals

- Unit test coverage: > 80%
- Integration test coverage: > 60%
- Critical path coverage: 100%

### 4. Manual Testing Checklist

- [ ] JIRA connection with PAT token
- [ ] Fetch unassigned tickets from queue
- [ ] AI classification accuracy
- [ ] AI summarization quality
- [ ] Workload calculation correctness
- [ ] Ticket assignment in JIRA
- [ ] Slack notification delivery
- [ ] Error handling for each service
- [ ] Dry-run mode functionality
- [ ] Log file creation and rotation

---

## Future Enhancements

### Phase 2 Features

1. **Advanced Assignment Logic**
   - Consider ticket priority in assignment
   - Time-based assignment (business hours)
   - Skill-level matching
   - Team member availability calendar integration

2. **Performance Optimization**
   - Batch processing for multiple tickets
   - Caching for team workload data
   - Parallel AI API calls
   - Database for state management

3. **Enhanced AI Capabilities**
   - Multi-label classification
   - Severity prediction
   - Estimated resolution time
   - Similar ticket detection

4. **Monitoring & Analytics**
   - Dashboard for automation metrics
   - Assignment distribution reports
   - AI accuracy tracking
   - Response time analytics

5. **User Interface**
   - Web dashboard for configuration
   - Manual override capabilities
   - Ticket reassignment interface
   - Team workload visualization

6. **Advanced Notifications**
   - Rich Slack messages with buttons
   - Email notifications
   - SMS alerts for critical tickets
   - Microsoft Teams integration

7. **Workflow Automation**
   - Auto-response to common issues
   - Ticket escalation rules
   - SLA monitoring
   - Auto-close resolved tickets

### Technical Debt Considerations

- Implement comprehensive error recovery
- Add metrics collection (Prometheus)
- Implement distributed tracing
- Add API rate limiting protection
- Implement circuit breakers for all external services
- Add health check endpoints
- Implement graceful shutdown

---

## Appendix

### A. JIRA API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/rest/api/2/search` | GET | Search for tickets using JQL |
| `/rest/api/2/issue/{issueKey}` | GET | Get ticket details |
| `/rest/api/2/issue/{issueKey}` | PUT | Update ticket (assign) |
| `/rest/api/2/issue/{issueKey}/comment` | POST | Add comment |
| `/rest/api/2/myself` | GET | Verify authentication |

### B. Mistral AI API Reference

**Classification Prompt Template**:
```
You are a support ticket classifier for an IT support team.

Classify the following ticket into exactly one category:
- TRIRIGA: Real estate, facility management, space planning, building operations
- APIC: API connectivity, integration issues, web services, REST/SOAP APIs
- APPC: Application configuration, customization, user settings, permissions

Ticket Information:
Summary: {summary}
Description: {description}
Comments: {comments}

Respond with JSON only:
{
  "classification": "CATEGORY",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}
```

### C. Slack Message Formatting

**Block Kit Example**:
```json
{
  "blocks": [
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
          "text": "*Ticket:*\n<https://jira.issworld.com/browse/PROJ-123|PROJ-123>"
        },
        {
          "type": "mrkdwn",
          "text": "*Classification:*\nTRIRIGA"
        },
        {
          "type": "mrkdwn",
          "text": "*Assigned To:*\n@john.doe"
        },
        {
          "type": "mrkdwn",
          "text": "*Priority:*\nHigh"
        }
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*AI Summary:*\nThe ticket describes an issue with facility management system..."
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
          "text": "_Automated by JIRA Ticket Bot • 2026-06-10 10:30 AM_"
        }
      ]
    }
  ]
}
```

### D. Troubleshooting Guide

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| No tickets found | JQL filter incorrect | Verify JQL in JIRA UI |
| Authentication failed | Invalid PAT token | Regenerate token |
| AI classification fails | API key invalid | Check Mistral API key |
| Slack notification fails | Wrong channel ID | Verify channel ID |
| Assignment fails | User not found | Check username in team.json |
| High memory usage | Too many tickets | Reduce MAX_TICKETS_PER_RUN |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-06-10 | AI Architect | Initial architecture design |

---

**End of Architecture Document**