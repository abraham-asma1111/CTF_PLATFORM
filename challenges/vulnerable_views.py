"""
Intentionally vulnerable views for CTF challenges
These endpoints contain security flaws that allow flag discovery
"""
from django.http import JsonResponse, HttpResponse, FileResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import os
import subprocess
from pathlib import Path
from .server_flags import ServerFlagManager


def vulnerable_file_read(request, challenge_id):
    """
    VULNERABLE: Path traversal vulnerability
    Users can read arbitrary files by manipulating the 'file' parameter
    
    Example: /challenges/vulnerable/1/read?file=../../../flag.txt
    """
    filename = request.GET.get('file', 'readme.txt')
    
    # INTENTIONALLY VULNERABLE - No path sanitization!
    try:
        challenge_dir = ServerFlagManager.FLAG_DIR / f'challenge_{challenge_id}'
        file_path = challenge_dir / filename
        
        # Read and return file content
        if file_path.exists():
            content = file_path.read_text()
            return HttpResponse(content, content_type='text/plain')
        else:
            return HttpResponse('File not found', status=404)
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)


def vulnerable_command_injection(request, challenge_id):
    """
    VULNERABLE: Command injection vulnerability
    Users can execute arbitrary commands
    
    Example: /challenges/vulnerable/1/ping?host=localhost; cat flag.txt
    """
    host = request.GET.get('host', 'localhost')
    
    # INTENTIONALLY VULNERABLE - No input sanitization!
    try:
        challenge_dir = ServerFlagManager.FLAG_DIR / f'challenge_{challenge_id}'
        os.chdir(challenge_dir)
        
        # Execute command (DANGEROUS!)
        result = subprocess.run(
            f'ping -c 1 {host}',
            shell=True,  # VULNERABLE!
            capture_output=True,
            text=True,
            timeout=5
        )
        
        output = result.stdout + result.stderr
        return HttpResponse(f'<pre>{output}</pre>', content_type='text/html')
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)


def vulnerable_directory_listing(request, challenge_id):
    """
    VULNERABLE: Directory listing enabled
    Users can see all files in the challenge directory
    
    Example: /challenges/vulnerable/1/files
    """
    try:
        challenge_dir = ServerFlagManager.FLAG_DIR / f'challenge_{challenge_id}'
        
        if not challenge_dir.exists():
            return HttpResponse('Challenge directory not found', status=404)
        
        # List all files (including hidden ones)
        files = []
        for item in challenge_dir.rglob('*'):
            if item.is_file():
                rel_path = item.relative_to(challenge_dir)
                size = item.stat().st_size
                files.append({
                    'name': str(rel_path),
                    'size': size,
                    'path': f'/challenges/vulnerable/{challenge_id}/download?file={rel_path}'
                })
        
        html = '<html><head><title>Directory Listing</title></head><body>'
        html += f'<h1>Directory Listing - Challenge {challenge_id}</h1>'
        html += '<ul>'
        for f in files:
            html += f'<li><a href="{f["path"]}">{f["name"]}</a> ({f["size"]} bytes)</li>'
        html += '</ul></body></html>'
        
        return HttpResponse(html, content_type='text/html')
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)


def vulnerable_file_download(request, challenge_id):
    """
    VULNERABLE: Unrestricted file download
    Users can download any file from the challenge directory
    """
    filename = request.GET.get('file', '')
    
    try:
        challenge_dir = ServerFlagManager.FLAG_DIR / f'challenge_{challenge_id}'
        file_path = challenge_dir / filename
        
        if file_path.exists() and file_path.is_file():
            return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
        else:
            return HttpResponse('File not found', status=404)
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)


@csrf_exempt
def vulnerable_sql_injection(request, challenge_id):
    """
    VULNERABLE: SQL injection (simulated)
    Returns flag if correct SQL injection is used
    
    Example: /challenges/vulnerable/1/login?username=admin' OR '1'='1
    """
    username = request.GET.get('username', '')
    password = request.GET.get('password', '')
    
    # Simulate SQL injection vulnerability
    if "' OR '1'='1" in username or "' OR '1'='1" in password:
        flag = ServerFlagManager.read_flag(challenge_id)
        return JsonResponse({
            'success': True,
            'message': 'Login successful!',
            'flag': flag or 'CTF{sql_injection_master}',
            'user': 'admin'
        })
    elif username == 'admin' and password == 'admin':
        return JsonResponse({
            'success': True,
            'message': 'Login successful!',
            'user': 'admin'
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Invalid credentials'
        })


def vulnerable_xxe(request, challenge_id):
    """
    VULNERABLE: XML External Entity (XXE) injection
    Simulated XXE vulnerability
    """
    if request.method == 'POST':
        xml_data = request.body.decode('utf-8')
        
        # Check for XXE payload
        if 'SYSTEM' in xml_data or 'file://' in xml_data:
            flag = ServerFlagManager.read_flag(challenge_id)
            return HttpResponse(f'XML Parsed Successfully!\nFlag: {flag}', content_type='text/plain')
        else:
            return HttpResponse('XML Parsed Successfully!', content_type='text/plain')
    
    return HttpResponse('''
    <html>
    <body>
        <h1>XML Parser</h1>
        <form method="POST">
            <textarea name="xml" rows="10" cols="50"></textarea><br>
            <button type="submit">Parse XML</button>
        </form>
    </body>
    </html>
    ''', content_type='text/html')


def vulnerable_info_disclosure(request, challenge_id):
    """
    VULNERABLE: Information disclosure through error messages
    Verbose error messages that leak sensitive information
    """
    action = request.GET.get('action', 'info')
    
    if action == 'debug':
        # Leak environment variables
        flag = ServerFlagManager.read_flag(challenge_id)
        return JsonResponse({
            'debug_info': {
                'flag': flag,
                'challenge_id': challenge_id,
                'server_path': str(ServerFlagManager.FLAG_DIR),
                'files': ServerFlagManager.list_challenge_files(challenge_id)
            }
        })
    elif action == 'error':
        # Trigger an error that leaks information
        try:
            flag = ServerFlagManager.read_flag(challenge_id)
            raise Exception(f'Database error! Flag leaked: {flag}')
        except Exception as e:
            return HttpResponse(f'<h1>Error 500</h1><pre>{str(e)}</pre>', status=500)
    else:
        return HttpResponse('Try ?action=debug or ?action=error')


def vulnerable_robots_txt(request, challenge_id):
    """
    VULNERABLE: Sensitive information in robots.txt
    """
    flag = ServerFlagManager.read_flag(challenge_id)
    
    robots_content = f"""User-agent: *
Disallow: /admin/
Disallow: /secret/
Disallow: /flag.txt
Disallow: /backup/

# Note to self: Don't forget to remove this!
# Flag: {flag}
"""
    return HttpResponse(robots_content, content_type='text/plain')
