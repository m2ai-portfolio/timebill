#!/bin/bash
set -e

echo "=== TimeBill Development Setup ==="

# Ensure we're in the project directory
cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dev dependencies
pip install pytest > /dev/null 2>&1

# Create data directory
mkdir -p data

echo "=== Setup complete ==="
echo "Virtual environment activated. Run: python -m timebill agent"
