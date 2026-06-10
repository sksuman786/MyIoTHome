#!/bin/bash

# MyHome IoT - Development Setup Script

echo "=========================================="
echo "MyHome IoT - Setup Script"
echo "=========================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if not exists
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠ Please edit .env with your settings"
fi

# Run migrations
echo ""
echo "Running database migrations..."
python manage.py migrate

# Create superuser
echo ""
read -p "Create superuser? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    python manage.py createsuperuser
fi

# Collect static files
echo ""
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "=========================================="
echo "Setup complete! 🎉"
echo "=========================================="
echo ""
echo "To start development:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run: python manage.py runserver"
echo "  3. Visit: http://localhost:8000"
echo "  4. Admin: http://localhost:8000/admin"
echo ""
