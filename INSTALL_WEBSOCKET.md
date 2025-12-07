# WebSocket Installation Guide

## Your System: Kali Linux with Externally Managed Python

Your system prevents direct pip installations to protect the system Python. Here are your options:

## Option 1: Use System Packages (Recommended for Kali)

```bash
# Install Django Channels from Kali repositories
sudo apt update
sudo apt install python3-channels python3-daphne
```

## Option 2: Override Protection (Use with Caution)

```bash
pip install --break-system-packages channels daphne channels-redis
```

⚠️ **Warning**: This can potentially break system packages. Only use if you understand the risks.

## Option 3: Virtual Environment (Best Practice)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install packages
pip install -r requirements.txt

# Run server
python manage.py runserver
```

## Option 4: Run Without WebSocket (Fallback)

The platform will still work without WebSocket! The LIVE indicator will use JavaScript timers instead of real-time updates.

**What works without WebSocket:**
- ✅ LIVE indicator (updates every 5 seconds via JavaScript)
- ✅ Countdown timer
- ✅ Event time validation
- ✅ Submission blocking

**What requires WebSocket:**
- ❌ Instant LIVE indicator updates when admin activates/deactivates
- ❌ Real-time leaderboard updates
- ❌ Live notifications

## Quick Test

After installation, test if WebSocket is working:

```bash
python -c "import channels; print('✅ WebSocket support available')"
```

If you see the success message, you're good to go!

## Running the Server

**With WebSocket support:**
```bash
python manage.py runserver
# or
daphne -b 0.0.0.0 -p 8000 ctf_platform.asgi:application
```

**Without WebSocket (fallback):**
```bash
# Just run normally - the platform will work fine
python manage.py runserver
```

The JavaScript fallback will check event times every 5 seconds, which is still very responsive!

## Verification

1. Start the server
2. Open your browser to http://localhost:8000
3. Open browser console (F12)
4. Look for one of these messages:

**With WebSocket:**
```
✅ WebSocket connected for event status
```

**Without WebSocket (fallback):**
```
❌ WebSocket disconnected. Reconnecting in 3 seconds...
```

Don't worry if you see the second message - the platform will still work using the JavaScript fallback!

## Recommendation

For development on Kali Linux, I recommend **Option 3 (Virtual Environment)** as it's the cleanest approach and won't affect your system Python.

```bash
# One-time setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Every time you work on the project
source venv/bin/activate
python manage.py runserver
```

## Summary

- **WebSocket is optional** - the platform works fine without it
- **JavaScript fallback** ensures LIVE indicator still works
- **Choose the installation method** that works best for your setup
- **Virtual environment** is the recommended approach

Need help? Check `WEBSOCKET_SETUP_GUIDE.md` for more details!
