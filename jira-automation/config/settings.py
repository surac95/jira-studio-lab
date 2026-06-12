"""
Settings and configuration management for JIRA automation system.

This module provides centralized configuration loading from environment
variables and configuration files, with validation and singleton pattern.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv


class Settings:
    """
    Singleton class for managing application settings.
    
    This class loads configuration from:
    - Environment variables (via .env file)
    - config/team.json file
    
    It provides validation and easy access to all configuration values.
    
    Attributes:
        jira_url: JIRA instance URL
        jira_pat_token: JIRA Personal Access Token
        jira_project_key: JIRA project key
        jira_queue_jql: JQL query for filtering tickets
        mistral_api_key: Mistral AI API key
        slack_bot_token: Slack bot token
        slack_channel_id: Slack channel ID for notifications
        log_level: Logging level
        team_members: List of team member dictionaries
    """
    
    _instance: Optional['Settings'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'Settings':
        """
        Implement singleton pattern.
        
        Returns:
            The single Settings instance
        """
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Initialize settings by loading from environment and config files.
        
        Only initializes once due to singleton pattern.
        """
        # Only initialize once
        if Settings._initialized:
            return
        
        # Load environment variables from .env file
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)
        
        # Load JIRA settings
        self.jira_url = os.getenv('JIRA_URL', '')
        self.jira_pat_token = os.getenv('JIRA_PAT_TOKEN', '')
        self.jira_project_key = os.getenv('JIRA_PROJECT_KEY', '')
        self.jira_queue_jql = os.getenv('JIRA_QUEUE_JQL', '')
        
        # Load Mistral AI settings
        self.mistral_api_key = os.getenv('MISTRAL_API_KEY', '')
        
        # Load Slack settings
        self.slack_bot_token = os.getenv('SLACK_BOT_TOKEN', '')
        self.slack_channel_id = os.getenv('SLACK_CHANNEL_ID', '')
        
        # Load logging settings
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # Load team members from config file
        self.team_members: List[Dict[str, Any]] = []
        self._load_team_members()
        
        Settings._initialized = True
    
    def _load_team_members(self) -> None:
        """
        Load team members from config/team.json file.
        
        Raises:
            FileNotFoundError: If team.json file is not found
            json.JSONDecodeError: If team.json is not valid JSON
        """
        team_config_path = Path(__file__).parent / 'team.json'
        
        if not team_config_path.exists():
            raise FileNotFoundError(
                f"Team configuration file not found: {team_config_path}"
            )
        
        try:
            with open(team_config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Extract team members from the JSON structure
            if 'team_members' in data:
                self.team_members = data['team_members']
            else:
                self.team_members = []
                
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in team configuration file: {e.msg}",
                e.doc,
                e.pos
            )
    
    def validate_required_settings(self) -> tuple[bool, List[str]]:
        """
        Validate that all required settings are configured.
        
        Checks that essential environment variables are set and not empty.
        
        Returns:
            Tuple of (is_valid, list_of_missing_settings)
            - is_valid: True if all required settings are present
            - list_of_missing_settings: List of missing setting names
        """
        required_settings = {
            'JIRA_URL': self.jira_url,
            'JIRA_PAT_TOKEN': self.jira_pat_token,
            'JIRA_PROJECT_KEY': self.jira_project_key,
            'JIRA_QUEUE_JQL': self.jira_queue_jql,
            'MISTRAL_API_KEY': self.mistral_api_key,
            'SLACK_BOT_TOKEN': self.slack_bot_token,
            'SLACK_CHANNEL_ID': self.slack_channel_id
        }
        
        missing_settings = [
            name for name, value in required_settings.items()
            if not value or value.strip() == ''
        ]
        
        is_valid = len(missing_settings) == 0
        
        return is_valid, missing_settings
    
    def load_team_members(self) -> List[Dict[str, Any]]:
        """
        Get the list of team members from configuration.
        
        Returns:
            List of team member dictionaries with their properties
        """
        return self.team_members.copy()
    
    def get_team_member_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Find a team member by their JIRA username.
        
        Args:
            username: JIRA username to search for
            
        Returns:
            Team member dictionary if found, None otherwise
        """
        for member in self.team_members:
            if member.get('jira_username') == username:
                return member.copy()
        return None
    
    def get_team_member_count(self) -> int:
        """
        Get the total number of team members.
        
        Returns:
            Number of team members in the configuration
        """
        return len(self.team_members)
    
    def reload_team_members(self) -> None:
        """
        Reload team members from the configuration file.
        
        Useful when the team.json file has been updated and needs to be reloaded.
        
        Raises:
            FileNotFoundError: If team.json file is not found
            json.JSONDecodeError: If team.json is not valid JSON
        """
        self._load_team_members()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert settings to dictionary representation.
        
        Note: Sensitive values like tokens are masked for security.
        
        Returns:
            Dictionary containing all settings (with masked sensitive values)
        """
        return {
            'jira_url': self.jira_url,
            'jira_pat_token': '***' if self.jira_pat_token else '',
            'jira_project_key': self.jira_project_key,
            'jira_queue_jql': self.jira_queue_jql,
            'mistral_api_key': '***' if self.mistral_api_key else '',
            'slack_bot_token': '***' if self.slack_bot_token else '',
            'slack_channel_id': self.slack_channel_id,
            'log_level': self.log_level,
            'team_member_count': len(self.team_members)
        }
    
    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance.
        
        This is primarily useful for testing purposes to create a fresh instance.
        """
        cls._instance = None
        cls._initialized = False
    
    def __repr__(self) -> str:
        """String representation of Settings."""
        return f"Settings(jira_url='{self.jira_url}', team_members={len(self.team_members)})"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        is_valid, missing = self.validate_required_settings()
        status = "Valid" if is_valid else f"Invalid (missing: {', '.join(missing)})"
        return f"Settings: {status}, Team Members: {len(self.team_members)}"


# Convenience function to get settings instance
def get_settings() -> Settings:
    """
    Get the Settings singleton instance.
    
    Returns:
        Settings instance
    """
    return Settings()

# Made with Bob
