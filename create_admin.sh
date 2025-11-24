#!/bin/bash

# CTF Platform Admin Creation Script

echo "================================"
echo "CTF Platform - Admin Setup"
echo "================================"
echo ""

# Check if superuser already exists
python manage.py shell << END
from django.contrib.auth.models import User
if User.objects.filter(is_superuser=True).exists():
    print("✓ Superuser already exists!")
    exit(0)
else:
    print("No superuser found. Creating one...")
    exit(1)
END

if [ $? -eq 0 ]; then
    echo ""
    echo "Admin panel is ready at: http://localhost:8000/admin/"
    exit 0
fi

echo ""
echo "Creating superuser account..."
echo "Please enter the following information:"
echo ""

python manage.py createsuperuser

echo ""
echo "================================"
echo "✓ Admin account created!"
echo "================================"
echo ""
echo "Access the admin panel at:"
echo "  http://localhost:8000/admin/"
echo ""
echo "Next steps:"
echo "1. Start the server: python manage.py runserver"
echo "2. Login to admin panel with your credentials"
echo "3. Create challenges in the Challenges section"
echo ""
