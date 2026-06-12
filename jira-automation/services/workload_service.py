"""
Workload service for intelligent ticket assignment based on team capacity.

This module provides workload management and intelligent ticket assignment
based on team member specializations, availability, and current capacity.
"""

import threading
from typing import List, Dict, Any, Optional

from config.settings import Settings
from models.team_member import TeamMember
from utils.logger import get_logger


class WorkloadService:
    """
    Service for managing team workload and intelligent ticket assignment.
    
    This service maintains team member workload state and provides methods
    for assigning tickets based on specialization, availability, and capacity.
    
    Attributes:
        settings: Application settings instance
        team_members: Dictionary mapping username to TeamMember objects
        logger: Logger instance for this service
        lock: Thread lock for thread-safe operations
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the workload service with team members from settings.
        
        Args:
            settings: Settings instance containing team member configuration
        """
        self.settings = settings
        self.logger = get_logger(__name__)
        self.lock = threading.Lock()
        
        # Load team members from settings
        self.team_members: Dict[str, TeamMember] = {}
        self._load_team_members()
        
        self.logger.info(
            f"WorkloadService initialized with {len(self.team_members)} team members"
        )
    
    def _load_team_members(self) -> None:
        """
        Load team members from settings into TeamMember objects.
        
        Creates TeamMember instances from the configuration and stores them
        in a dictionary keyed by JIRA username for quick lookup.
        """
        team_data = self.settings.load_team_members()
        
        for member_data in team_data:
            try:
                member = TeamMember.from_dict(member_data)
                self.team_members[member.jira_username] = member
                self.logger.debug(f"Loaded team member: {member.name}")
            except (KeyError, TypeError) as e:
                self.logger.error(
                    f"Failed to load team member from data {member_data}: {e}"
                )
        
        self.logger.info(f"Loaded {len(self.team_members)} team members")
    
    def assign_ticket(
        self,
        ticket: Any,
        category: str
    ) -> Optional[TeamMember]:
        """
        Assign a ticket to the best available team member.
        
        The assignment algorithm:
        1. Filter team members by specialization (can handle category)
        2. Filter by availability (is_available = True)
        3. Filter by capacity (has_capacity() = True)
        4. Sort by current workload (ascending)
        5. Return team member with lowest workload
        
        Args:
            ticket: Ticket object to assign
            category: Category of the ticket (TRIRIGA/APIC/APPC)
            
        Returns:
            TeamMember object if assignment successful, None otherwise
            
        Example:
            >>> workload_service = WorkloadService(settings)
            >>> ticket = Ticket(key="PROJ-123", summary="TRIRIGA issue")
            >>> assignee = workload_service.assign_ticket(ticket, "TRIRIGA")
            >>> if assignee:
            ...     print(f"Assigned to {assignee.name}")
        """
        with self.lock:
            self.logger.info(
                f"Attempting to assign ticket {ticket.key} (category: {category})"
            )
            
            # Step 1: Filter by specialization
            specialized_members = [
                member for member in self.team_members.values()
                if member.can_handle_category(category)
            ]
            
            if not specialized_members:
                self.logger.warning(
                    f"No team members with {category} specialization found"
                )
                return None
            
            self.logger.debug(
                f"Found {len(specialized_members)} members with {category} specialization"
            )
            
            # Step 2 & 3: Filter by availability and capacity
            available_members = [
                member for member in specialized_members
                if member.is_available and member.has_capacity()
            ]
            
            if not available_members:
                self.logger.warning(
                    f"No available team members with capacity for {category}"
                )
                return None
            
            self.logger.debug(
                f"Found {len(available_members)} available members with capacity"
            )
            
            # Step 4: Sort by current workload (ascending)
            available_members.sort(key=lambda m: m.current_ticket_count)
            
            # Step 5: Return member with lowest workload
            assignee = available_members[0]
            
            self.logger.info(
                f"Assigned ticket {ticket.key} to {assignee.name} "
                f"(current load: {assignee.current_ticket_count}/{assignee.max_capacity})"
            )
            
            return assignee
    
    def get_team_workload(self) -> List[Dict[str, Any]]:
        """
        Get current workload information for all team members.
        
        Returns:
            List of dictionaries containing member info and workload stats:
                - name: Team member name
                - jira_username: JIRA username
                - specializations: List of specializations
                - current_ticket_count: Current number of tickets
                - max_capacity: Maximum capacity
                - capacity_percentage: Percentage of capacity used
                - is_available: Availability status
                - has_capacity: Whether member can take more tickets
                
        Example:
            >>> workload_service = WorkloadService(settings)
            >>> workload = workload_service.get_team_workload()
            >>> for member in workload:
            ...     print(f"{member['name']}: {member['capacity_percentage']:.1f}%")
        """
        with self.lock:
            workload_info = []
            
            for member in self.team_members.values():
                workload_info.append({
                    'name': member.name,
                    'jira_username': member.jira_username,
                    'specializations': member.specializations,
                    'current_ticket_count': member.current_ticket_count,
                    'max_capacity': member.max_capacity,
                    'capacity_percentage': member.get_capacity_percentage(),
                    'is_available': member.is_available,
                    'has_capacity': member.has_capacity()
                })
            
            return workload_info
    
    def get_available_members(
        self,
        category: Optional[str] = None
    ) -> List[TeamMember]:
        """
        Get list of available team members, optionally filtered by category.
        
        Args:
            category: Optional category to filter by (TRIRIGA/APIC/APPC)
            
        Returns:
            List of TeamMember objects that are available and have capacity
            
        Example:
            >>> workload_service = WorkloadService(settings)
            >>> available = workload_service.get_available_members("TRIRIGA")
            >>> print(f"{len(available)} TRIRIGA specialists available")
        """
        with self.lock:
            available = [
                member for member in self.team_members.values()
                if member.is_available and member.has_capacity()
            ]
            
            # Filter by category if specified
            if category:
                available = [
                    member for member in available
                    if member.can_handle_category(category)
                ]
            
            self.logger.debug(
                f"Found {len(available)} available members"
                + (f" for category {category}" if category else "")
            )
            
            return available
    
    def update_member_workload(
        self,
        username: str,
        increment: int
    ) -> bool:
        """
        Update a team member's ticket count.
        
        Args:
            username: JIRA username of the team member
            increment: Amount to change ticket count (+1 or -1)
            
        Returns:
            True if update successful, False if member not found
            
        Example:
            >>> workload_service = WorkloadService(settings)
            >>> # Assign a ticket
            >>> workload_service.update_member_workload("john.doe", 1)
            >>> # Complete a ticket
            >>> workload_service.update_member_workload("john.doe", -1)
        """
        with self.lock:
            member = self.team_members.get(username)
            
            if not member:
                self.logger.error(f"Team member not found: {username}")
                return False
            
            old_count = member.current_ticket_count
            
            if increment > 0:
                # Assign ticket
                success = member.assign_ticket()
                if success:
                    self.logger.info(
                        f"Increased workload for {member.name}: "
                        f"{old_count} -> {member.current_ticket_count}"
                    )
                else:
                    self.logger.warning(
                        f"Failed to assign ticket to {member.name} - at capacity"
                    )
                return success
            elif increment < 0:
                # Unassign ticket
                success = member.unassign_ticket()
                if success:
                    self.logger.info(
                        f"Decreased workload for {member.name}: "
                        f"{old_count} -> {member.current_ticket_count}"
                    )
                else:
                    self.logger.warning(
                        f"Failed to unassign ticket from {member.name} - already at 0"
                    )
                return success
            else:
                # No change
                return True
    
    def get_member_by_username(self, username: str) -> Optional[TeamMember]:
        """
        Get a team member by their JIRA username.
        
        Args:
            username: JIRA username to search for
            
        Returns:
            TeamMember object if found, None otherwise
            
        Example:
            >>> workload_service = WorkloadService(settings)
            >>> member = workload_service.get_member_by_username("john.doe")
            >>> if member:
            ...     print(f"Found: {member.name}")
        """
        with self.lock:
            return self.team_members.get(username)
    
    def get_assignment_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about team capacity and assignments.
        
        Returns:
            Dictionary containing:
                - total_capacity: Total ticket capacity across all members
                - used_capacity: Total tickets currently assigned
                - available_capacity: Remaining capacity
                - capacity_percentage: Overall capacity utilization percentage
                - by_category: Breakdown by specialization category
                - team_size: Number of team members
                - available_members: Number of members with capacity
                
        Example:
            >>> workload_service = WorkloadService(settings)
            >>> stats = workload_service.get_assignment_statistics()
            >>> print(f"Team capacity: {stats['capacity_percentage']:.1f}%")
        """
        with self.lock:
            total_capacity = 0
            used_capacity = 0
            category_stats = {}
            available_count = 0
            
            for member in self.team_members.values():
                total_capacity += member.max_capacity
                used_capacity += member.current_ticket_count
                
                if member.has_capacity():
                    available_count += 1
                
                # Track by specialization
                for spec in member.specializations:
                    if spec not in category_stats:
                        category_stats[spec] = {
                            'total_capacity': 0,
                            'used_capacity': 0,
                            'member_count': 0,
                            'available_members': 0
                        }
                    
                    category_stats[spec]['total_capacity'] += member.max_capacity
                    category_stats[spec]['used_capacity'] += member.current_ticket_count
                    category_stats[spec]['member_count'] += 1
                    
                    if member.has_capacity():
                        category_stats[spec]['available_members'] += 1
            
            available_capacity = total_capacity - used_capacity
            capacity_percentage = (
                (used_capacity / total_capacity * 100) if total_capacity > 0 else 0
            )
            
            # Calculate percentages for each category
            for spec, stats in category_stats.items():
                if stats['total_capacity'] > 0:
                    stats['capacity_percentage'] = (
                        stats['used_capacity'] / stats['total_capacity'] * 100
                    )
                else:
                    stats['capacity_percentage'] = 0
                stats['available_capacity'] = (
                    stats['total_capacity'] - stats['used_capacity']
                )
            
            return {
                'total_capacity': total_capacity,
                'used_capacity': used_capacity,
                'available_capacity': available_capacity,
                'capacity_percentage': capacity_percentage,
                'team_size': len(self.team_members),
                'available_members': available_count,
                'by_category': category_stats
            }
    
    def reload_team_members(self) -> None:
        """
        Reload team members from settings.
        
        This is useful when the team configuration has been updated
        and needs to be reloaded without restarting the service.
        
        Note: This will reset all workload counters to their configured values.
        """
        with self.lock:
            self.logger.info("Reloading team members from settings")
            self.team_members.clear()
            self._load_team_members()
            self.logger.info("Team members reloaded successfully")
    
    def __repr__(self) -> str:
        """String representation of WorkloadService."""
        return f"WorkloadService(team_size={len(self.team_members)})"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        stats = self.get_assignment_statistics()
        return (
            f"WorkloadService: {stats['team_size']} members, "
            f"{stats['used_capacity']}/{stats['total_capacity']} capacity used "
            f"({stats['capacity_percentage']:.1f}%)"
        )


# Made with Bob