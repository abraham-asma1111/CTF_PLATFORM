"""
Server-side flag management for CTF challenges
Flags are stored on the server and users must discover them through various methods
"""
import os
import hashlib
from pathlib import Path
from django.conf import settings


class ServerFlagManager:
    """Manage flags stored on the server side"""
    
    # Directory for storing flag files
    FLAG_DIR = Path(settings.BASE_DIR) / 'server_flags'
    
    @classmethod
    def setup_flag_directory(cls):
        """Create the flag directory if it doesn't exist"""
        cls.FLAG_DIR.mkdir(exist_ok=True)
        # Create .gitignore to prevent flags from being committed
        gitignore_path = cls.FLAG_DIR / '.gitignore'
        if not gitignore_path.exists():
            gitignore_path.write_text('*\n!.gitignore\n')
    
    @classmethod
    def create_flag_file(cls, challenge_id, flag_content, filename='flag.txt', hidden=False):
        """
        Create a flag file on the server
        
        Args:
            challenge_id: ID of the challenge
            flag_content: The flag text (e.g., "CTF{server_side_flag}")
            filename: Name of the file
            hidden: If True, creates a hidden file (starts with .)
        """
        cls.setup_flag_directory()
        
        # Create challenge-specific directory
        challenge_dir = cls.FLAG_DIR / f'challenge_{challenge_id}'
        challenge_dir.mkdir(exist_ok=True)
        
        # Create flag file
        if hidden and not filename.startswith('.'):
            filename = f'.{filename}'
        
        flag_file = challenge_dir / filename
        flag_file.write_text(flag_content)
        
        # Set restrictive permissions (owner read-only)
        os.chmod(flag_file, 0o400)
        
        return str(flag_file)
    
    @classmethod
    def create_backup_file(cls, challenge_id, flag_content):
        """Create a backup file that might be discovered"""
        return cls.create_flag_file(
            challenge_id, 
            flag_content, 
            filename='backup.txt.bak',
            hidden=False
        )
    
    @classmethod
    def create_git_exposed_flag(cls, challenge_id, flag_content):
        """Create a flag in a .git directory (simulating exposed git)"""
        cls.setup_flag_directory()
        
        challenge_dir = cls.FLAG_DIR / f'challenge_{challenge_id}'
        git_dir = challenge_dir / '.git' / 'logs'
        git_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a git log file with the flag
        log_file = git_dir / 'HEAD'
        log_content = f"""
0000000000000000000000000000000000000000 abc123def456 Developer <dev@ctf.com> 1234567890 +0000	commit: Initial commit
abc123def456 def789ghi012 Developer <dev@ctf.com> 1234567891 +0000	commit: Add flag
# Flag for testing: {flag_content}
def789ghi012 ghi345jkl678 Developer <dev@ctf.com> 1234567892 +0000	commit: Remove flag (oops, too late!)
"""
        log_file.write_text(log_content)
        return str(log_file)
    
    @classmethod
    def create_source_code_flag(cls, challenge_id, flag_content):
        """Create a flag hidden in source code comments"""
        cls.setup_flag_directory()
        
        challenge_dir = cls.FLAG_DIR / f'challenge_{challenge_id}'
        challenge_dir.mkdir(exist_ok=True)
        
        # Create a source file with flag in comments
        source_file = challenge_dir / 'app.py'
        source_content = f"""#!/usr/bin/env python3
# Web Application
# TODO: Remove this before deployment!
# Flag: {flag_content}

def main():
    print("Welcome to the application")
    # More code here...
    pass

if __name__ == "__main__":
    main()
"""
        source_file.write_text(source_content)
        return str(source_file)
    
    @classmethod
    def get_flag_path(cls, challenge_id, filename='flag.txt'):
        """Get the path to a flag file"""
        return cls.FLAG_DIR / f'challenge_{challenge_id}' / filename
    
    @classmethod
    def read_flag(cls, challenge_id, filename='flag.txt'):
        """Read a flag from the server"""
        try:
            flag_path = cls.get_flag_path(challenge_id, filename)
            if flag_path.exists():
                return flag_path.read_text().strip()
        except Exception as e:
            print(f"Error reading flag: {e}")
        return None
    
    @classmethod
    def list_challenge_files(cls, challenge_id):
        """List all files for a challenge (for debugging)"""
        challenge_dir = cls.FLAG_DIR / f'challenge_{challenge_id}'
        if challenge_dir.exists():
            return [str(f.relative_to(challenge_dir)) for f in challenge_dir.rglob('*') if f.is_file()]
        return []


# Example flag types and how to create them
FLAG_TYPES = {
    'file': 'Flag stored in a regular file',
    'hidden': 'Flag in a hidden file (starts with .)',
    'backup': 'Flag in a backup file (.bak)',
    'git': 'Flag exposed in .git directory',
    'source': 'Flag in source code comments',
    'env': 'Flag in environment variables',
    'database': 'Flag in database (already implemented)',
}
