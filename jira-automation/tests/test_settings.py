"""
Unit tests for the Settings configuration class.

This module contains comprehensive tests for the Settings class,
including configuration loading, validation, and singleton behavior.
"""

import unittest
import os
import json
import sys
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Settings, get_settings


class TestSettings(unittest.TestCase):
    """Test cases for the Settings class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset singleton instance before each test
        Settings.reset_instance()
        
        # Sample environment variables
        self.env_vars = {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_PAT_TOKEN': 'test_token_123',
            'JIRA_PROJECT_KEY': 'TEST',
            'JIRA_QUEUE_JQL': 'project = TEST AND status = "To Do"',
            'MISTRAL_API_KEY': 'test_mistral_key',
            'SLACK_BOT_TOKEN': 'xoxb-test-token',
            'SLACK_CHANNEL_ID': 'C1234567890',
            'LOG_LEVEL': 'DEBUG'
        }
        
        # Sample team configuration
        self.team_config = {
            'team_members': [
                {
                    'name': 'Alice Johnson',
                    'jira_username': 'alice.johnson',
                    'email': 'alice@test.com',
                    'skills': ['Python', 'Backend'],
                    'max_concurrent_tickets': 5,
                    'current_workload': 0,
                    'availability': 'available'
                },
                {
                    'name': 'Bob Smith',
                    'jira_username': 'bob.smith',
                    'email': 'bob@test.com',
                    'skills': ['JavaScript', 'Frontend'],
                    'max_concurrent_tickets': 4,
                    'current_workload': 0,
                    'availability': 'available'
                }
            ],
            'metadata': {
                'last_updated': '2026-06-10T08:00:00Z',
                'version': '1.0.0'
            }
        }
    
    def tearDown(self):
        """Clean up after each test method."""
        Settings.reset_instance()
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('config.settings.load_dotenv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_settings_initialization_with_env_vars(self, mock_exists, mock_file, mock_load_dotenv):
        """Test settings initialization with environment variables."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.team_config)
        
        with patch.dict(os.environ, self.env_vars):
            settings = Settings()
            
            self.assertEqual(settings.jira_url, self.env_vars['JIRA_URL'])
            self.assertEqual(settings.jira_pat_token, self.env_vars['JIRA_PAT_TOKEN'])
            self.assertEqual(settings.jira_project_key, self.env_vars['JIRA_PROJECT_KEY'])
            self.assertEqual(settings.jira_queue_jql, self.env_vars['JIRA_QUEUE_JQL'])
            self.assertEqual(settings.mistral_api_key, self.env_vars['MISTRAL_API_KEY'])
            self.assertEqual(settings.slack_bot_token, self.env_vars['SLACK_BOT_TOKEN'])
            self.assertEqual(settings.slack_channel_id, self.env_vars['SLACK_CHANNEL_ID'])
            self.assertEqual(settings.log_level, self.env_vars['LOG_LEVEL'])
    
    @patch('config.settings.load_dotenv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_settings_singleton_behavior(self, mock_exists, mock_file, mock_load_dotenv):
        """Test that Settings implements singleton pattern."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.team_config)
        
        settings1 = Settings()
        settings2 = Settings()
        
        self.assertIs(settings1, settings2)
    
    @patch('config.settings.load_dotenv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_load_team_members_success(self, mock_exists, mock_file, mock_load_dotenv):
        """Test successful loading of team members from JSON."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.team_config)
        
        with patch('builtins.open', mock_open(read_data=json.dumps(self.team_config))):
            settings = Settings()
            
            self.assertEqual(len(settings.team_members), 2)
            self.assertEqual(settings.team_members[0]['name'], 'Alice Johnson')
            self.assertEqual(settings.team_members[1]['name'], 'Bob Smith')
    
    @patch('config.settings.load_dotenv')
    @patch('pathlib.Path.exists')
    def test_load_team_members_file_not_found(self, mock_exists, mock_load_dotenv):
        """Test that FileNotFoundError is raised when team.json is missing."""
        mock_exists.return_value = False
        
        with self.assertRaises(FileNotFoundError):
            Settings()
    
    @patch('config.settings.load_dotenv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_load_team_members_invalid_json(self, mock_exists, mock_file, mock_load_dotenv):
        """Test that JSONDecodeError is raised for invalid JSON."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "invalid json {"
        
        with patch('builtins.open', mock_open(read_data="invalid json {")):
            with self.assertRaises(json.JSONDecodeError):
                Settings()
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('config.settings.load_dotenv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_validate_required_settings_all_present(self, mock_exists, mock_file, mock_load_dotenv):
        """Test validation when all required settings are present."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.team_config)
        
        with patch.dict(os.environ, self.env_vars):
            with patch('builtins.open', mock_open(read_data=json.dumps(self.team_config))):
                settings = Settings()
                is_valid, missing = settings.validate_required_settings()
                
                self.assertTrue(is_valid)
                self.assertEqual(len(missing), 0)
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('config.settings.load_dotenv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_validate_required_settings_missing(self, mock_exists, mock_file, mock_load_dotenv):
        """Test validation when required settings are missing."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.team_config)
        
        # Only set some environment variables
        partial_env = {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_PROJECT_KEY': 'TEST'
        }
        
        with patch.dict(os.environ, partial_env, clear=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(self.team_config))):
                settings = Settings()
                is_valid, missing = settings.validate_required_settings()
                
                self.assertFalse(is_valid)
                self.assertGreater(len(missing), 0)
                self.assertIn('JIRA_PAT_TOKEN', missing)
                self.assertIn('MISTRAL_API_KEY', missing)
    
    @patch('config.settings.load_dotenv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_load_team_members_method(self, mock_exists, mock_file, mock_load_dotenv):
        """Test the load_team_members method returns a copy."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.team_config)
        
        with patch('builtins.open', mock_open(read_data=json.dumps(self.team_config))):
            settings = Settings()
            team_members = settings.load_team_members()
            
            # Modify the returned list
            team_members.append({'name': 'Test'})
            
            # Original should not be modified
            self.assertEqual(len(settings.team_members), 2)
    
    @patch('config.settings.load_dotenv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_get_team_member_by_username_found(self, mock_exists, mock_file, mock_load_dotenv):
        """Test finding a team member by username."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.team_config)
        
        with patch('builtins.open', mock_open(read_data=json.dumps(self.team_config))):
            settings = Settings()
            member = settings.get_team_member_by_username('alice.johnson')
            
            self.assertIsNotNone(member)
            self.assertEqual(member['name'], 'Alice Johnson')
    
    @patch('config.settings.load_dotenv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_get_team_member_by_username_not_found(self, mock_exists, mock_file, mock_load_dotenv):
        """Test finding a team member that doesn't exist."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.team_config)
        
        with patch('builtins.open', mock_open(read_data=json.dumps(self.team_config))):
            settings = Settings()
            member = settings.get_team_member_by_username('nonexistent.user')
            
            self.assertIsNone(member)
    
    @patch('config.settings.load_dotenv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_get_team_member_count(self, mock_exists, mock_file, mock_load_dotenv):
        """Test getting the team member count."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.team_config)
        
        with patch('builtins.open', mock_open(read_data=json.dumps(self.team_config))):
            settings = Settings()
            count = settings.get_team_member_count()
            
            self.assertEqual(count, 2)
    
    @patch('config.settings.load_dotenv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_to_dict_masks_sensitive_data(self, mock_exists, mock_file, mock_load_dotenv):
        """Test that to_dict masks sensitive information."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.team_config)
        
        with patch.dict(os.environ, self.env_vars):
            with patch('builtins.open', mock_open(read_data=json.dumps(self.team_config))):
                settings = Settings()
                settings_dict = settings.to_dict()
                
                # Sensitive fields should be masked
                self.assertEqual(settings_dict['jira_pat_token'], '***')
                self.assertEqual(settings_dict['mistral_api_key'], '***')
                self.assertEqual(settings_dict['slack_bot_token'], '***')
                
                # Non-sensitive fields should be present
                self.assertEqual(settings_dict['jira_url'], self.env_vars['JIRA_URL'])
                self.assertEqual(settings_dict['jira_project_key'], self.env_vars['JIRA_PROJECT_KEY'])
    
    @patch('config.settings.load_dotenv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_repr(self, mock_exists, mock_file, mock_load_dotenv):
        """Test string representation of Settings."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.team_config)
        
        with patch.dict(os.environ, self.env_vars):
            with patch('builtins.open', mock_open(read_data=json.dumps(self.team_config))):
                settings = Settings()
                repr_str = repr(settings)
                
                self.assertIn('Settings', repr_str)
                self.assertIn(self.env_vars['JIRA_URL'], repr_str)
    
    @patch('config.settings.load_dotenv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_str(self, mock_exists, mock_file, mock_load_dotenv):
        """Test human-readable string representation."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.team_config)
        
        with patch.dict(os.environ, self.env_vars):
            with patch('builtins.open', mock_open(read_data=json.dumps(self.team_config))):
                settings = Settings()
                str_repr = str(settings)
                
                self.assertIn('Settings', str_repr)
                self.assertIn('Team Members', str_repr)
    
    @patch('config.settings.load_dotenv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_get_settings_function(self, mock_exists, mock_file, mock_load_dotenv):
        """Test the get_settings convenience function."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.team_config)
        
        with patch('builtins.open', mock_open(read_data=json.dumps(self.team_config))):
            settings = get_settings()
            
            self.assertIsInstance(settings, Settings)
    
    @patch('config.settings.load_dotenv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_reload_team_members(self, mock_exists, mock_file, mock_load_dotenv):
        """Test reloading team members from configuration file."""
        mock_exists.return_value = True
        
        # Initial config
        initial_config = {
            'team_members': [
                {'name': 'Alice', 'jira_username': 'alice'}
            ]
        }
        
        # Updated config
        updated_config = {
            'team_members': [
                {'name': 'Alice', 'jira_username': 'alice'},
                {'name': 'Bob', 'jira_username': 'bob'}
            ]
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(initial_config))):
            settings = Settings()
            self.assertEqual(len(settings.team_members), 1)
        
        # Reload with updated config
        with patch('builtins.open', mock_open(read_data=json.dumps(updated_config))):
            settings.reload_team_members()
            self.assertEqual(len(settings.team_members), 2)
    
    def test_reset_instance(self):
        """Test resetting the singleton instance."""
        Settings.reset_instance()
        
        self.assertIsNone(Settings._instance)
        self.assertFalse(Settings._initialized)


if __name__ == '__main__':
    unittest.main()

# Made with Bob
