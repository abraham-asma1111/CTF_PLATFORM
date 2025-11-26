#!/bin/bash

# Email Configuration Setup Script for CTF Platform

echo "================================"
echo "CTF Platform - Email Setup"
echo "================================"
echo ""

# Check if .env file exists
if [ -f .env ]; then
    echo "✓ .env file already exists"
    echo ""
    echo "Current email configuration:"
    grep "EMAIL" .env || echo "No email configuration found"
    echo ""
    read -p "Do you want to update email configuration? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping email setup"
        exit 0
    fi
else
    echo "Creating .env file..."
    cp .env.example .env
fi

echo ""
echo "Email Provider Options:"
echo "1. Gmail (Recommended)"
echo "2. SendGrid"
echo "3. Outlook/Hotmail"
echo "4. Yahoo Mail"
echo "5. Other SMTP"
echo ""
read -p "Select email provider (1-5): " provider

case $provider in
    1)
        echo ""
        echo "Gmail Setup Instructions:"
        echo "1. Go to https://myaccount.google.com/"
        echo "2. Enable 2-Step Verification"
        echo "3. Go to https://myaccount.google.com/apppasswords"
        echo "4. Generate an App Password"
        echo ""
        read -p "Enter your Gmail address: " email
        read -sp "Enter your 16-character App Password: " password
        echo ""
        
        sed -i "s/EMAIL_HOST=.*/EMAIL_HOST=smtp.gmail.com/" .env
        sed -i "s/EMAIL_PORT=.*/EMAIL_PORT=587/" .env
        sed -i "s/EMAIL_USE_TLS=.*/EMAIL_USE_TLS=True/" .env
        sed -i "s/EMAIL_HOST_USER=.*/EMAIL_HOST_USER=$email/" .env
        sed -i "s|EMAIL_HOST_PASSWORD=.*|EMAIL_HOST_PASSWORD=$password|" .env
        sed -i "s/DEFAULT_FROM_EMAIL=.*/DEFAULT_FROM_EMAIL=$email/" .env
        sed -i "s/EMAIL_BACKEND=.*/EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend/" .env
        ;;
    2)
        echo ""
        read -p "Enter your SendGrid API Key: " api_key
        
        sed -i "s/EMAIL_HOST=.*/EMAIL_HOST=smtp.sendgrid.net/" .env
        sed -i "s/EMAIL_PORT=.*/EMAIL_PORT=587/" .env
        sed -i "s/EMAIL_USE_TLS=.*/EMAIL_USE_TLS=True/" .env
        sed -i "s/EMAIL_HOST_USER=.*/EMAIL_HOST_USER=apikey/" .env
        sed -i "s|EMAIL_HOST_PASSWORD=.*|EMAIL_HOST_PASSWORD=$api_key|" .env
        sed -i "s/EMAIL_BACKEND=.*/EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend/" .env
        ;;
    3)
        echo ""
        read -p "Enter your Outlook email: " email
        read -sp "Enter your Outlook password: " password
        echo ""
        
        sed -i "s/EMAIL_HOST=.*/EMAIL_HOST=smtp-mail.outlook.com/" .env
        sed -i "s/EMAIL_PORT=.*/EMAIL_PORT=587/" .env
        sed -i "s/EMAIL_USE_TLS=.*/EMAIL_USE_TLS=True/" .env
        sed -i "s/EMAIL_HOST_USER=.*/EMAIL_HOST_USER=$email/" .env
        sed -i "s|EMAIL_HOST_PASSWORD=.*|EMAIL_HOST_PASSWORD=$password|" .env
        sed -i "s/DEFAULT_FROM_EMAIL=.*/DEFAULT_FROM_EMAIL=$email/" .env
        sed -i "s/EMAIL_BACKEND=.*/EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend/" .env
        ;;
    4)
        echo ""
        read -p "Enter your Yahoo email: " email
        read -sp "Enter your Yahoo App Password: " password
        echo ""
        
        sed -i "s/EMAIL_HOST=.*/EMAIL_HOST=smtp.mail.yahoo.com/" .env
        sed -i "s/EMAIL_PORT=.*/EMAIL_PORT=587/" .env
        sed -i "s/EMAIL_USE_TLS=.*/EMAIL_USE_TLS=True/" .env
        sed -i "s/EMAIL_HOST_USER=.*/EMAIL_HOST_USER=$email/" .env
        sed -i "s|EMAIL_HOST_PASSWORD=.*|EMAIL_HOST_PASSWORD=$password|" .env
        sed -i "s/DEFAULT_FROM_EMAIL=.*/DEFAULT_FROM_EMAIL=$email/" .env
        sed -i "s/EMAIL_BACKEND=.*/EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend/" .env
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "✓ Email configuration updated!"
echo ""
echo "Testing email configuration..."
python manage.py shell << EOF
from django.core.mail import send_mail
try:
    send_mail(
        'CTF Platform - Test Email',
        'This is a test email from CTF Platform. If you received this, email is configured correctly!',
        None,
        ['test@example.com'],
        fail_silently=False,
    )
    print("✓ Test email sent successfully!")
except Exception as e:
    print(f"✗ Error sending test email: {str(e)}")
EOF

echo ""
echo "Setup complete! Your email is now configured."
echo "Users will receive verification codes when they register."
