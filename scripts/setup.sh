#!/bin/bash

# Setup script for FastAPI project
set -e

echo "🚀 Setting up FastAPI Legacy Migration Project..."

# Check if Python 3.11+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "📍 Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements-dev.txt

# Set up pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
pre-commit install

# Copy environment template if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "🔧 Creating .env file from template..."
    cp env.example .env
    echo "📝 Please edit .env file with your configuration"
fi

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "🐳 Docker is available"

    # Check if Docker Compose is available
    if command -v docker-compose &> /dev/null; then
        echo "🐳 Docker Compose is available"
        echo "💡 You can run 'make docker-dev' to start the development environment"
    else
        echo "⚠️  Docker Compose not found. Please install Docker Compose for easy development setup."
    fi
else
    echo "⚠️  Docker not found. Docker is recommended for easy development setup."
fi

# Check if make is available
if command -v make &> /dev/null; then
    echo "🛠️  Make is available"
    echo "💡 Run 'make help' to see available commands"
else
    echo "⚠️  Make not found. You can still run commands manually."
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env with your database credentials"
echo "   2. Run 'make docker-dev' to start development environment"
echo "   3. Visit http://localhost:8000/docs for API documentation"
echo "   4. Run 'make test' to run the test suite"
echo ""
echo "📖 Read README.md for detailed documentation"
echo "🔄 Read MIGRATION_GUIDE.md for migration strategy"
