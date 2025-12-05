"""
SQL Injection Challenge - Vulnerable Login System
A realistic web application with SQL injection vulnerability
"""
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import sqlite3
import os
from pathlib import Path
from django.conf import settings


class SQLInjectionChallenge:
    """Manages the SQL injection challenge database and logic"""
    
    @staticmethod
    def get_db_path(challenge_id):
        """Get the path to the challenge database"""
        db_dir = Path(settings.BASE_DIR) / 'server_flags' / f'challenge_{challenge_id}'
        db_dir.mkdir(parents=True, exist_ok=True)
        return db_dir / 'users.db'
    
    @staticmethod
    def setup_database(challenge_id, flag):
        """Create and populate the vulnerable database"""
        db_path = SQLInjectionChallenge.get_db_path(challenge_id)
        
        # Remove existing database
        if db_path.exists():
            db_path.unlink()
        
        # Create new database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                role TEXT,
                secret TEXT
            )
        ''')
        
        # Create secrets table
        cursor.execute('''
            CREATE TABLE secrets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                secret_key TEXT,
                secret_value TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Insert sample users
        users = [
            ('admin', 'super_secret_password_123', 'admin@company.com', 'administrator', flag),
            ('john', 'password123', 'john@company.com', 'user', 'Nothing interesting here'),
            ('alice', 'alice2024', 'alice@company.com', 'user', 'My favorite color is blue'),
            ('bob', 'bob_pass', 'bob@company.com', 'user', 'I like pizza'),
            ('guest', 'guest', 'guest@company.com', 'guest', 'Welcome guest user'),
        ]
        
        cursor.executemany(
            'INSERT INTO users (username, password, email, role, secret) VALUES (?, ?, ?, ?, ?)',
            users
        )
        
        # Insert secrets
        secrets = [
            (1, 'flag', flag),
            (1, 'api_key', 'sk_live_abc123def456'),
            (2, 'note', 'Remember to change password'),
            (3, 'backup_code', '9876-5432-1098'),
        ]
        
        cursor.executemany(
            'INSERT INTO secrets (user_id, secret_key, secret_value) VALUES (?, ?, ?)',
            secrets
        )
        
        conn.commit()
        conn.close()
        
        return str(db_path)
    
    @staticmethod
    def vulnerable_login(challenge_id, username, password):
        """
        VULNERABLE LOGIN FUNCTION
        This function is intentionally vulnerable to SQL injection
        """
        db_path = SQLInjectionChallenge.get_db_path(challenge_id)
        
        if not db_path.exists():
            return {'success': False, 'error': 'Database not initialized'}
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # VULNERABLE QUERY - String concatenation instead of parameterized query
            query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
            
            cursor.execute(query)
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                return {
                    'success': True,
                    'user': {
                        'id': result[0],
                        'username': result[1],
                        'email': result[3],
                        'role': result[4],
                        'secret': result[5]
                    },
                    'query': query  # Show query for educational purposes
                }
            else:
                return {
                    'success': False,
                    'error': 'Invalid username or password',
                    'query': query
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Database error: {str(e)}',
                'query': query if 'query' in locals() else 'N/A'
            }


def sqli_challenge_home(request, challenge_id):
    """Home page for SQL injection challenge"""
    context = {
        'challenge_id': challenge_id,
        'title': 'SecureBank Login Portal'
    }
    return render(request, 'challenges/sqli_home.html', context)


@csrf_exempt
def sqli_challenge_login(request, challenge_id):
    """Vulnerable login endpoint"""
    if request.method == 'GET':
        context = {'challenge_id': challenge_id}
        return render(request, 'challenges/sqli_login.html', context)
    
    elif request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        # Call vulnerable login function
        result = SQLInjectionChallenge.vulnerable_login(challenge_id, username, password)
        
        if result['success']:
            # Successful login
            context = {
                'challenge_id': challenge_id,
                'user': result['user'],
                'query': result.get('query', '')
            }
            return render(request, 'challenges/sqli_dashboard.html', context)
        else:
            # Failed login
            context = {
                'challenge_id': challenge_id,
                'error': result['error'],
                'query': result.get('query', ''),
                'username': username
            }
            return render(request, 'challenges/sqli_login.html', context)


def sqli_challenge_hint(request, challenge_id):
    """Hints page for the challenge"""
    hints = [
        {
            'level': 'Beginner',
            'hint': "Try entering a single quote (') in the username field and see what happens."
        },
        {
            'level': 'Intermediate',
            'hint': "The SQL query looks like: SELECT * FROM users WHERE username = 'INPUT' AND password = 'INPUT'"
        },
        {
            'level': 'Advanced',
            'hint': "Try: admin' OR '1'='1' -- in the username field"
        },
        {
            'level': 'Expert',
            'hint': "Use UNION SELECT to extract data from other tables. Try: ' UNION SELECT * FROM secrets--"
        }
    ]
    
    context = {
        'challenge_id': challenge_id,
        'hints': hints
    }
    return render(request, 'challenges/sqli_hints.html', context)


def sqli_challenge_source(request, challenge_id):
    """Show the vulnerable source code"""
    source_code = '''
# Vulnerable Login Function
def login(username, password):
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    result = cursor.fetchone()
    
    if result:
        return {"success": True, "user": result}
    else:
        return {"success": False}
'''
    
    context = {
        'challenge_id': challenge_id,
        'source_code': source_code
    }
    return render(request, 'challenges/sqli_source.html', context)


def sqli_challenge_reset(request, challenge_id):
    """Reset the challenge database"""
    flag = 'CTF{sql_injection_master_2024}'
    db_path = SQLInjectionChallenge.setup_database(challenge_id, flag)
    
    return HttpResponse(f'''
    <html>
    <head><title>Database Reset</title></head>
    <body style="font-family: Arial; padding: 20px; background: #1a1a1a; color: #fff;">
        <h1>✅ Database Reset Successful</h1>
        <p>The challenge database has been reset.</p>
        <p>Database location: <code>{db_path}</code></p>
        <br>
        <a href="/challenges/sqli/{challenge_id}/" style="color: #00ff88;">← Back to Challenge</a>
    </body>
    </html>
    ''')
