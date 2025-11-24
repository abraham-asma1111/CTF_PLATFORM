# CTF Challenge File Upload Setup

## Overview

Admins can now upload challenge files (binaries, archives, source code, etc.) through the Django admin panel. Users can download these files to solve the challenges.

## How It Works

### For Admins

1. **Go to Admin Panel**: `http://localhost:8000/admin/`
2. **Navigate to Challenges**
3. **Create or Edit a Challenge**
4. **Upload Challenge File** (optional):
   - Scroll to "Challenge File" section
   - Click to expand the section
   - Choose a file to upload (binary, .zip, .tar.gz, etc.)
   - Save the challenge

### For Users

1. **View Challenge Details**
2. **Download Challenge File** (if available):
   - Click the "⬇️ Download File" button
   - File will be downloaded to their computer
3. **Solve the Challenge**
4. **Submit the Flag**

## File Storage

Files are stored in: `media/challenges/YYYY/MM/DD/`

Example structure:
```
media/
└── challenges/
    └── 2025/
        └── 11/
            └── 24/
                ├── binary_exploit
                ├── crypto_challenge.zip
                └── reverse_engineering.tar.gz
```

## Challenge Types & File Examples

### Binary Exploitation (pwn)
- Upload compiled binaries
- Example: `pwn_challenge` (ELF binary)
- Users download and analyze with tools like GDB, IDA Pro

### Reverse Engineering
- Upload compiled programs or libraries
- Example: `reverse_me.exe` or `libchallenge.so`
- Users use disassemblers and decompilers

### Cryptography
- Upload encrypted files or source code
- Example: `encrypted_message.txt` or `crypto_challenge.py`
- Users analyze and break the encryption

### Forensics
- Upload memory dumps, disk images, or logs
- Example: `memory_dump.bin` or `access_logs.tar.gz`
- Users analyze for hidden information

### Web
- Upload source code or configuration files
- Example: `web_app.zip` containing source code
- Users analyze for vulnerabilities

### Miscellaneous
- Any other file type needed for the challenge
- Example: `puzzle.txt`, `data.json`, etc.

## Admin Workflow Example

### Creating a Binary Exploitation Challenge

1. **Title**: "Buffer Overflow 101"
2. **Description**: "Exploit the buffer overflow vulnerability to get the flag"
3. **Category**: Binary Exploitation
4. **Difficulty**: Medium
5. **Flag**: flag{buffer_overflow_solved}
6. **Points**: 200
7. **Challenge File**: Upload `overflow_challenge` (compiled binary)
8. **Is Active**: ✓ Check

Users will see a download button to get the binary.

### Creating a Cryptography Challenge

1. **Title**: "RSA Decryption"
2. **Description**: "Decrypt the message using RSA"
3. **Category**: Cryptography
4. **Difficulty**: Hard
5. **Flag**: flag{rsa_decrypted}
6. **Points**: 300
7. **Challenge File**: Upload `encrypted_message.txt`
8. **Is Active**: ✓ Check

Users download the encrypted message and decrypt it.

## File Upload Limits

- Maximum file size: Depends on Django settings (default: unlimited)
- Supported formats: Any file type
- Recommended: Keep files under 100MB for faster downloads

## Security Considerations

✅ **DO:**
- Scan uploaded files for malware before uploading
- Use meaningful file names
- Organize files by challenge type
- Keep backups of challenge files

❌ **DON'T:**
- Upload files with sensitive information
- Upload files larger than necessary
- Share admin credentials with users

## Troubleshooting

### File Not Downloading
- Check if file exists in `media/challenges/` folder
- Verify file permissions (should be readable)
- Check Django MEDIA_URL and MEDIA_ROOT settings

### File Upload Failed
- Check file size limit
- Verify write permissions on `media/` folder
- Ensure file format is supported

### Users Can't See Download Button
- Verify challenge file is uploaded
- Check if challenge is active
- Refresh the page

## File Management

### View Uploaded Files
```bash
ls -la media/challenges/
```

### Delete Old Files
```bash
rm -rf media/challenges/2025/11/
```

### Backup Challenge Files
```bash
tar -czf challenges_backup.tar.gz media/challenges/
```

## Docker Deployment

When deploying with Docker, ensure:

1. **Volume Mapping**: Map `media/` folder to persistent storage
   ```yaml
   volumes:
     - ./media:/app/media
   ```

2. **File Permissions**: Ensure Docker container can write to media folder
   ```bash
   chmod -R 755 media/
   ```

3. **Backup Strategy**: Regularly backup the media folder

## API Endpoints

### Download Challenge File
```
GET /challenges/<challenge_id>/download/
```

Example:
```
http://localhost:8000/challenges/1/download/
```

Returns the file as an attachment for download.

## Next Steps

1. Create a challenge with a file upload
2. Test the download functionality
3. Verify users can access the file
4. Monitor file storage usage
