#!/bin/bash
# TimeBill - Development Server Initialization
set -e

cd "$(dirname "$0")"

# Check Python version
python3 --version 2>/dev/null || { echo "Python 3 is required"; exit 1; }

# Set default environment variables
export TIMEBILL_DB_PATH="${TIMEBILL_DB_PATH:-./data/timebill.db}"
export TIMEBILL_LOG_LEVEL="${TIMEBILL_LOG_LEVEL:-INFO}"
export TIMEBILL_IDLE_SECONDS="${TIMEBILL_IDLE_SECONDS:-300}"

# Create data directory if needed
mkdir -p data

# Install pytest if needed (for testing)
pip install pytest --quiet 2>/dev/null || true

echo "TimeBill environment ready."
echo "Run: python -m timebill agent"
