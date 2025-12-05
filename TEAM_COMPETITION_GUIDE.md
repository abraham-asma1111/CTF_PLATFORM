# Team Competition Guide

## Overview

The CTF platform now supports **team-based competition** in addition to individual competition. Users can form teams, collaborate, and compete together for higher rankings.

## Key Features

### Team Structure
- **Team Size**: 2-5 members per team
- **Minimum Members**: Teams need at least 2 members to compete
- **Team Captain**: The creator of the team becomes the captain
- **Team Roles**: Captain has special privileges (approve/reject members)

### Competition Modes

#### Individual Competition
- Users **not in a team** compete individually
- Scores are tracked in their personal profile
- Displayed on the individual leaderboard

#### Team Competition
- Users **in a team** compete as part of that team
- All scores go to the team (not individual members)
- Teams are displayed on the team leaderboard
- Only teams with 2+ members can compete

## How to Use

### Creating a Team

1. Navigate to **Teams** in the navigation menu
2. Click **"Create Team"**
3. Enter team name and description
4. You become the team captain automatically
5. Invite or wait for members to join

### Joining a Team

**Option 1: Request to Join**
1. Browse available teams
2. Click **"Request to Join"** on a team
3. Wait for the captain to approve your request

**Option 2: Accept Invitation**
1. Receive invitation from a team captain
2. Accept or reject the invitation

### Team Captain Responsibilities

- **Approve/Reject Join Requests**: Review and manage incoming requests
- **Manage Team**: Ensure team has at least 2 members to compete
- **Transfer Captaincy**: (Optional) Transfer captain role before leaving
- **Disband Team**: If captain leaves and is the last member, team is deactivated

### Leaving a Team

1. Go to your team page
2. Click **"Leave Team"**
3. **Note**: Captains cannot leave if there are other members (must transfer captaincy or disband)

## Scoring System

### Team Scoring
- When a team member solves a challenge, points go to the **team**
- Individual member scores are **not tracked** for team members
- Team score = sum of all challenges solved by any team member
- Each challenge can only be solved once per team

### Individual Scoring
- Users not in a team earn points individually
- Scores are tracked in their user profile
- Displayed on the individual leaderboard

## Leaderboards

### Team Leaderboard
- Shows all teams with 2+ members
- Ranked by total team score
- Displays: Team name, captain, members, score, challenges solved

### Individual Leaderboard
- Shows users competing individually (not in teams)
- Ranked by individual score
- Displays: Username, score, challenges solved

## Important Rules

1. **One Team Per User**: Users can only be in one team at a time
2. **Minimum Team Size**: Teams need at least 2 members to compete
3. **Maximum Team Size**: Teams can have up to 5 members
4. **No Double Scoring**: Challenges solved by team members only count once for the team
5. **Leave to Switch**: Users must leave their current team before joining another

## URLs

- **Team List**: `/teams/`
- **Create Team**: `/teams/create/`
- **My Team**: `/teams/my-team/`
- **Team Leaderboard**: `/teams/leaderboard/`
- **Team Detail**: `/teams/<team_id>/`

## Admin Features

Admins can:
- View all teams in the admin panel
- Manage team memberships
- View team invitations
- Deactivate teams if needed

## Tips for Success

1. **Communicate**: Use external tools (Discord, Slack) to coordinate with team members
2. **Divide Work**: Split challenges among team members based on expertise
3. **Share Knowledge**: Help each other learn and solve challenges
4. **Stay Active**: Regular participation keeps your team competitive
5. **Recruit Wisely**: Choose team members with complementary skills

## Troubleshooting

**Q: I can't join a team**
- Check if you're already in another team (leave first)
- Check if the team is full (5 members max)
- Check if you already have a pending request

**Q: My team can't compete**
- Ensure your team has at least 2 members
- Check that members have accepted their invitations

**Q: I want to leave but I'm the captain**
- Transfer captaincy to another member first
- Or if you're the last member, leaving will disband the team

**Q: Scores aren't updating**
- Ensure your team has at least 2 members
- Check that the challenge hasn't been solved by another team member already
- Refresh the page

## Email Invitations

### Sending Invitations (Captain Only)
1. Go to your team page
2. Find the "Invite Members" section
3. Enter the user's email address (must be registered)
4. Add an optional message
5. Click "Send Invitation"
6. User receives an email with invitation details

### Receiving Invitations
1. Check your email for invitation notifications
2. Or visit "My Invitations" page on the platform
3. View invitation details (team info, message, etc.)
4. Accept or decline the invitation

### Invitation Email Contains:
- Team name and captain
- Current team members and score
- Personal message from captain (if provided)
- Link to log in and view invitation

## Future Enhancements

Potential features for future updates:
- Team chat/messaging
- Team achievements and badges
- Team challenges (team-specific challenges)
- Team statistics and analytics
- Captain transfer functionality
