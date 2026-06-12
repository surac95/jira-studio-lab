"""
Unit tests for the TeamMember model.

This module contains comprehensive tests for the TeamMember class,
including initialization, capacity management, and specialization checks.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.team_member import TeamMember


class TestTeamMember(unittest.TestCase):
    """Test cases for the TeamMember class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_name = "John Doe"
        self.test_username = "john.doe"
        self.test_specializations = ["TRIRIGA", "APIC", "Python"]
        self.test_current_count = 2
        self.test_max_capacity = 5
    
    def test_team_member_initialization_with_all_params(self):
        """Test team member initialization with all parameters."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            specializations=self.test_specializations,
            current_ticket_count=self.test_current_count,
            max_capacity=self.test_max_capacity,
            is_available=True
        )
        
        self.assertEqual(member.name, self.test_name)
        self.assertEqual(member.jira_username, self.test_username)
        self.assertEqual(member.specializations, self.test_specializations)
        self.assertEqual(member.current_ticket_count, self.test_current_count)
        self.assertEqual(member.max_capacity, self.test_max_capacity)
        self.assertTrue(member.is_available)
    
    def test_team_member_initialization_with_defaults(self):
        """Test team member initialization with default values."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username
        )
        
        self.assertEqual(member.name, self.test_name)
        self.assertEqual(member.jira_username, self.test_username)
        self.assertEqual(member.specializations, [])
        self.assertEqual(member.current_ticket_count, 0)
        self.assertEqual(member.max_capacity, 5)
        self.assertTrue(member.is_available)
    
    def test_to_dict(self):
        """Test conversion of team member to dictionary."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            specializations=self.test_specializations,
            current_ticket_count=self.test_current_count,
            max_capacity=self.test_max_capacity,
            is_available=True
        )
        
        member_dict = member.to_dict()
        
        self.assertEqual(member_dict['name'], self.test_name)
        self.assertEqual(member_dict['jira_username'], self.test_username)
        self.assertEqual(member_dict['specializations'], self.test_specializations)
        self.assertEqual(member_dict['current_ticket_count'], self.test_current_count)
        self.assertEqual(member_dict['max_capacity'], self.test_max_capacity)
        self.assertTrue(member_dict['is_available'])
    
    def test_from_dict_complete(self):
        """Test creating team member from dictionary with all fields."""
        data = {
            'name': self.test_name,
            'jira_username': self.test_username,
            'specializations': self.test_specializations,
            'current_ticket_count': self.test_current_count,
            'max_capacity': self.test_max_capacity,
            'is_available': True
        }
        
        member = TeamMember.from_dict(data)
        
        self.assertEqual(member.name, self.test_name)
        self.assertEqual(member.jira_username, self.test_username)
        self.assertEqual(member.specializations, self.test_specializations)
        self.assertEqual(member.current_ticket_count, self.test_current_count)
        self.assertEqual(member.max_capacity, self.test_max_capacity)
        self.assertTrue(member.is_available)
    
    def test_from_dict_minimal(self):
        """Test creating team member from dictionary with minimal fields."""
        data = {
            'name': self.test_name,
            'jira_username': self.test_username
        }
        
        member = TeamMember.from_dict(data)
        
        self.assertEqual(member.name, self.test_name)
        self.assertEqual(member.jira_username, self.test_username)
        self.assertEqual(member.specializations, [])
        self.assertEqual(member.current_ticket_count, 0)
        self.assertEqual(member.max_capacity, 5)
        self.assertTrue(member.is_available)
    
    def test_from_dict_missing_name(self):
        """Test that from_dict raises KeyError when name is missing."""
        data = {
            'jira_username': self.test_username
        }
        
        with self.assertRaises(KeyError) as context:
            TeamMember.from_dict(data)
        
        self.assertIn('name', str(context.exception))
    
    def test_from_dict_missing_username(self):
        """Test that from_dict raises KeyError when username is missing."""
        data = {
            'name': self.test_name
        }
        
        with self.assertRaises(KeyError) as context:
            TeamMember.from_dict(data)
        
        self.assertIn('jira_username', str(context.exception))
    
    def test_can_handle_category_exact_match(self):
        """Test category handling with exact match."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            specializations=["TRIRIGA", "APIC"]
        )
        
        self.assertTrue(member.can_handle_category("TRIRIGA"))
        self.assertTrue(member.can_handle_category("APIC"))
    
    def test_can_handle_category_case_insensitive(self):
        """Test category handling is case-insensitive."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            specializations=["TRIRIGA", "APIC"]
        )
        
        self.assertTrue(member.can_handle_category("tririga"))
        self.assertTrue(member.can_handle_category("Tririga"))
        self.assertTrue(member.can_handle_category("apic"))
        self.assertTrue(member.can_handle_category("Apic"))
    
    def test_can_handle_category_no_match(self):
        """Test category handling when no match exists."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            specializations=["TRIRIGA", "APIC"]
        )
        
        self.assertFalse(member.can_handle_category("Python"))
        self.assertFalse(member.can_handle_category("Java"))
    
    def test_can_handle_category_empty_string(self):
        """Test category handling with empty string."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            specializations=["TRIRIGA"]
        )
        
        self.assertFalse(member.can_handle_category(""))
    
    def test_can_handle_category_no_specializations(self):
        """Test category handling when member has no specializations."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            specializations=[]
        )
        
        self.assertFalse(member.can_handle_category("TRIRIGA"))
    
    def test_has_capacity_available_with_space(self):
        """Test has_capacity when member is available and has space."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            current_ticket_count=2,
            max_capacity=5,
            is_available=True
        )
        
        self.assertTrue(member.has_capacity())
    
    def test_has_capacity_at_max(self):
        """Test has_capacity when member is at maximum capacity."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            current_ticket_count=5,
            max_capacity=5,
            is_available=True
        )
        
        self.assertFalse(member.has_capacity())
    
    def test_has_capacity_unavailable(self):
        """Test has_capacity when member is unavailable."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            current_ticket_count=2,
            max_capacity=5,
            is_available=False
        )
        
        self.assertFalse(member.has_capacity())
    
    def test_assign_ticket_success(self):
        """Test successful ticket assignment."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            current_ticket_count=2,
            max_capacity=5
        )
        
        result = member.assign_ticket()
        
        self.assertTrue(result)
        self.assertEqual(member.current_ticket_count, 3)
    
    def test_assign_ticket_at_capacity(self):
        """Test ticket assignment when at capacity."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            current_ticket_count=5,
            max_capacity=5
        )
        
        result = member.assign_ticket()
        
        self.assertFalse(result)
        self.assertEqual(member.current_ticket_count, 5)
    
    def test_unassign_ticket_success(self):
        """Test successful ticket unassignment."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            current_ticket_count=3,
            max_capacity=5
        )
        
        result = member.unassign_ticket()
        
        self.assertTrue(result)
        self.assertEqual(member.current_ticket_count, 2)
    
    def test_unassign_ticket_at_zero(self):
        """Test ticket unassignment when count is zero."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            current_ticket_count=0,
            max_capacity=5
        )
        
        result = member.unassign_ticket()
        
        self.assertFalse(result)
        self.assertEqual(member.current_ticket_count, 0)
    
    def test_get_capacity_percentage(self):
        """Test capacity percentage calculation."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            current_ticket_count=3,
            max_capacity=5
        )
        
        percentage = member.get_capacity_percentage()
        
        self.assertEqual(percentage, 60.0)
    
    def test_get_capacity_percentage_zero_max(self):
        """Test capacity percentage when max capacity is zero."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            current_ticket_count=0,
            max_capacity=0
        )
        
        percentage = member.get_capacity_percentage()
        
        self.assertEqual(percentage, 100.0)
    
    def test_get_capacity_percentage_full(self):
        """Test capacity percentage when at full capacity."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            current_ticket_count=5,
            max_capacity=5
        )
        
        percentage = member.get_capacity_percentage()
        
        self.assertEqual(percentage, 100.0)
    
    def test_set_availability(self):
        """Test setting availability status."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            is_available=True
        )
        
        member.set_availability(False)
        self.assertFalse(member.is_available)
        
        member.set_availability(True)
        self.assertTrue(member.is_available)
    
    def test_repr(self):
        """Test string representation of team member."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            specializations=["TRIRIGA"],
            current_ticket_count=2,
            max_capacity=5
        )
        
        repr_str = repr(member)
        
        self.assertIn(self.test_name, repr_str)
        self.assertIn(self.test_username, repr_str)
        self.assertIn("TeamMember", repr_str)
        self.assertIn("2/5", repr_str)
    
    def test_str(self):
        """Test human-readable string representation."""
        member = TeamMember(
            name=self.test_name,
            jira_username=self.test_username,
            specializations=["TRIRIGA", "APIC"],
            current_ticket_count=2,
            max_capacity=5,
            is_available=True
        )
        
        str_repr = str(member)
        
        self.assertIn(self.test_name, str_repr)
        self.assertIn(self.test_username, str_repr)
        self.assertIn("Available", str_repr)
        self.assertIn("2/5", str_repr)
        self.assertIn("TRIRIGA", str_repr)
        self.assertIn("APIC", str_repr)


if __name__ == '__main__':
    unittest.main()

# Made with Bob
