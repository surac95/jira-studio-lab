"""
Unit tests for WorkloadService.

Tests the workload management and intelligent ticket assignment functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

from services.workload_service import WorkloadService
from models.team_member import TeamMember
from models.ticket import Ticket
from config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create a mock Settings object with test team members."""
    settings = Mock(spec=Settings)
    settings.load_team_members.return_value = [
        {
            'name': 'Alice Johnson',
            'jira_username': 'alice.johnson',
            'specializations': ['TRIRIGA', 'APPC'],
            'current_ticket_count': 2,
            'max_capacity': 5,
            'is_available': True
        },
        {
            'name': 'Bob Smith',
            'jira_username': 'bob.smith',
            'specializations': ['APIC', 'APPC'],
            'current_ticket_count': 4,
            'max_capacity': 5,
            'is_available': True
        },
        {
            'name': 'Charlie Brown',
            'jira_username': 'charlie.brown',
            'specializations': ['TRIRIGA'],
            'current_ticket_count': 0,
            'max_capacity': 5,
            'is_available': True
        },
        {
            'name': 'Diana Prince',
            'jira_username': 'diana.prince',
            'specializations': ['APIC'],
            'current_ticket_count': 3,
            'max_capacity': 5,
            'is_available': False  # Not available
        },
        {
            'name': 'Eve Adams',
            'jira_username': 'eve.adams',
            'specializations': ['TRIRIGA', 'APIC'],
            'current_ticket_count': 5,
            'max_capacity': 5,
            'is_available': True  # At capacity
        }
    ]
    return settings


@pytest.fixture
def workload_service(mock_settings):
    """Create a WorkloadService instance with mock settings."""
    with patch('services.workload_service.get_logger'):
        service = WorkloadService(mock_settings)
    return service


@pytest.fixture
def sample_ticket():
    """Create a sample ticket for testing."""
    return Ticket(
        key='TEST-123',
        summary='Test ticket',
        description='Test description',
        priority='High'
    )


class TestWorkloadServiceInitialization:
    """Test WorkloadService initialization."""
    
    def test_initialization_success(self, mock_settings):
        """Test successful initialization with valid settings."""
        with patch('services.workload_service.get_logger'):
            service = WorkloadService(mock_settings)
        
        assert service.settings == mock_settings
        assert len(service.team_members) == 5
        assert 'alice.johnson' in service.team_members
        assert 'bob.smith' in service.team_members
    
    def test_team_members_loaded_correctly(self, workload_service):
        """Test that team members are loaded with correct attributes."""
        alice = workload_service.team_members['alice.johnson']
        
        assert alice.name == 'Alice Johnson'
        assert alice.jira_username == 'alice.johnson'
        assert 'TRIRIGA' in alice.specializations
        assert alice.current_ticket_count == 2
        assert alice.max_capacity == 5
        assert alice.is_available is True
    
    def test_invalid_team_member_data_skipped(self, mock_settings):
        """Test that invalid team member data is skipped gracefully."""
        mock_settings.load_team_members.return_value = [
            {
                'name': 'Valid User',
                'jira_username': 'valid.user',
                'specializations': ['TRIRIGA']
            },
            {
                # Missing required 'jira_username' field
                'name': 'Invalid User',
                'specializations': ['APIC']
            }
        ]
        
        with patch('services.workload_service.get_logger'):
            service = WorkloadService(mock_settings)
        
        # Only valid user should be loaded
        assert len(service.team_members) == 1
        assert 'valid.user' in service.team_members


class TestAssignTicket:
    """Test ticket assignment functionality."""
    
    def test_assign_to_member_with_lowest_workload(self, workload_service, sample_ticket):
        """Test that ticket is assigned to member with lowest workload."""
        # Charlie has 0 tickets, Alice has 2 - both have TRIRIGA specialization
        assignee = workload_service.assign_ticket(sample_ticket, 'TRIRIGA')
        
        assert assignee is not None
        assert assignee.jira_username == 'charlie.brown'
        assert assignee.current_ticket_count == 0
    
    def test_assign_filters_by_specialization(self, workload_service, sample_ticket):
        """Test that only members with matching specialization are considered."""
        # Only Bob has APIC specialization and is available with capacity
        assignee = workload_service.assign_ticket(sample_ticket, 'APIC')
        
        assert assignee is not None
        assert assignee.jira_username == 'bob.smith'
        assert 'APIC' in assignee.specializations
    
    def test_assign_filters_by_availability(self, workload_service, sample_ticket):
        """Test that unavailable members are not assigned tickets."""
        # Diana has APIC but is not available
        # Bob should be assigned instead
        assignee = workload_service.assign_ticket(sample_ticket, 'APIC')
        
        assert assignee is not None
        assert assignee.jira_username == 'bob.smith'
        assert assignee.is_available is True
    
    def test_assign_filters_by_capacity(self, workload_service, sample_ticket):
        """Test that members at capacity are not assigned tickets."""
        # Eve has TRIRIGA but is at capacity (5/5)
        # Should assign to Charlie (0/5) or Alice (2/5)
        assignee = workload_service.assign_ticket(sample_ticket, 'TRIRIGA')
        
        assert assignee is not None
        assert assignee.jira_username in ['charlie.brown', 'alice.johnson']
        assert assignee.has_capacity() is True
    
    def test_assign_returns_none_when_no_suitable_member(self, workload_service, sample_ticket):
        """Test that None is returned when no suitable member is found."""
        # No one has 'UNKNOWN' specialization
        assignee = workload_service.assign_ticket(sample_ticket, 'UNKNOWN')
        
        assert assignee is None
    
    def test_assign_case_insensitive_category(self, workload_service, sample_ticket):
        """Test that category matching is case-insensitive."""
        # Test with lowercase category
        assignee = workload_service.assign_ticket(sample_ticket, 'tririga')
        
        assert assignee is not None
        assert 'TRIRIGA' in assignee.specializations
    
    def test_assign_thread_safe(self, workload_service, sample_ticket):
        """Test that assignment is thread-safe."""
        # This is a basic test - full thread safety would require concurrent testing
        assignee1 = workload_service.assign_ticket(sample_ticket, 'TRIRIGA')
        assignee2 = workload_service.assign_ticket(sample_ticket, 'TRIRIGA')
        
        assert assignee1 is not None
        assert assignee2 is not None


class TestGetTeamWorkload:
    """Test team workload retrieval."""
    
    def test_get_team_workload_returns_all_members(self, workload_service):
        """Test that workload info is returned for all members."""
        workload = workload_service.get_team_workload()
        
        assert len(workload) == 5
        assert all('name' in member for member in workload)
        assert all('jira_username' in member for member in workload)
    
    def test_get_team_workload_includes_correct_fields(self, workload_service):
        """Test that workload info includes all required fields."""
        workload = workload_service.get_team_workload()
        alice_info = next(m for m in workload if m['jira_username'] == 'alice.johnson')
        
        assert alice_info['name'] == 'Alice Johnson'
        assert alice_info['specializations'] == ['TRIRIGA', 'APPC']
        assert alice_info['current_ticket_count'] == 2
        assert alice_info['max_capacity'] == 5
        assert alice_info['capacity_percentage'] == 40.0
        assert alice_info['is_available'] is True
        assert alice_info['has_capacity'] is True
    
    def test_get_team_workload_calculates_capacity_percentage(self, workload_service):
        """Test that capacity percentage is calculated correctly."""
        workload = workload_service.get_team_workload()
        eve_info = next(m for m in workload if m['jira_username'] == 'eve.adams')
        
        assert eve_info['capacity_percentage'] == 100.0
        assert eve_info['has_capacity'] is False


class TestGetAvailableMembers:
    """Test available members retrieval."""
    
    def test_get_available_members_without_category(self, workload_service):
        """Test getting all available members without category filter."""
        available = workload_service.get_available_members()
        
        # Alice (2/5), Bob (4/5), Charlie (0/5) are available with capacity
        # Diana is not available, Eve is at capacity
        assert len(available) == 3
        usernames = [m.jira_username for m in available]
        assert 'alice.johnson' in usernames
        assert 'bob.smith' in usernames
        assert 'charlie.brown' in usernames
    
    def test_get_available_members_with_category(self, workload_service):
        """Test getting available members filtered by category."""
        available = workload_service.get_available_members('TRIRIGA')
        
        # Alice and Charlie have TRIRIGA and are available with capacity
        assert len(available) == 2
        usernames = [m.jira_username for m in available]
        assert 'alice.johnson' in usernames
        assert 'charlie.brown' in usernames
    
    def test_get_available_members_excludes_unavailable(self, workload_service):
        """Test that unavailable members are excluded."""
        available = workload_service.get_available_members('APIC')
        
        # Diana has APIC but is not available
        usernames = [m.jira_username for m in available]
        assert 'diana.prince' not in usernames
    
    def test_get_available_members_excludes_at_capacity(self, workload_service):
        """Test that members at capacity are excluded."""
        available = workload_service.get_available_members('TRIRIGA')
        
        # Eve has TRIRIGA but is at capacity
        usernames = [m.jira_username for m in available]
        assert 'eve.adams' not in usernames


class TestUpdateMemberWorkload:
    """Test workload update functionality."""
    
    def test_update_workload_increment(self, workload_service):
        """Test incrementing a member's workload."""
        initial_count = workload_service.team_members['alice.johnson'].current_ticket_count
        
        success = workload_service.update_member_workload('alice.johnson', 1)
        
        assert success is True
        assert workload_service.team_members['alice.johnson'].current_ticket_count == initial_count + 1
    
    def test_update_workload_decrement(self, workload_service):
        """Test decrementing a member's workload."""
        initial_count = workload_service.team_members['alice.johnson'].current_ticket_count
        
        success = workload_service.update_member_workload('alice.johnson', -1)
        
        assert success is True
        assert workload_service.team_members['alice.johnson'].current_ticket_count == initial_count - 1
    
    def test_update_workload_at_capacity_fails(self, workload_service):
        """Test that incrementing at capacity fails."""
        # Eve is at capacity (5/5)
        success = workload_service.update_member_workload('eve.adams', 1)
        
        assert success is False
        assert workload_service.team_members['eve.adams'].current_ticket_count == 5
    
    def test_update_workload_at_zero_fails(self, workload_service):
        """Test that decrementing at zero fails."""
        # Charlie has 0 tickets
        success = workload_service.update_member_workload('charlie.brown', -1)
        
        assert success is False
        assert workload_service.team_members['charlie.brown'].current_ticket_count == 0
    
    def test_update_workload_invalid_username(self, workload_service):
        """Test that updating non-existent member returns False."""
        success = workload_service.update_member_workload('invalid.user', 1)
        
        assert success is False
    
    def test_update_workload_zero_increment(self, workload_service):
        """Test that zero increment returns True without changes."""
        initial_count = workload_service.team_members['alice.johnson'].current_ticket_count
        
        success = workload_service.update_member_workload('alice.johnson', 0)
        
        assert success is True
        assert workload_service.team_members['alice.johnson'].current_ticket_count == initial_count


class TestGetMemberByUsername:
    """Test member retrieval by username."""
    
    def test_get_member_by_username_success(self, workload_service):
        """Test getting a member by valid username."""
        member = workload_service.get_member_by_username('alice.johnson')
        
        assert member is not None
        assert member.name == 'Alice Johnson'
        assert member.jira_username == 'alice.johnson'
    
    def test_get_member_by_username_not_found(self, workload_service):
        """Test getting a member by invalid username."""
        member = workload_service.get_member_by_username('invalid.user')
        
        assert member is None


class TestGetAssignmentStatistics:
    """Test assignment statistics calculation."""
    
    def test_get_statistics_calculates_totals(self, workload_service):
        """Test that statistics calculates total capacity correctly."""
        stats = workload_service.get_assignment_statistics()
        
        # 5 members * 5 capacity = 25 total
        assert stats['total_capacity'] == 25
        # 2 + 4 + 0 + 3 + 5 = 14 used
        assert stats['used_capacity'] == 14
        # 25 - 14 = 11 available
        assert stats['available_capacity'] == 11
        # 14/25 = 56%
        assert stats['capacity_percentage'] == pytest.approx(56.0, rel=0.1)
    
    def test_get_statistics_counts_team_size(self, workload_service):
        """Test that statistics includes team size."""
        stats = workload_service.get_assignment_statistics()
        
        assert stats['team_size'] == 5
    
    def test_get_statistics_counts_available_members(self, workload_service):
        """Test that statistics counts available members correctly."""
        stats = workload_service.get_assignment_statistics()
        
        # Alice, Bob, Charlie have capacity (Diana unavailable, Eve at capacity)
        assert stats['available_members'] == 3
    
    def test_get_statistics_by_category(self, workload_service):
        """Test that statistics includes breakdown by category."""
        stats = workload_service.get_assignment_statistics()
        
        assert 'by_category' in stats
        assert 'TRIRIGA' in stats['by_category']
        assert 'APIC' in stats['by_category']
        assert 'APPC' in stats['by_category']
    
    def test_get_statistics_category_details(self, workload_service):
        """Test that category statistics include correct details."""
        stats = workload_service.get_assignment_statistics()
        tririga_stats = stats['by_category']['TRIRIGA']
        
        # Alice (TRIRIGA, APPC): 2/5
        # Charlie (TRIRIGA): 0/5
        # Eve (TRIRIGA, APIC): 5/5
        # Total: 15 capacity, 7 used
        assert tririga_stats['total_capacity'] == 15
        assert tririga_stats['used_capacity'] == 7
        assert tririga_stats['member_count'] == 3
        assert tririga_stats['available_members'] == 2  # Alice and Charlie


class TestReloadTeamMembers:
    """Test team member reloading."""
    
    def test_reload_team_members(self, workload_service, mock_settings):
        """Test that team members can be reloaded."""
        # Modify a member's workload
        workload_service.update_member_workload('alice.johnson', 1)
        initial_count = workload_service.team_members['alice.johnson'].current_ticket_count
        
        # Reload should reset to configured values
        workload_service.reload_team_members()
        
        # Count should be back to original (2)
        assert workload_service.team_members['alice.johnson'].current_ticket_count == 2


class TestStringRepresentations:
    """Test string representations."""
    
    def test_repr(self, workload_service):
        """Test __repr__ method."""
        repr_str = repr(workload_service)
        
        assert 'WorkloadService' in repr_str
        assert 'team_size=5' in repr_str
    
    def test_str(self, workload_service):
        """Test __str__ method."""
        str_repr = str(workload_service)
        
        assert 'WorkloadService' in str_repr
        assert '5 members' in str_repr
        assert 'capacity used' in str_repr


# Made with Bob