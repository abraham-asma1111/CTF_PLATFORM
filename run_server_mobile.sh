#!/bin/bash

# Get local IP address
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo "=========================================="
echo "  CTF Platform - Mobile Access"
echo "=========================================="
echo ""
echo "Your local IP: $LOCAL_IP"
echo ""
echo "📱 Access from your phone:"
echo "   http://$LOCAL_IP:8000"
echo ""
echo "⚠️  Make sure:"
echo "   1. Your phone is on the same WiFi"
echo "   2. Firewall allows port 8000"
echo ""
echo "Starting server..."
echo "=========================================="
echo ""

python manage.py runserver 0.0.0.0:8000
