# Password Reset Security Guide

## Overview
The CTF platform implements a secure password reset system with rate limiting and IP blocking to prevent abuse.

## Features

### 1. 6-Digit Verification Code
- Random 6-digit code sent to user's email
- Code expires in 60 seconds
- Code is single-use only

### 2. Rate Limiting
- Maximum 3 attempts per reset request
- After 3 failed attempts, user is blocked for 15 minutes
- Countdown timer shows remaining time

### 3. IP Blocking
- Blocks by IP address, email, and username
- 15-minute block duration
- Prevents brute force attacks

### 4. Security Measures
- Tracks all reset attempts in database
- Logs IP addresses for security auditing
- Prevents multiple simultaneous reset requests
- Clears session after successful reset

## User Flow

### Step 1: Request Password Reset
1. User clicks "Forgot your password?" on login page
2. Enters email or username
3. System validates user exists

### Step 2: Receive Verification Code
1. 6-digit code sent to registered email
2. Code displayed in terminal (development mode)
3. 60-second countdown timer starts

### Step 3: Enter Verification Code
1. User enters 6-digit code
2. System validates code and checks:
   - Code matches
   - Code not expired
   - Attempts < 3
   - User not blocked

### Step 4: Reset Password
1. After successful verification, user enters new password
2. Password must be at least 8 characters
3. Passwords must match
4. Account updated, session cleared

## Rate Limiting Details

### Attempt Tracking
- Each verification code submission counts as 1 attempt
- Maximum 3 attempts per reset request
- Attempts reset when new code is requested

### Blocking Triggers
- 3 failed verification attempts
- User blocked for 15 minutes
- Block applies to:
  - Email address
  - IP address
  - Username

### Block Duration
- 15 minutes from last failed attempt
- Automatic unblock after duration
- Admin can manually unblock via Django admin

## Database Models

### PasswordResetAttempt
Tracks each password reset request:
- `email` - User's email address
- `ip_address` - Client IP address
- `reset_code` - 6-digit verification code
- `attempts` - Number of failed attempts
- `created_at` - When code was generated
- `expires_at` - When code expires (60 seconds)
- `is_used` - Whether code has been used

### BlockedPasswordReset
Tracks blocked users:
- `email` - Blocked email address
- `ip_address` - Blocked IP address
- `username` - Blocked username
- `reason` - Why user was blocked
- `blocked_at` - When block started
- `blocked_until` - When block expires (15 minutes)

## Admin Management

### View Reset Attempts
1. Login to Django admin: `/admin/`
2. Navigate to "Password reset attempts"
3. View all reset requests with:
   - Email and IP
   - Number of attempts
   - Expiration time
   - Usage status

### View Blocked Users
1. Login to Django admin: `/admin/`
2. Navigate to "Blocked password resets"
3. View all blocks with:
   - Email, username, IP
   - Block reason
   - Block duration
   - Active status

### Manually Unblock User
1. Find blocked user in admin
2. Delete the block record
3. User can immediately request new reset

## Security Best Practices

### For Administrators
1. **Monitor reset attempts** - Check admin regularly for suspicious activity
2. **Review blocked IPs** - Investigate repeated blocks from same IP
3. **Adjust block duration** - Modify `timedelta(minutes=15)` in code if needed
4. **Enable email logging** - Monitor all password reset emails sent

### For Users
1. **Check spam folder** - Verification emails might be filtered
2. **Act quickly** - Code expires in 60 seconds
3. **Don't share codes** - Codes are single-use and personal
4. **Contact admin if blocked** - If legitimately blocked, admin can help

## Configuration

### Adjust Code Expiration Time
In `users/views.py`, modify:
```python
expires_at=timezone.now() + timedelta(seconds=60)  # Change 60 to desired seconds
```

### Adjust Block Duration
In `users/views.py`, modify:
```python
blocked_until=timezone.now() + timedelta(minutes=15)  # Change 15 to desired minutes
```

### Adjust Maximum Attempts
In `users/views.py`, modify:
```python
if reset_attempt.attempts >= 3:  # Change 3 to desired max attempts
```

## Testing

### Test Normal Flow
1. Go to `/users/forgot-password/`
2. Enter valid email/username
3. Check terminal for code
4. Enter code within 60 seconds
5. Set new password
6. Login with new password

### Test Rate Limiting
1. Request password reset
2. Enter wrong code 3 times
3. Verify block message appears
4. Try again - should show "temporarily blocked"
5. Wait 15 minutes or unblock via admin

### Test Code Expiration
1. Request password reset
2. Wait 60+ seconds
3. Try to enter code
4. Verify "expired" message appears

## Troubleshooting

### "No account found with that email or username"
- User doesn't exist in database
- Check spelling of email/username
- User might have registered with different email

### "Too many failed attempts. You are temporarily blocked."
- User exceeded 3 attempts
- Wait 15 minutes
- Or contact admin to unblock

### "Verification code expired"
- Code was not entered within 60 seconds
- Request new code
- Act faster next time

### "Invalid verification code"
- Code doesn't match
- Check email for correct code
- Check terminal in development mode
- Ensure no typos

### Email not received
- Check spam/junk folder
- Verify email configuration in `.env`
- Check Django terminal for printed code (development)
- Verify SMTP settings are correct

## API Endpoints

### Forgot Password
- **URL**: `/users/forgot-password/`
- **Method**: GET, POST
- **Parameters**:
  - `identifier` - Email or username
  - `verification_code` - 6-digit code (optional)

### Reset Password
- **URL**: `/users/reset-password/`
- **Method**: GET, POST
- **Parameters**:
  - `password1` - New password
  - `password2` - Confirm password
- **Requires**: Valid session from forgot password flow

## Security Considerations

### Timing Attacks
- Code validation uses constant-time comparison
- Prevents timing-based code guessing

### Brute Force Protection
- Rate limiting prevents rapid attempts
- IP blocking prevents distributed attacks
- Email blocking prevents account targeting

### Session Security
- Reset session cleared after use
- Session expires after password change
- Cannot reuse verification codes

### Email Security
- Codes sent via encrypted SMTP (TLS)
- Codes expire quickly (60 seconds)
- Codes are single-use only

## Monitoring

### Key Metrics to Track
1. **Reset requests per day** - Normal vs suspicious patterns
2. **Failed attempts** - High failure rate indicates attacks
3. **Blocked IPs** - Repeated blocks from same IP
4. **Code expiration rate** - Users not acting fast enough

### Alert Triggers
- More than 10 blocks per hour
- Same IP blocked multiple times
- Unusual spike in reset requests
- High failure rate (>50%)

## Future Enhancements

### Possible Improvements
1. **CAPTCHA on reset page** - Additional bot protection
2. **SMS verification** - Alternative to email
3. **Longer block duration** - For repeat offenders
4. **Whitelist IPs** - Trusted IPs bypass rate limiting
5. **Email notifications** - Alert user of reset attempts
6. **Two-factor authentication** - Additional security layer

## Resources

- Django Authentication: https://docs.djangoproject.com/en/4.2/topics/auth/
- Rate Limiting: https://django-ratelimit.readthedocs.io/
- Security Best Practices: https://docs.djangoproject.com/en/4.2/topics/security/

## Current Status

✅ Password reset with 6-digit code implemented
✅ Rate limiting (3 attempts) active
✅ IP/email/username blocking active
✅ 60-second code expiration active
✅ 15-minute block duration active
✅ Admin interface for monitoring
✅ Email notifications configured

**System is production-ready and secure!**
