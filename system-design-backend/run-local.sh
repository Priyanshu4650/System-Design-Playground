#!/bin/bash

echo "🧪 Testing System Design Backend Locally..."

# Create data directory
mkdir -p ./data

# Set environment variables for local testing
export PYTHONPATH=$(pwd)
export DATABASE_PATH=./data/system_design.db

# Check if Redis is available (optional)
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is available"
        export REDIS_URL=redis://localhost:6379
    else
        echo "⚠️  Redis not running, will run without cache"
    fi
else
    echo "⚠️  Redis not installed, will run without cache"
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "🚀 Starting backend server..."
echo "🌐 Server will be available at: http://localhost:8000"
echo "📊 Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"

uvicorn main:app --host 0.0.0.0 --port 8000 --reload