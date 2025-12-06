# Design Document

## Overview

The CTF Event Management system introduces a dual-architecture approach where regular individual challenges and group challenges operate as completely separate systems. The system provides administrators with the ability to activate group competition mode, which redirects users from the regular challenge system to a specialized team section with its own challenge database, scoring system, and management interface.

## Architecture

The system follows a dual-availability architecture with two coexisting challenge ecosystems:

1. **Regular Challenge System**: The existing individual challenge infrastructure (always available)
2. **Group Challenge System**: A separate challenge infrastructure accessed through the team section (available during group events)

The Event Management system acts as a controller that manages the availability of group challenges while maintaining continuous access to regular challenges, allowing users to choose their participation level.

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Admin Panel   │    │  Event Manager   │    │   User Interface│
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │Regular Chals│ │    │ │ Mode Switch  │ │    │ │Regular View │ │
│ └─────────────┘ │    │ │              │ │    │ └─────────────┘ │
│ ┌─────────────┐ │◄──►│ │ ┌──────────┐ │ │◄──►│ ┌─────────────┐ │
│ │Group Chals  │ │    │ │ │Individual│ │ │    │ │Team Section │ │
│ │(Team Section)│ │    │ │ │   Mode   │ │ │    │ │(Group Mode) │ │
│ └─────────────┘ │    │ │ └──────────┘ │ │    │ └─────────────┘ │
└─────────────────┘    │ │ ┌──────────┐ │ │    └─────────────────┘
                       │ │ │  Group   │ │ │
                       │ │ │   Mode   │ │ │
                       │ │ └──────────┘ │ │
                       │ └──────────────┘ │
                       └──────────────────┘
```

## Components and Interfaces

### 1. Event Management Component

**Purpose**: Controls competition mode switching and manages group events

**Key Interfaces**:
- `EventManager.activate_group_mode(event_id)`: Switches platform to group competition
- `EventManager.deactivate_group_mode()`: Returns platform to individual mode
- `EventManager.get_current_mode()`: Returns current competition mode
- `EventManager.is_group_mode_active()`: Boolean check for group mode status

### 2. Group Challenge System

**Purpose**: Manages challenges specifically for team competitions

**Key Interfaces**:
- `GroupChallengeManager.create_challenge(challenge_data)`: Creates group-specific challenges
- `GroupChallengeManager.get_team_challenges(team_id)`: Retrieves challenges for a team
- `GroupChallengeManager.submit_solution(team_id, challenge_id, solution)`: Handles team submissions
- `GroupScoring.calculate_team_points(team_id, challenge_id)`: Calculates group-specific scoring

### 3. Routing Controller

**Purpose**: Manages user redirection based on competition mode

**Key Interfaces**:
- `RoutingController.handle_challenge_access(user, challenge_id)`: Routes users to appropriate challenge system
- `RoutingController.redirect_to_team_section(user)`: Redirects users to team section during group mode
- `RoutingController.enforce_team_membership(user)`: Validates team membership for group challenges

### 4. UI Mode Manager

**Purpose**: Controls interface rendering based on active competition mode

**Key Interfaces**:
- `UIManager.render_competition_banner(mode)`: Displays current competition mode
- `UIManager.show_group_interface()`: Renders group competition UI in team section
- `UIManager.hide_regular_challenges()`: Disables regular challenge access during group mode

## Data Models

### Group Event Model

```python
class GroupEvent(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Event-specific settings
    point_multiplier = models.FloatField(default=1.0)
    max_teams = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'group_events'
```

### Group Challenge Model

```python
class GroupChallenge(models.Model):
    event = models.ForeignKey(GroupEvent, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    points = models.IntegerField()
    flag = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=20)
    
    # Group-specific fields
    requires_collaboration = models.BooleanField(default=True)
    max_attempts_per_team = models.IntegerField(default=10)
    
    class Meta:
        db_table = 'group_challenges'
```

### Group Submission Model

```python
class GroupSubmission(models.Model):
    challenge = models.ForeignKey(GroupChallenge, on_delete=models.CASCADE)
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE)
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    flag_submitted = models.CharField(max_length=255)
    is_correct = models.BooleanField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    points_awarded = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'group_submissions'
```

### Platform Mode Model

```python
class PlatformMode(models.Model):
    mode = models.CharField(max_length=20, choices=[
        ('individual', 'Individual Mode'),
        ('group', 'Group Mode')
    ], default='individual')
    active_event = models.ForeignKey(GroupEvent, null=True, blank=True, on_delete=models.SET_NULL)
    changed_at = models.DateTimeField(auto_now=True)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'platform_mode'
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After reviewing all identified properties, several can be consolidated to eliminate redundancy:

- Properties 2.1, 3.1, and 3.4 all relate to routing behavior and can be combined into a comprehensive routing property
- Properties 2.2 and 2.5 both deal with UI state during group mode and can be merged
- Properties 1.1 and 4.2 both verify data storage separation and can be consolidated
- Properties 2.3 and 2.4 form a round-trip property for mode switching

### Consolidated Properties

**Property 1: Data Storage Separation**
*For any* group challenge or submission, the data should be stored in group-specific database tables separate from regular challenge data
**Validates: Requirements 1.1, 4.2**

**Property 2: Optional Participation**
*For any* active group event, users should be able to access both regular challenges and group challenges (via team section) without forced redirection
**Validates: Requirements 2.2, 3.4**

**Property 3: Group Event Information Display**
*For any* active group event, the platform should display group competition information and options in the team section while maintaining regular challenge access
**Validates: Requirements 2.5, 3.2, 3.3**

**Property 4: Group Event Lifecycle**
*For any* group event activation and deactivation cycle, group challenges should appear and disappear from team section while regular challenges remain unaffected
**Validates: Requirements 2.1, 2.3, 2.4**

**Property 5: Access Control Enforcement**
*For any* user attempting to access group challenges, the system should enforce team membership requirements and proper permissions
**Validates: Requirements 1.2, 3.5**

**Property 6: Group Challenge Management Separation**
*For any* group challenge creation or management operation, it should use different tools and interfaces than regular challenges and be accessible only through team section
**Validates: Requirements 1.3, 1.5**

**Property 7: Group Scoring System Independence**
*For any* group challenge solution, points should be calculated using the separate group scoring system and update team leaderboards independently from regular challenges
**Validates: Requirements 1.4, 4.1, 4.4**

**Property 8: Group Challenge Display**
*For any* user redirected to team section during group mode, only group challenges should be displayed with appropriate collaboration features
**Validates: Requirements 3.2, 4.3**

**Property 9: Data Preservation Separation**
*For any* group competition that ends, results should be preserved separately from regular challenge history without interference
**Validates: Requirements 4.5**

## Error Handling

### Mode Switching Errors
- **Invalid Event Activation**: Validate event exists and has valid time ranges before activation
- **Concurrent Event Conflict**: Ensure only one group event can be active at a time
- **Database Connection Failures**: Graceful fallback to individual mode if group database is unavailable

### User Access Errors
- **Team Membership Validation**: Handle users without teams during group mode with clear messaging
- **Permission Denied**: Provide informative error messages for unauthorized access attempts
- **Session Management**: Handle mode switches during active user sessions

### Data Integrity Errors
- **Cross-System Data Leakage**: Prevent group challenge data from appearing in regular challenge queries
- **Scoring Conflicts**: Ensure group and regular scoring systems remain completely separate
- **Challenge Visibility**: Prevent group challenges from being accessible outside team section

## Testing Strategy

### Unit Testing Approach
Unit tests will focus on:
- Individual component functionality (EventManager, GroupChallengeManager, RoutingController)
- Database model validation and constraints
- Permission and access control logic
- UI component rendering in different modes

### Property-Based Testing Approach
Property-based tests will use **Django's built-in testing framework with Hypothesis** for generating test data. Each property-based test will run a minimum of 100 iterations to ensure comprehensive coverage.

Property-based tests will verify:
- Data storage separation across all possible challenge and submission combinations
- Routing behavior consistency across different user states and navigation patterns
- UI state management across all possible mode transitions
- Access control enforcement across various user permission combinations
- Scoring system independence across different challenge and team configurations

Each property-based test will be tagged with comments explicitly referencing the correctness property from this design document using the format: **Feature: ctf-event-management, Property {number}: {property_text}**

### Integration Testing
- End-to-end mode switching workflows
- Cross-system data isolation verification
- User experience flows during mode transitions
- Admin management workflows for group events

### Performance Testing
- Database query performance with separate challenge systems
- UI rendering performance during mode switches
- Concurrent user handling during group events