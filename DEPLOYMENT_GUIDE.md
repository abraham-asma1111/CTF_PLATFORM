# CTF Platform - Deployment & Admin Access Guide

## Post-Deployment Admin Access

### 1. Access Admin Panel

After deployment, the admin can access the system management at:

```
http://your-domain.com/admin/
```

**Example URLs:**
- Local: `http://localhost:8000/admin/`
- Docker: `http://localhost:8000/admin/`
- Production: `https://your-ctf-platform.com/admin/`

### 2. Login Credentials

**Default Admin Account:**
- Username: `admin`
- Password: `admin@123`
- Email: `admin@ctf.com`

### 3. Admin Dashboard Features

Once logged in, the admin can manage:

#### A. Challenges Management
- **Create new challenges** with title, description, category, difficulty, flag, points
- **Edit existing challenges** - modify any challenge details
- **Deactivate challenges** - hide challenges from users
- **Filter challenges** by category, difficulty, or status
- **Search challenges** by title or description

#### B. User Management
- View all registered users
- View user profiles and statistics
- Manage user permissions
- Deactivate user accounts if needed

#### C. Submissions Management
- View all flag submissions
- See which users solved which challenges
- Track submission history
- Monitor user progress

#### D. Leaderboard Management
- View real-time leaderboard
- See user rankings and scores
- Monitor challenge completion rates

## Docker Deployment Steps

### Step 1: Build Docker Image
```bash
docker build -t ctf-platform .
```

### Step 2: Run Docker Container
```bash
docker-compose up -d
```

### Step 3: Create Admin Account (if not exists)
```bash
docker-compose exec web python manage.py shell << 'EOF'
from django.contrib.auth.models import User

admin_user, created = User.objects.get_or_create(username='admin')
admin_user.set_password('admin@123')
admin_user.is_superuser = True
admin_user.is_staff = True
admin_user.is_active = True
admin_user.email = 'admin@ctf.com'
admin_user.save()

print("✓ Admin account ready!")
EOF
```

### Step 4: Access Admin Panel
- URL: `http://localhost:8000/admin/`
- Login with admin credentials

## Production Deployment

### Step 1: Update Settings
Edit `ctf_platform/settings.py`:
```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']
SECRET_KEY = 'your-secret-key-here'
```

### Step 2: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Step 3: Run Migrations
```bash
python manage.py migrate
```

### Step 4: Create Admin Account
```bash
python manage.py shell << 'EOF'
from django.contrib.auth.models import User

admin_user, created = User.objects.get_or_create(username='admin')
admin_user.set_password('your-secure-password')
admin_user.is_superuser = True
admin_user.is_staff = True
admin_user.is_active = True
admin_user.email = 'admin@your-domain.com'
admin_user.save()

print("✓ Admin account created!")
EOF
```

### Step 5: Deploy with Gunicorn
```bash
gunicorn ctf_platform.wsgi:application --bind 0.0.0.0:8000
```

## Admin Panel Sections

### 1. Challenges
- **Add Challenge**: Create new CTF challenges
- **List Challenges**: View all challenges with filters
- **Edit Challenge**: Modify challenge details
- **Delete Challenge**: Remove challenges

### 2. Users
- **View Users**: See all registered users
- **User Details**: Check user profile and stats
- **Permissions**: Manage user roles

### 3. Submissions
- **View Submissions**: See all flag submissions
- **Filter by User**: Check specific user submissions
- **Filter by Challenge**: See who solved which challenge

### 4. Leaderboard
- **Real-time Rankings**: View current leaderboard
- **User Scores**: See points earned by each user
- **Challenge Stats**: View completion rates

## Common Admin Tasks

### Creating a Challenge
1. Go to Admin Panel → Challenges
2. Click "Add Challenge"
3. Fill in:
   - Title: "SQL Injection 101"
   - Description: "Find the hidden admin panel"
   - Category: Web
   - Difficulty: Easy
   - Flag: flag{sql_injection_found}
   - Points: 100
   - Is Active: ✓
4. Click Save

### Deactivating a Challenge
1. Go to Challenges list
2. Click on the challenge
3. Uncheck "Is Active"
4. Click Save

### Viewing User Progress
1. Go to Admin Panel → Users
2. Click on a user
3. View their profile and statistics
4. See challenges they've solved

### Monitoring Submissions
1. Go to Admin Panel → Submissions
2. Filter by user or challenge
3. View submission history
4. Check if flags are correct

## Security Best Practices

✅ **DO:**
- Change default admin password immediately
- Use strong, unique passwords
- Enable HTTPS in production
- Regularly backup the database
- Monitor admin access logs
- Keep Django updated

❌ **DON'T:**
- Share admin credentials
- Use weak passwords
- Deploy with DEBUG=True
- Expose SECRET_KEY
- Allow public access to /admin/

## Troubleshooting

### Admin Panel Not Accessible
- Check if server is running
- Verify URL: `http://localhost:8000/admin/`
- Check if admin account exists

### Can't Login
- Verify username and password
- Check if account is active
- Ensure account has staff permissions

### Challenges Not Showing
- Check if challenges are active
- Verify challenges are saved
- Refresh the page

## Support

For issues or questions, refer to:
- `ADMIN_GUIDE.md` - Detailed admin guide
- `QUICK_START_ADMIN.md` - Quick reference
- Django Admin Documentation: https://docs.djangoproject.com/en/4.2/ref/contrib/admin/
