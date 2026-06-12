"""
Team Member model for JIRA automation system.

This module defines the TeamMember class that represents a team member
with their specializations, capacity, and availability.
"""

from typing import List, Dict, Any, Optional


class TeamMember:
    """
    Represents a team member with their skills and capacity.
    
    This class encapsulates team member information including their
    specializations, current workload, and availability for ticket assignment.
    
    Attributes:
        name: Full name of the team member
        jira_username: JIRA username for assignment
        specializations: List of areas of expertise (e.g., ['TRIRIGA', 'APIC'])
        current_ticket_count: Number of tickets currently assigned
        max_capacity: Maximum number of tickets the member can handle
        is_available: Whether the member is available for new assignments
    """
    
    def __init__(
        self,
        name: str,
        jira_username: str,
        specializations: Optional[List[str]] = None,
        current_ticket_count: int = 0,
        max_capacity: int = 5,
        is_available: bool = True
    ):
        """
        Initialize a TeamMember instance.
        
        Args:
            name: Full name of the team member
            jira_username: JIRA username for assignment
            specializations: List of expertise areas (default: empty list)
            current_ticket_count: Current number of assigned tickets (default: 0)
            max_capacity: Maximum ticket capacity (default: 5)
            is_available: Availability status (default: True)
        """
        self.name = name
        self.jira_username = jira_username
        self.specializations = specializations or []
        self.current_ticket_count = current_ticket_count
        self.max_capacity = max_capacity
        self.is_available = is_available
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert team member to dictionary representation.
        
        Returns:
            Dictionary containing all team member properties
        """
        return {
            'name': self.name,
            'jira_username': self.jira_username,
            'specializations': self.specializations,
            'current_ticket_count': self.current_ticket_count,
            'max_capacity': self.max_capacity,
            'is_available': self.is_available
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TeamMember':
        """
        Create a TeamMember instance from a dictionary.
        
        This method is useful for loading team members from configuration
        files or API responses.
        
        Args:
            data: Dictionary containing team member properties
            
        Returns:
            TeamMember instance populated with data from the dictionary
            
        Raises:
            KeyError: If required fields are missing from data
            TypeError: If data types are incorrect
        """
        # Validate required fields
        if 'name' not in data:
            raise KeyError("Missing required field: 'name'")
        if 'jira_username' not in data:
            raise KeyError("Missing required field: 'jira_username'")
        
        return cls(
            name=data['name'],
            jira_username=data['jira_username'],
            specializations=data.get('specializations', []),
            current_ticket_count=data.get('current_ticket_count', 0),
            max_capacity=data.get('max_capacity', 5),
            is_available=data.get('is_available', True)
        )
    
    def can_handle_category(self, category: str) -> bool:
        """
        Check if team member can handle a specific ticket category.
        
        This method checks if the given category matches any of the
        team member's specializations. The comparison is case-insensitive.
        
        Args:
            category: Ticket category to check (e.g., 'TRIRIGA', 'APIC')
            
        Returns:
            True if the member has the specialization, False otherwise
        """
        if not category:
            return False
        
        # Convert to uppercase for case-insensitive comparison
        category_upper = category.upper()
        
        # Check if category matches any specialization
        for specialization in self.specializations:
            if specialization.upper() == category_upper:
                return True
        
        return False
    
    def has_capacity(self) -> bool:
        """
        Check if team member can take more tickets.
        
        This method checks both availability status and current workload
        against maximum capacity.
        
        Returns:
            True if the member is available and has capacity, False otherwise
        """
        return self.is_available and self.current_ticket_count < self.max_capacity
    
    def assign_ticket(self) -> bool:
        """
        Assign a ticket to this team member.
        
        Increments the current ticket count if the member has capacity.
        
        Returns:
            True if ticket was assigned successfully, False otherwise
        """
        if self.has_capacity():
            self.current_ticket_count += 1
            return True
        return False
    
    def unassign_ticket(self) -> bool:
        """
        Remove a ticket assignment from this team member.
        
        Decrements the current ticket count if greater than zero.
        
        Returns:
            True if ticket was unassigned successfully, False otherwise
        """
        if self.current_ticket_count > 0:
            self.current_ticket_count -= 1
            return True
        return False
    
    def get_capacity_percentage(self) -> float:
        """
        Calculate the current capacity utilization as a percentage.
        
        Returns:
            Percentage of capacity used (0.0 to 100.0)
        """
        if self.max_capacity == 0:
            return 100.0
        return (self.current_ticket_count / self.max_capacity) * 100.0
    
    def set_availability(self, available: bool) -> None:
        """
        Set the availability status of the team member.
        
        Args:
            available: New availability status
        """
        self.is_available = available
    
    def __repr__(self) -> str:
        """String representation of the TeamMember."""
        return (
            f"TeamMember(name='{self.name}', "
            f"jira_username='{self.jira_username}', "
            f"specializations={self.specializations}, "
            f"capacity={self.current_ticket_count}/{self.max_capacity})"
        )
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        status = "Available" if self.is_available else "Unavailable"
        return (
            f"{self.name} ({self.jira_username}) - "
            f"{status} - {self.current_ticket_count}/{self.max_capacity} tickets - "
            f"Specializations: {', '.join(self.specializations) if self.specializations else 'None'}"
        )

# Made with Bob
