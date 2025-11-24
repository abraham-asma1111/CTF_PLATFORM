# Quick Start - Admin Challenge Management

## 1. Create Admin Account (First Time Only)

```bash
# Option A: Using the script
./create_admin.sh

# Option B: Manual
python manage.py createsuperuser
```

## 2. Start the Server

```bash
python manage.py runserver
```

## 3. Access Admin Panel

- URL: `http://localhost:8000/admin/`
- Login with your admin credentials

## 4. Create Your First Challenge

1. Click **"Challenges"** in the admin panel
2. Click **"+ Add Challenge"** button
3. Fill in:
   - **Title**: "My First Challenge"
   - **Description**: "Find the hidden flag"
   - **Category**: Web
   - **Difficulty**: Easy
   - **Flag**: flag{my_first_flag}
   - **Points**: 100
   - **Is Active**: ✓ Check this box
4. Click **"Save"**

## 5. Users Can Now Access

- Users login to the platform
- Go to Challenges section
- See your new challenge
- Submit the flag to solve it

## Docker Deployment

```bash
# Build image
docker build -t ctf-platform .

# Run container
docker-compose up -d

# Create admin in Docker
docker-compose exec web python manage.py createsuperuser

# Access at http://localhost:8000/admin/
```

## Challenge Categories

| Category | Best For |
|----------|----------|
| Web | SQL Injection, XSS, CSRF |
| Crypto | Encryption, Hashing, Decryption |
| Forensics | File Analysis, Memory Dumps |
| Binary Exploitation (pwn) | Buffer Overflow, ROP |
| Reverse Engineering | Disassembly, Decompilation |
| Miscellaneous | Other challenges |

## Points Guide

| Difficulty | Recommended Points |
|------------|-------------------|
| Easy | 50-100 |
| Medium | 100-250 |
| Hard | 250-500+ |

## Tips

✅ Test challenges before activating
✅ Write clear descriptions with hints
✅ Use appropriate difficulty levels
✅ Deactivate challenges when needed
✅ Monitor user submissions

## Support

See `ADMIN_GUIDE.md` for detailed documentation.
