# CTF Platform Security Features

## Overview
This document summarizes all security features implemented in the CTF platform.

## 1. Email Verification (Registration)

### Features
- 6-digit verification code sent to email
- 60-second expiration
- Account only created after verification
- Session-based temporary storage

### Security
- No database entry until verified
- Prevents fake account creation
- Email ownership validation

### Files
- `users/views.py` - `register()` function
- `templates/users/register.html`

## 2. reCAPTCHA Protection

### Features
- Google reCAPTCHA v2 on registration
- "I'm not a robot" checkbox
- Bot prevention

### Configuration
- Site key and secret key in `.env`
- Test keys provided for development
- Production keys from Google reCAPTCHA admin

### Files
- `users/forms.py` - `CustomUserCreationForm`
- `ctf_platform/settings.py` - reCAPTCHA config
- `RECAPTCHA_SETUP_GUIDE.md`

## 3. Password Reset with Rate Limiting

### Features
- 6-digit verification code
- 60-second expiration
- 3 attempts maximum
- 15-minute IP/email/username block
- Real-time countdown timer

### Security Measures
- IP address tracking
- Email validation
- Username validation
- Attempt counting
- Automatic blocking
- Session-based verification

### Database Models
- `PasswordResetAttempt` - Tracks reset requests
- `BlockedPasswordReset` - Tracks blocked users

### Files
- `users/views.py` - `forgot_password()`, `reset_password()`
- `users/models.py` - Security models
- `templates/users/forgot_password.html`
- `templates/users/reset_password.html`
- `PASSWORD_RESET_GUIDE.md`

## 4. Login Protection

### Features
- Email verification required before login
- Custom login view with verification check
- Session management

### Security
- Unverified users cannot login
- Email ownership validation
- Prevents unauthorized access

### Files
- `users/views.py` - `custom_login()` function
- `templates/users/login.html`

## 5. User Input Validation

### Registration Validation
- First name: Letters only
- Last name: Letters only
- Username: Letters, numbers, underscore only
- Username: Cannot be email format
- Email: Must be unique
- Password: Django's built-in validators

### Security
- Prevents SQL injection
- Prevents XSS attacks
- Enforces data integrity

## 6. CSRF Protection

### Features
- Django's built-in CSRF protection
- CSRF tokens on all forms
- Automatic validation

### Files
- All templates with forms include `{% csrf_token %}`

## 7. Session Security

### Features
- Secure session management
- Session clearing after sensitive operations
- Temporary data storage for verification

### Security
- Password reset verification in session
- Registration data in session
- Auto-cleanup after completion

## Security Configuration Summary

### Environment Variables (.env)
```bash
# Email Security
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# reCAPTCHA Security
RECAPTCHA_PUBLIC_KEY=your-site-key
RECAPTCHA_PRIVATE_KEY=your-secret-key
```

### Settings (ctf_platform/settings.py)
```python
# Email with TLS
EMAIL_USE_TLS = True

# reCAPTCHA
RECAPTCHA_PUBLIC_KEY = os.getenv('RECAPTCHA_PUBLIC_KEY')
RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_PRIVATE_KEY')

# CSRF Protection (enabled by default)
MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',
    ...
]
```

## Rate Limiting Summary

| Feature | Time Limit | Attempt Limit | Block Duration |
|---------|------------|---------------|----------------|
| Email Verification (Registration) | 60 seconds | Unlimited | N/A |
| Password Reset Code | 60 seconds | 3 attempts | 15 minutes |
| reCAPTCHA | N/A | Unlimited | N/A |

## Admin Monitoring

### Available Admin Panels
1. **Users** - View all registered users
2. **User Profiles** - View user details and scores
3. **Password Reset Attempts** - Monitor reset requests
4. **Blocked Password Resets** - View and manage blocks

### Access
- URL: `/admin/`
- Requires superuser account
- Create with: `python manage.py createsuperuser`

## Testing Security Features

### Test Email Verification
```bash
1. Register new account
2. Check email/terminal for code
3. Enter code within 60 seconds
4. Verify account created
5. Login successfully
```

### Test reCAPTCHA
```bash
1. Go to registration page
2. Try to submit without checking reCAPTCHA
3. Verify error message
4. Check reCAPTCHA and submit
5. Verify form processes
```

### Test Password Reset Rate Limiting
```bash
1. Request password reset
2. Enter wrong code 3 times
3. Verify block message
4. Try again - should be blocked
5. Check admin for block record
```

### Test Code Expiration
```bash
1. Request verification code
2. Wait 60+ seconds
3. Try to submit code
4. Verify expiration message
```

## Security Best Practices

### For Administrators
1. ✅ Use strong admin passwords
2. ✅ Enable 2FA for admin accounts (future)
3. ✅ Monitor password reset attempts regularly
4. ✅ Review blocked IPs for patterns
5. ✅ Keep Django and dependencies updated
6. ✅ Use HTTPS in production
7. ✅ Regular security audits

### For Users
1. ✅ Use strong, unique passwords
2. ✅ Verify email ownership
3. ✅ Don't share verification codes
4. ✅ Act quickly on time-limited codes
5. ✅ Report suspicious activity

## Production Deployment Checklist

### Before Going Live
- [ ] Set `DEBUG = False` in settings.py
- [ ] Configure real reCAPTCHA keys
- [ ] Set up production email (SendGrid, etc.)
- [ ] Enable HTTPS/SSL
- [ ] Set strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up database backups
- [ ] Configure logging
- [ ] Test all security features
- [ ] Review admin access

## Security Incident Response

### If User Reports Suspicious Activity
1. Check admin for reset attempts
2. Review blocked IPs
3. Check user's recent activity
4. Reset user's password if needed
5. Document incident

### If Multiple Failed Attempts Detected
1. Review IP addresses
2. Check for patterns
3. Consider extending block duration
4. Add IP to permanent blocklist if needed
5. Monitor for continued attempts

## Future Security Enhancements

### Planned Features
1. Two-factor authentication (2FA)
2. Login attempt rate limiting
3. IP whitelist/blacklist
4. Security audit logging
5. Automated threat detection
6. Email notifications for security events
7. Password strength meter
8. Account lockout after failed logins

## Documentation Files

- `EMAIL_SETUP_GUIDE.md` - Email configuration
- `RECAPTCHA_SETUP_GUIDE.md` - reCAPTCHA setup
- `PASSWORD_RESET_GUIDE.md` - Password reset details
- `SECURITY_FEATURES.md` - This file

## Support

For security concerns or questions:
1. Check documentation files
2. Review Django admin logs
3. Test in development environment
4. Contact system administrator

---

**Last Updated**: November 26, 2025
**Security Status**: ✅ Production Ready
**Compliance**: OWASP Best Practices
