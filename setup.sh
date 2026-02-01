#!/bin/bash

# Setup script for GitHub Repository Checker

set -e

echo "🚀 Setting up GitHub Repository Checker..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Install dev dependencies
echo "📥 Installing dev dependencies..."
pip install pytest pytest-cov black flake8

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found!"
    echo "📝 Please create a .env file with your GitHub token:"
    echo ""
    echo "   GITHUB_TOKEN=your_token_here"
    echo ""
    echo "Get a token from: https://github.com/settings/tokens"
    echo ""
    
    read -p "Would you like to create .env file now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your GitHub token: " github_token
        echo "GITHUB_TOKEN=$github_token" > .env
        echo "✓ .env file created"
    fi
else
    echo "✓ .env file exists"
fi

# Make main.py executable
chmod +x main.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "To use the tool:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run commands:"
echo "     ./main.py verify https://github.com/owner/repo"
echo "     ./main.py search --language Python --min-stars 100"
echo ""
echo "To run tests:"
echo "  pytest test_checker.py -v"
echo ""
