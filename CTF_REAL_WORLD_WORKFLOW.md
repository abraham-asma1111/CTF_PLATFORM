# CTF Platform - Real World Workflow Guide

## Complete CTF Lifecycle: From Creation to Solution

This guide walks through a real-world scenario of how CTF challenges are created, deployed, and solved.

---

## PHASE 1: CHALLENGE CREATION (Admin/Challenge Creator)

### Step 1: Challenge Design & Preparation

**Scenario**: Security team wants to create a "SQL Injection" challenge

1. **Design the Challenge**
   - Decide challenge type: Web exploitation
   - Difficulty level: Medium
   - Points: 150
   - Time estimate: 30-45 minutes

2. **Create Challenge Files**
   - Create vulnerable web application
   - Set up database with hidden flag
   - Package everything (if needed)
   - Example: `sql_injection_app.zip` containing:
     ```
     sql_injection_app/
     ├── app.py (vulnerable Flask app)
     ├── database.db (with hidden flag)
     ├── requirements.txt
     └── README.txt (hints)
     ```

3. **Prepare the Flag**
   - Create unique flag: `flag{sql_injection_bypassed_login}`
   - Document it securely
   - Never share with users

### Step 2: Upload to Platform (Admin Dashboard)

**Admin logs in**: `http://localhost:8000/admin/`
- Username: `admin`
- Password: `admin@123`

**Create Challenge**:
1. Click "Challenges" → "Add Challenge"
2. Fill in details:
   - **Title**: "SQL Injection 101"
   - **Description**: 
     ```
     A vulnerable login form is waiting for you.
     Can you bypass the authentication using SQL injection?
     
     Hints:
     - Try entering special characters in the username field
     - Think about SQL syntax
     - The flag is in the database
     ```
   - **Category**: Web
   - **Difficulty**: Medium
   - **Flag**: `flag{sql_injection_bypassed_login}`
   - **Points**: 150
   - **Challenge File**: Upload `sql_injection_app.zip`
   - **Is Active**: ✓ Check

3. Click "Save"

**Result**: Challenge is now live on the platform

---

## PHASE 2: USER REGISTRATION & ACCESS

### Step 1: User Registration

**New user visits platform**: `http://localhost:8000/`

1. Click "JOIN THE ELITE" button
2. Fill registration form:
   - First Name: John
   - Last Name: Doe
   - Email: john@example.com
   - Username: john_hacker
   - Password: SecurePass123!
   - Sex: Male
   - Education Level: Undergraduate
   - Department: Cyber Security

3. Click "Register"
4. Redirected to login page
5. Login with credentials:
   - Username: john_hacker
   - Password: SecurePass123!

**Result**: User is now logged in and can access challenges

### Step 2: Browse Challenges

**User navigates to**: `http://localhost:8000/challenges/`

Sees list of all active challenges:
- SQL Injection 101 (Medium, 150 pts)
- Buffer Overflow Basics (Hard, 250 pts)
- Crypto Challenge (Easy, 100 pts)
- etc.

---

## PHASE 3: SOLVING A CHALLENGE

### Step 1: View Challenge Details

**User clicks**: "SQL Injection 101"

Sees:
- Full description with hints
- Difficulty badge: Medium
- Points: 150
- Download button: "⬇️ Download File"

### Step 2: Download Challenge File

**User clicks**: "⬇️ Download File"

Downloads: `sql_injection_app.zip`

### Step 3: Solve the Challenge Locally

**User's computer**:

1. Extract the file:
   ```bash
   unzip sql_injection_app.zip
   cd sql_injection_app
   ```

2. Read the README:
   ```
   SQL Injection Challenge
   
   This is a vulnerable web application.
   Your goal: Find the flag by exploiting SQL injection.
   
   Setup:
   - pip install -r requirements.txt
   - python app.py
   - Visit http://localhost:5000
   
   Hints:
   - Try entering: admin' OR '1'='1
   - The flag is stored in the users table
   ```

3. Set up locally:
   ```bash
   pip install -r requirements.txt
   python app.py
   ```

4. Open browser: `http://localhost:5000`

5. Try SQL injection:
   - Username field: `admin' OR '1'='1`
   - Password field: `anything`
   - Click Login

6. Success! Page displays:
   ```
   Welcome Admin!
   Flag: flag{sql_injection_bypassed_login}
   ```

### Step 4: Submit Flag on Platform

**User returns to platform**:

1. On challenge detail page, enters flag:
   - Input field: `flag{sql_injection_bypassed_login}`

2. Clicks "Submit Flag"

3. System validates:
   - Hashes the submitted flag
   - Compares with stored hash
   - Match found!

4. Success message:
   ```
   ✓ Correct! You earned 150 points!
   ```

**Result**: 
- Challenge marked as "Solved"
- User gains 150 points
- Leaderboard updated

---

## PHASE 4: REAL-WORLD CHALLENGE EXAMPLES

### Example 1: Binary Exploitation

**Admin creates challenge**:
- Title: "Buffer Overflow 101"
- Category: Binary Exploitation
- Difficulty: Hard
- Points: 250
- File: `overflow_challenge` (compiled binary)

**User workflow**:
1. Downloads binary
2. Analyzes with GDB/IDA Pro
3. Finds buffer overflow vulnerability
4. Crafts exploit
5. Runs: `./overflow_challenge < exploit.txt`
6. Gets flag: `flag{buffer_overflow_exploited}`
7. Submits on platform

### Example 2: Cryptography

**Admin creates challenge**:
- Title: "RSA Decryption"
- Category: Cryptography
- Difficulty: Hard
- Points: 300
- File: `encrypted_message.txt`

**User workflow**:
1. Downloads encrypted message
2. Analyzes encryption method
3. Finds weak RSA parameters
4. Writes Python script to decrypt
5. Decrypts message
6. Extracts flag: `flag{rsa_decrypted}`
7. Submits on platform

### Example 3: Reverse Engineering

**Admin creates challenge**:
- Title: "Reverse Me"
- Category: Reverse Engineering
- Difficulty: Medium
- Points: 200
- File: `reverse_me.exe`

**User workflow**:
1. Downloads executable
2. Opens in IDA Pro/Ghidra
3. Analyzes assembly code
4. Finds hardcoded flag check
5. Extracts flag: `flag{reverse_engineering_complete}`
6. Submits on platform

### Example 4: Web Exploitation

**Admin creates challenge**:
- Title: "XSS Vulnerability"
- Category: Web
- Difficulty: Easy
- Points: 100
- File: `web_app.zip`

**User workflow**:
1. Downloads and extracts web app
2. Runs locally
3. Finds XSS vulnerability in comment form
4. Injects payload: `<script>alert('flag{xss_found}')</script>`
5. Extracts flag
6. Submits on platform

### Example 5: Forensics

**Admin creates challenge**:
- Title: "Memory Dump Analysis"
- Category: Forensics
- Difficulty: Hard
- Points: 350
- File: `memory_dump.bin`

**User workflow**:
1. Downloads memory dump
2. Uses Volatility framework
3. Analyzes processes and memory
4. Finds hidden flag in memory
5. Extracts: `flag{forensics_analysis_complete}`
6. Submits on platform

---

## PHASE 5: LEADERBOARD & SCORING

### Real-Time Updates

**After user solves challenges**:

1. **User Profile** (`/users/profile/`):
   - Total Score: 150 points
   - Challenges Solved: 1
   - Last Submission: 2 minutes ago

2. **Leaderboard** (`/leaderboard/`):
   - Rank: #5
   - Username: john_hacker
   - Score: 150
   - Challenges: 1

3. **Challenge List** (`/challenges/`):
   - SQL Injection 101: ✓ Solved (150 pts)
   - Other challenges: Available

---

## PHASE 6: ADMIN MONITORING

### Admin Dashboard

**Admin views**:

1. **Challenge Statistics**:
   - Total challenges: 10
   - Active challenges: 8
   - Solved by users: 45 submissions

2. **User Progress**:
   - Total users: 25
   - Active users: 18
   - Average score: 450 points

3. **Submission History**:
   - john_hacker: Solved "SQL Injection 101" ✓
   - jane_smith: Attempted "Buffer Overflow" (incorrect)
   - bob_security: Solved "Crypto Challenge" ✓

---

## COMPLETE WORKFLOW TIMELINE

```
Day 1 - Challenge Creation
├── 09:00 - Admin designs challenge
├── 10:00 - Challenge files prepared
├── 11:00 - Challenge uploaded to platform
└── 12:00 - Challenge goes live

Day 2 - User Registration
├── 14:00 - New user registers
├── 14:05 - User logs in
└── 14:10 - User browses challenges

Day 2 - Challenge Solving
├── 14:15 - User downloads challenge file
├── 14:20 - User sets up locally
├── 15:00 - User solves challenge
├── 15:05 - User submits flag
└── 15:06 - Flag accepted, points awarded

Day 3 - Leaderboard Update
├── 09:00 - User checks leaderboard
├── 09:05 - User sees ranking
└── 09:10 - User attempts next challenge
```

---

## KEY COMPONENTS

### For Admins
- Challenge creation interface
- File upload system
- Flag management (hashed)
- User monitoring
- Submission tracking

### For Users
- Challenge browsing
- File downloads
- Local solving environment
- Flag submission
- Progress tracking
- Leaderboard viewing

### Platform Features
- Secure flag hashing (SHA256)
- User authentication
- Real-time scoring
- Leaderboard ranking
- Challenge categorization
- Difficulty levels
- Points system

---

## SECURITY CONSIDERATIONS

1. **Flag Protection**
   - Flags are hashed before storage
   - Users never see plain text flags
   - Only submitted flags are compared

2. **File Security**
   - Challenge files stored securely
   - Malware scanning recommended
   - File permissions properly set

3. **User Data**
   - Passwords hashed
   - Email validation
   - Profile privacy

4. **Admin Access**
   - Admin panel protected
   - Staff-only access
   - Audit trail available

---

## DEPLOYMENT CHECKLIST

- [ ] Admin account created
- [ ] Challenge files prepared
- [ ] Challenges uploaded
- [ ] Users can register
- [ ] Users can download files
- [ ] Flag submission working
- [ ] Leaderboard updating
- [ ] Scoring accurate
- [ ] Database backed up
- [ ] HTTPS enabled (production)

---

## SUPPORT & TROUBLESHOOTING

See other documentation:
- `ADMIN_GUIDE.md` - Admin operations
- `DEPLOYMENT_GUIDE.md` - Deployment steps
- `CHALLENGE_FILE_SETUP.md` - File upload details
- `QUICK_START_ADMIN.md` - Quick reference
