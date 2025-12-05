# Team Chat System Guide

## Overview

The Team Chat System enables secure communication between team members in the CTF platform. Each team has its own private chat room where only accepted team members can participate.

## Features

### 🔒 **Security & Privacy**
- **Team-only access**: Only accepted team members can view and send messages
- **Profile matching**: Messages are associated with user profiles
- **No cross-team communication**: Users can only see messages from their own team

### 💬 **Messaging Features**
- **Real-time messaging**: Send and receive messages instantly
- **Message editing**: Edit your own messages (marked as edited)
- **Message deletion**: Delete your own messages or captain can delete any message
- **Message reactions**: React to messages with emojis (😀, 👍, ❤️)
- **Read tracking**: System tracks which messages have been read
- **Typing indicators**: See when someone is typing (planned feature)

### 👥 **Team Integration**
- **Member list**: See all team members in the sidebar
- **Captain privileges**: Team captains have additional moderation powers
- **Notification badges**: Unread message count in navigation
- **Easy access**: Direct links from team pages

## How to Use

### Accessing Team Chat

1. **From Team Detail Page**: Click the "Team Chat" button (only visible to team members)
2. **From Navigation**: Click the "💬 Chat" link in the main navigation
3. **Direct URL**: `/chat/team/{team_id}/`

### Sending Messages

1. Type your message in the input field at the bottom
2. Press **Enter** or click **Send** button
3. Messages appear instantly for all team members
4. Maximum message length: 1000 characters

### Message Actions

- **React**: Click emoji buttons (😀, 👍, ❤️) below any message
- **Edit**: Click "Edit" button on your own messages
- **Delete**: Click "Delete" button on your own messages (captains can delete any)

### Notifications

- Unread message count appears as a red badge in navigation
- Messages from the last 7 days are tracked for notifications
- Messages are automatically marked as read when you view the chat

## Technical Details

### Database Models

#### TeamMessage
- Stores all chat messages
- Links to team and sender
- Supports text, system, and file message types
- Tracks edit history and timestamps

#### MessageReaction
- Stores emoji reactions to messages
- Prevents duplicate reactions from same user
- Supports multiple emoji types per message

#### MessageRead
- Tracks which users have read which messages
- Used for notification calculations
- Automatically created when viewing chat

### API Endpoints

- `GET /chat/team/{team_id}/` - Chat interface
- `POST /chat/team/{team_id}/send/` - Send message
- `GET /chat/team/{team_id}/messages/` - Get messages (for real-time updates)
- `POST /chat/message/{message_id}/edit/` - Edit message
- `POST /chat/message/{message_id}/delete/` - Delete message
- `POST /chat/message/{message_id}/react/` - Add/remove reaction
- `GET /chat/notifications/` - Get unread counts

### Security Features

1. **Team Membership Validation**: All endpoints verify user is an accepted team member
2. **Message Ownership**: Users can only edit/delete their own messages (except captains)
3. **Input Sanitization**: Messages are validated and length-limited
4. **CSRF Protection**: All POST requests require CSRF tokens

## Administration

### Django Admin

Access chat data through Django admin:
- **TeamMessage**: View, edit, and delete messages
- **MessageReaction**: Manage reactions
- **MessageRead**: Track read status

### Management Commands

```bash
# Create sample chat data for testing
python manage.py create_sample_messages
```

### Monitoring

- Monitor message volume and activity
- Track team engagement through chat usage
- Identify inactive teams or communication issues

## Best Practices

### For Users
- Keep messages relevant to CTF challenges and team coordination
- Use reactions to acknowledge messages without cluttering chat
- Edit messages instead of sending corrections
- Respect team members and maintain professional communication

### For Administrators
- Monitor chat for inappropriate content
- Set up regular database cleanup for old messages
- Consider implementing message retention policies
- Monitor system performance with high message volumes

## Troubleshooting

### Common Issues

1. **Can't access chat**: Ensure you're an accepted team member
2. **Messages not appearing**: Check browser console for JavaScript errors
3. **Can't send messages**: Verify team membership and try refreshing page
4. **Notifications not updating**: Clear browser cache and reload

### Performance Considerations

- Chat loads last 50 messages by default
- Auto-refresh every 30 seconds (can be adjusted)
- Consider implementing WebSocket for real-time updates in production
- Database indexes on team_id and timestamp for fast queries

## Future Enhancements

### Planned Features
- **File sharing**: Upload and share files in chat
- **WebSocket integration**: Real-time updates without page refresh
- **Message search**: Search through chat history
- **Message threading**: Reply to specific messages
- **Typing indicators**: Show when users are typing
- **Message formatting**: Support for markdown or basic formatting
- **Chat archives**: Export chat history
- **Moderation tools**: Advanced admin controls

### Integration Opportunities
- **Challenge notifications**: Automatic messages when team solves challenges
- **Submission alerts**: Notify team of successful submissions
- **Hint sharing**: Share challenge hints within team chat
- **Meeting scheduler**: Coordinate team meetings through chat

## Sample Usage

```python
# Create a message programmatically
from chat.models import TeamMessage
from teams.models import Team
from django.contrib.auth.models import User

team = Team.objects.get(name='My Team')
user = User.objects.get(username='captain')

message = TeamMessage.objects.create(
    team=team,
    sender=user,
    content='Great work on that SQL injection challenge!',
    message_type='text'
)

# Add a reaction
from chat.models import MessageReaction

reaction = MessageReaction.objects.create(
    message=message,
    user=user,
    emoji='🎉'
)
```

## Support

For technical issues or feature requests related to the chat system:
1. Check this documentation first
2. Review Django admin for data issues
3. Check application logs for errors
4. Contact system administrator

---

**Note**: This chat system is designed for team coordination in CTF competitions. All messages should be relevant to the competition and maintain appropriate professional standards.