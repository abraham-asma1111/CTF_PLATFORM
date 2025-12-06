# Requirements Document

## Introduction

The CTF Event Management system enables administrators to create group competition events with a completely separate challenge architecture from regular individual challenges. When group mode is activated, users are redirected to the team section where they solve specially created group challenges that are managed independently from the regular challenge system.

## Glossary

- **CTF_Platform**: The main capture-the-flag competition platform
- **Group_Event**: A special competition event using separate group challenges
- **Regular_Challenges**: The default individual challenge system and database
- **Group_Challenges**: Separate challenge system and database for team competitions
- **Event_Administrator**: A user with administrative privileges to manage events
- **Team_Section**: The dedicated area where group challenges are managed and solved
- **Group_Mode**: When group competition is active and users are redirected to team section
- **Individual_Mode**: Default mode using regular challenges

## Requirements

### Requirement 1

**User Story:** As an Event_Administrator, I want to create and manage group challenges separately from regular challenges, so that I can set up team competitions with different architecture.

#### Acceptance Criteria

1. WHEN an Event_Administrator creates group challenges, THE CTF_Platform SHALL store them in a separate database from Regular_Challenges
2. WHEN managing Group_Challenges, THE Event_Administrator SHALL access them through the Team_Section interface
3. WHEN creating Group_Challenges, THE CTF_Platform SHALL provide different management tools than Regular_Challenges
4. WHEN Group_Challenges are created, THE CTF_Platform SHALL allow different scoring and submission systems
5. WHEN Event_Administrator sets up group competition, THE CTF_Platform SHALL make Group_Challenges available only in Team_Section

### Requirement 2

**User Story:** As an Event_Administrator, I want to activate group competition events, so that users can optionally participate in team-based challenges while regular challenges remain available.

#### Acceptance Criteria

1. WHEN an Event_Administrator activates a group event, THE CTF_Platform SHALL make Group_Challenges available in Team_Section
2. WHEN a group event is active, THE CTF_Platform SHALL continue providing access to Regular_Challenges
3. WHEN a group event is deactivated, THE CTF_Platform SHALL remove Group_Challenges from Team_Section
4. WHEN no group event is active, THE CTF_Platform SHALL operate with only Regular_Challenges available
5. WHEN a group event is active, THE CTF_Platform SHALL display group competition information in Team_Section

### Requirement 3

**User Story:** As a user, I want to see information about active group competitions, so that I can choose whether to participate in team challenges or continue with individual challenges.

#### Acceptance Criteria

1. WHEN a group event is active, THE CTF_Platform SHALL display group competition notifications on the main interface
2. WHEN a user navigates to Team_Section during active group event, THE CTF_Platform SHALL show group competition information
3. WHEN in Team_Section during group event, THE CTF_Platform SHALL display options to join or create teams for competition
4. WHEN a user chooses not to participate in group competition, THE CTF_Platform SHALL allow continued access to Regular_Challenges
5. WHEN users access Team_Section during group event, THE CTF_Platform SHALL show both team management and group challenge options

### Requirement 4

**User Story:** As a user, I want to solve group challenges in the team section with my team, so that I can participate in team-based competitions.

#### Acceptance Criteria

1. WHEN a user solves Group_Challenges, THE CTF_Platform SHALL award points using the separate group scoring system
2. WHEN team members solve Group_Challenges, THE CTF_Platform SHALL track team progress in the group database
3. WHEN accessing Group_Challenges, THE CTF_Platform SHALL display team collaboration features
4. WHEN Group_Challenges are completed, THE CTF_Platform SHALL update team leaderboards for the group event
5. WHEN group competition ends, THE CTF_Platform SHALL preserve group challenge results separately from regular challenge history