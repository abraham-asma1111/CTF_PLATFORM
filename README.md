# CTF Platform

A complete Capture The Flag (CTF) platform built with Django and vanilla HTML/CSS/JavaScript.

## Features

- 🔐 User registration and authentication
- 🎯 Challenge management with categories and difficulty levels
- 🚩 Flag submission with real-time validation
- 🏆 Live leaderboard with automatic updates
- 👤 User profiles with progress tracking
- 🔒 Secure flag storage with hashing
- 📱 Responsive design for all devices
- ⚡ AJAX-powered interactions

## Challenge Categories

- **Web**: Web application security vulnerabilities
- **Cryptography**: Encryption, decryption, and cryptographic puzzles
- **Forensics**: Digital forensics and data recovery
- **Binary Exploitation**: Buffer overflows and binary analysis
- **Reverse Engineering**: Analyzing and understanding compiled code
- **Miscellaneous**: Various other security challenges

## Quick Start

### Prerequisites

- Python 3.8+
- Django 4.2+

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ctf_platform
```

2. Install dependencies:
```bash
pip install django
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Create a superuser:
```bash
python manage.py createsuperuser
```

5. Load sample challenges:
```bash
python manage.py create_sample_challenges
```

6. Start the development server:
```bash
python manage.py runserver
```

7. Visit `http://127.0.0.1:8000` to access the platform

## Admin Panel

Access the admin panel at `http://127.0.0.1:8000/admin/` to:
- Add/edit challenges
- View submissions
- Manage users
- Monitor platform activity

## Sample Challenges

The platform comes with 8 sample challenges across different categories:

1. **Welcome to CTF** (Misc, 50 pts) - Easy
2. **Basic Web Challenge** (Web, 100 pts) - Easy
3. **Caesar Cipher** (Crypto, 75 pts) - Easy
4. **SQL Injection** (Web, 200 pts) - Medium
5. **Buffer Overflow** (Pwn, 300 pts) - Hard
6. **Reverse Engineering** (Reverse, 250 pts) - Medium
7. **Digital Forensics** (Forensics, 180 pts) - Medium
8. **Advanced Crypto** (Crypto, 400 pts) - Hard

## Architecture

### Backend (Django)
- **users**: User authentication and profiles
- **challenges**: Challenge management and display
- **submissions**: Flag submission and validation
- **leaderboard**: Scoring and rankings

### Frontend (Vanilla JS)
- Pure HTML templates with Django template engine
- CSS with responsive design and animations
- JavaScript for AJAX submissions and live updates
- No external frameworks or libraries

### Security Features
- CSRF protection on all forms
- Flag hashing with SHA-256
- Input validation and sanitization
- Session-based authentication
- XSS protection through template escaping

## Customization

### Adding New Challenges

1. Use the admin panel to add challenges manually
2. Or create a management command similar to `create_sample_challenges.py`

### Styling

- Edit `static/css/style.css` for visual customization
- Modify templates in `templates/` for layout changes

### Functionality

- Add new challenge categories in `challenges/models.py`
- Extend user profiles in `users/models.py`
- Add new views and URLs as needed

## Production Deployment

For production deployment, consider:

1. Use PostgreSQL instead of SQLite
2. Configure static file serving
3. Set up proper logging
4. Use environment variables for secrets
5. Enable HTTPS
6. Set `DEBUG = False`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.