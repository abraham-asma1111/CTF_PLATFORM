# CTF Platform Admin Guide

## Admin Access

### Creating a Superuser (First Time Setup)
```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account with:
- Username
- Email
- Password

### Accessing Admin Panel
1. Start the Django development server: `python manage.py runserver`
2. Navigate to: `http://127.0.0.1:8000/admin/`
3. Login with your superuser credentials

## Managing Challenges

### Creating a New Challenge

1. Go to **Challenges** section in admin panel
2. Click **"Add Challenge"** button
3. Fill in the following fields:

#### Challenge Information
- **Title**: Name of the challenge (e.g., "SQL Injection Basics")
- **Description**: Detailed description of what users need to do
- **Category**: Select from:
  - Web
  - Cryptography
  - Forensics
  - Binary Exploitation (pwn)
  - Reverse Engineering
  - Miscellaneous

#### Flag & Points
- **Flag**: Enter the plain text flag (e.g., "flag{sql_injection_solved}")
  - ⚠️ **Important**: The flag is automatically hashed for security
  - Users will submit this flag to solve the challenge
- **Points**: Award points for solving (e.g., 100, 250, 500)

#### Difficulty
- **Easy**: For beginners (50-100 points)
- **Medium**: For intermediate users (100-250 points)
- **Hard**: For advanced users (250-500+ points)

#### Status
- **Is Active**: Check to make the challenge visible to users
- Uncheck to hide/disable a challenge

### Example Challenge

**Title**: Basic Web Exploitation
**Description**: Find the hidden admin panel and login using SQL injection techniques
**Category**: Web
**Difficulty**: Medium
**Flag**: flag{admin_panel_found}
**Points**: 150
**Is Active**: ✓ Checked

### Editing Challenges

1. Click on a challenge title in the list
2. Modify any fields
3. Click **"Save"** button

### Deactivating Challenges

1. Find the challenge in the list
2. Uncheck the **"Is Active"** checkbox
3. Click **"Save"**
4. Challenge will no longer appear to users

### Filtering & Searching

- **Filter by Category**: Click category in left sidebar
- **Filter by Difficulty**: Click difficulty level in left sidebar
- **Filter by Status**: Click "Active" or "Inactive" in left sidebar
- **Search**: Use the search box to find challenges by title or description

## Docker Deployment

### Building the Docker Image
```bash
docker build -t ctf-platform .
```

### Running the Container
```bash
docker-compose up -d
```

### Accessing Admin in Docker
1. The application runs on `http://localhost:8000`
2. Admin panel: `http://localhost:8000/admin/`
3. Use the same superuser credentials

### Creating Superuser in Docker
```bash
docker-compose exec web python manage.py createsuperuser
```

## User Access to Challenges

### How Users See Challenges
1. Users login to the platform
2. Navigate to **"Challenges"** section
3. See all active challenges filtered by:
   - Category
   - Difficulty
   - Points
4. Click on a challenge to view details
5. Submit the flag to solve

### Challenge Submission
- Users submit the flag they found
- System automatically hashes and compares
- If correct: Challenge marked as solved, points awarded
- If incorrect: User can try again

## Best Practices

### Challenge Creation
✅ **DO:**
- Create clear, descriptive titles
- Write detailed descriptions with hints
- Use appropriate difficulty levels
- Award points based on difficulty
- Test challenges before activating

❌ **DON'T:**
- Use the same flag for multiple challenges
- Make descriptions too vague
- Forget to activate challenges
- Award too many/too few points

### Security
- Flags are automatically hashed using SHA256
- Never share plain text flags with users
- Only admins can see the hashed flags
- Users only submit their answers

## Troubleshooting

### Challenge Not Appearing
- Check if **"Is Active"** is checked
- Verify the challenge was saved
- Refresh the page

### Users Can't Submit Flags
- Ensure challenge is active
- Check that flag is correctly entered
- Verify user is logged in

### Admin Panel Not Accessible
- Ensure you're logged in as superuser
- Check URL: `http://localhost:8000/admin/`
- Verify superuser account exists

## Support

For issues or questions, contact the platform administrator.
