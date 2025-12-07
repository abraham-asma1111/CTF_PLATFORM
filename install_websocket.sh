#!/bin/bash

echo "🚀 Installing WebSocket dependencies for CTF Platform..."
echo ""

# Check if running in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Not in a virtual environment!"
    echo ""
    echo "Please install packages manually:"
    echo "  pip install --user channels daphne channels-redis"
    echo ""
    echo "Or create a virtual environment:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Install packages
echo "📦 Installing packages..."
pip install channels daphne channels-redis

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎯 Next steps:"
echo "  1. Run the server: python manage.py runserver"
echo "  2. Open browser and check console (F12)"
echo "  3. You should see: '✅ WebSocket connected for event status'"
echo ""
echo "📖 For more info, see: WEBSOCKET_SETUP_GUIDE.md"
