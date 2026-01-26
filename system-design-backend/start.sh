#!/bin/bash

echo "🚀 Starting System Design Playground Backend..."

# Create data directory if it doesn't exist
mkdir -p ./data

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build and start services
echo "📦 Building and starting services..."
docker-compose up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "🔍 Checking service status..."
docker-compose ps

# Show logs
echo "📋 Recent logs:"
docker-compose logs --tail=20

echo ""
echo "✅ Backend is running!"
echo "🌐 API: http://localhost:8000"
echo "📊 Health: http://localhost:8000/health"
echo "🔧 Redis: localhost:6379"
echo ""
echo "To stop: docker-compose down"
echo "To view logs: docker-compose logs -f"