# Admin Guide: How to Delete Teams

## ✅ Fixed! You Can Now Delete Teams from Django Admin

The team deletion issue has been resolved. You can now safely delete teams directly from the Django admin panel at:

http://127.0.0.1:8000/admin/teams/team/

The admin interface now properly handles all foreign key relationships including:
- Chat messages and reactions
- Group challenge submissions
- Regular challenge submissions
- Team memberships
- Team invitations

## Alternative: Management Command

If you prefer using the command line, you can still use the management command:

```bash
python manage.py delete_team <team_id>
```

### Example:
```bash
# Delete team with ID 9
python manage.py delete_team 9
```

## Find Team IDs

You can find team IDs in several ways:

### Option 1: Django Admin
Go to http://127.0.0.1:8000/admin/teams/team/ and look at the ID column

### Option 2: Django Shell
```bash
python manage.py shell
```

Then run:
```python
from teams.models import Team

# List all teams with their IDs
for team in Team.objects.all():
    print(f"ID: {team.id} - Name: {team.name}")
```

### Option 3: Command Line
```bash
python manage.py shell -c "from teams.models import Team; [print(f'ID: {t.id} - {t.name}') for t in Team.objects.all()]"
```

## What Happens During Deletion

Both the admin interface and management command safely handle:
1. Delete chat messages, reactions, and read status
2. Delete all group challenge submissions
3. Set `team=NULL` for all regular challenge submissions
4. Delete team memberships
5. Delete team invitations
6. Delete the team itself

All operations are wrapped in a transaction, so if anything fails, nothing is deleted.
