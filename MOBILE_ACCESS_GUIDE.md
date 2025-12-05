# Mobile Access Guide

## Quick Start

### 1. Start Server for Mobile Access
```bash
./run_server_mobile.sh
```

Or manually:
```bash
python manage.py runserver 0.0.0.0:8000
```

### 2. Access from Phone
Open browser on your phone and go to:
```
http://10.161.170.159:8000
```

---

## reCAPTCHA Domain Error Fix

### Problem
"ERROR for site owner: Invalid domain for site key"

### Solution Options

#### Option 1: Add Domain to reCAPTCHA (Recommended for Testing)
1. Go to [Google reCAPTCHA Admin](https://www.google.com/recaptcha/admin)
2. Select your site
3. Click "Settings"
4. Under "Domains", add:
   - `10.161.170.159`
   - Or use `localhost` (if testing locally)
5. Save changes

#### Option 2: Use Test Keys (Development Only)
Update `.env` file:
```env
RECAPTCHA_PUBLIC_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
RECAPTCHA_PRIVATE_KEY=6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe
```

These are Google's official test keys that work on any domain.

#### Option 3: Temporarily Disable reCAPTCHA
In `ctf_platform/settings.py`, uncomment:
```python
RECAPTCHA_DISABLE = True
```

**⚠️ Remember to re-enable for production!**

---

## Mobile Responsiveness Features

### ✅ Implemented
- Responsive navigation (collapses on mobile)
- Touch-friendly buttons (44px minimum)
- Scalable forms (prevents zoom on iOS)
- Responsive tables
- Mobile-optimized cards
- Adaptive reCAPTCHA sizing
- Landscape mode support
- Touch-specific interactions

### Screen Breakpoints
- **Desktop**: > 768px
- **Tablet**: 768px - 480px
- **Mobile**: < 480px
- **Landscape**: < 896px (landscape orientation)

---

## Testing Checklist

### On Your Phone
- [ ] Homepage loads correctly
- [ ] Navigation menu works
- [ ] Login form is usable
- [ ] Register form is usable
- [ ] reCAPTCHA displays properly
- [ ] Challenge list is readable
- [ ] Challenge detail page works
- [ ] Flag submission works
- [ ] Leaderboard is viewable
- [ ] Profile page displays correctly
- [ ] Settings page is accessible

### Common Issues

#### 1. Can't Connect
**Check:**
- Phone and computer on same WiFi
- Firewall allows port 8000: `sudo ufw allow 8000`
- Server running on `0.0.0.0:8000`

#### 2. reCAPTCHA Error
**Fix:**
- Add domain to reCAPTCHA admin
- Or use test keys
- Or temporarily disable

#### 3. Layout Broken
**Fix:**
- Clear browser cache
- Hard refresh (Ctrl+Shift+R)
- Check CSS loaded: View source → verify `/static/css/style.css`

#### 4. Zoom Issues on iOS
**Fixed by:**
- Input fields have `font-size: 16px` (prevents auto-zoom)
- Viewport meta tag properly set

---

## Network Configuration

### Find Your IP
```bash
hostname -I | awk '{print $1}'
```

### Allow Firewall (if needed)
```bash
sudo ufw allow 8000
sudo ufw status
```

### Check Server is Listening
```bash
netstat -tuln | grep 8000
```

Should show:
```
tcp  0  0  0.0.0.0:8000  0.0.0.0:*  LISTEN
```

---

## Production Deployment

For actual deployment (not local testing):

### 1. Use a Real Domain
- Register domain (e.g., `ctfplatform.com`)
- Point DNS to your server IP

### 2. Update Settings
```python
ALLOWED_HOSTS = ['ctfplatform.com', 'www.ctfplatform.com']
DEBUG = False
```

### 3. Configure reCAPTCHA
- Add production domain to reCAPTCHA admin
- Use production keys (not test keys)

### 4. Use HTTPS
- Get SSL certificate (Let's Encrypt)
- Configure nginx/Apache with SSL

### 5. Use Production Server
- Gunicorn or uWSGI
- Not Django development server

---

## Troubleshooting Commands

### Check if port is open
```bash
nc -zv 10.161.170.159 8000
```

### Test from computer browser
```
http://10.161.170.159:8000
```

### View Django logs
Watch terminal where server is running

### Check phone's IP (to verify same network)
Phone Settings → WiFi → Network Details

---

## Security Notes

⚠️ **Development Server Warning**
- Django's `runserver` is NOT for production
- Only use for local development/testing
- No security hardening
- Single-threaded (slow)

⚠️ **Network Exposure**
- Running on `0.0.0.0:8000` exposes to local network
- Anyone on your WiFi can access
- Don't use on public WiFi
- Don't expose to internet without proper security

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start server | `./run_server_mobile.sh` |
| Find IP | `hostname -I` |
| Allow firewall | `sudo ufw allow 8000` |
| Check port | `netstat -tuln \| grep 8000` |
| Access URL | `http://10.161.170.159:8000` |

---

## Support

If issues persist:
1. Check server logs in terminal
2. Check browser console (F12 → Console)
3. Verify network connectivity
4. Try different browser on phone
5. Restart Django server
