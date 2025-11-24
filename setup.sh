#!/bin/bash

echo "🚩 Setting up CTF Platform..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "🗄️ Setting up database..."
python manage.py migrate

# Create sample challenges
echo "🎯 Creating sample challenges..."
python manage.py create_sample_challenges

# Create superuser (optional)
echo "👤 Create superuser? (y/n)"
read -r create_superuser
if [ "$create_superuser" = "y" ]; then
    python manage.py createsuperuser
fi

echo "✅ Setup complete!"
echo "🚀 Run 'python manage.py runserver' to start the platform"
echo "🌐 Visit http://127.0.0.1:8000 to access the CTF platform"
echo "🔧 Admin panel: http://127.0.0.1:8000/admin/"