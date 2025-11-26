# Email Configuration Guide for CTF Platform

## Overview
The CTF platform uses email verification for user registration. This guide explains how to set up real email sending.

## Option 1: Gmail (Recommended for Development)

### Step 1: Enable 2-Factor Authentication
1. Go to https://myaccount.google.com/
2. Click "Security" in the left menu
3. Enable "2-Step Verification"

### Step 2: Create App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer" (or your device)
3. Google will generate a 16-character password
4. Copy this password (you'll need it in Step 3)

### Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### Step 4: Install python-dotenv

```bash
pip install python-dotenv
```

### Step 5: Update settings.py to load .env

Add this at the top of `ctf_platform/settings.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

## Option 2: SendGrid (Recommended for Production)

### Step 1: Create SendGrid Account
1. Sign up at https://sendgrid.com/
2. Create an API key

### Step 2: Configure Environment Variables

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

## Option 3: Other SMTP Providers

### Outlook/Hotmail
```bash
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
```

### Yahoo Mail
```bash
EMAIL_HOST=smtp.mail.yahoo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@yahoo.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Testing Email Configuration

Run this command to test your email setup:

```bash
python manage.py shell
```

Then in the Python shell:

```python
from django.core.mail import send_mail

send_mail(
    'Test Email',
    'This is a test email from CTF Platform',
    'your-email@gmail.com',
    ['recipient@example.com'],
    fail_silently=False,
)
```

## Troubleshooting

### "SMTPAuthenticationError: 535-5.7.8 Username and password not accepted"
- Make sure you're using an App Password (not your regular Gmail password)
- Verify 2-Factor Authentication is enabled
- Check that EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are correct

### "SMTPException: SMTP AUTH extension not supported by server"
- Make sure EMAIL_USE_TLS is set to True
- Verify EMAIL_PORT is 587 (not 465 or 25)

### Emails not being sent
- Check that EMAIL_BACKEND is set to `django.core.mail.backends.smtp.EmailBackend`
- Verify all environment variables are set correctly
- Check Django logs for error messages

## Security Best Practices

1. **Never commit credentials** - Always use environment variables
2. **Use App Passwords** - Don't use your main account password
3. **Rotate credentials** - Change passwords periodically
4. **Use HTTPS** - Always use TLS/SSL for email
5. **Monitor logs** - Check for failed authentication attempts

## Environment Variables Summary

| Variable | Description | Example |
|----------|-------------|---------|
| EMAIL_BACKEND | Email backend to use | django.core.mail.backends.smtp.EmailBackend |
| EMAIL_HOST | SMTP server address | smtp.gmail.com |
| EMAIL_PORT | SMTP port | 587 |
| EMAIL_USE_TLS | Use TLS encryption | True |
| EMAIL_HOST_USER | Email account username | your-email@gmail.com |
| EMAIL_HOST_PASSWORD | Email account password/app-password | your-16-char-password |
| DEFAULT_FROM_EMAIL | Sender email address | noreply@ctfplatform.com |

## Current Configuration

The platform is currently configured to read from environment variables. To use real email:

1. Set up your email provider (Gmail recommended)
2. Create a `.env` file with your credentials
3. Restart the Django server
4. Test by registering a new user

The verification code will be sent to the user's email address automatically.
