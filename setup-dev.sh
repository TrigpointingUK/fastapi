#!/bin/bash
# Development environment setup script
# Run this once: chmod +x setup-dev.sh && ./setup-dev.sh

set -e

echo "🔧 Setting up development environment..."

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hook
echo "🪝 Installing git hooks..."
cp .githooks/pre-commit .git/hooks/pre-commit
cp .githooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/pre-push

# Run initial CI check
echo "🧪 Running initial CI check..."
make ci

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Always activate the virtual environment: source venv/bin/activate"
echo "2. Run 'make ci' before every commit (now automated via pre-commit hook)"
echo "3. The pre-commit hook will automatically run CI checks on every commit"
echo ""
echo "🚀 Happy coding!"
