#!/bin/bash

# Quick test script for Docker setup on Mac Mini
# This helps you evaluate if Docker setup works before committing to iMac

set -e

echo "🚀 Testing Docker Setup on Mac Mini"
echo "=================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "📥 Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "✅ Docker is installed: $(docker --version)"
echo ""

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running"
    echo "🔧 Please start Docker Desktop"
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ docker-compose is not available"
    exit 1
fi

echo "✅ docker-compose is available"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "✅ Created .env file"
        echo "⚠️  Please edit .env and add your API keys (optional)"
    else
        echo "❌ env.example not found"
        exit 1
    fi
else
    echo "✅ .env file exists"
fi
echo ""

# Check if data directory exists
if [ ! -d data ]; then
    echo "📁 Creating data directory..."
    mkdir -p data
    
    # Check if existing database should be copied
    if [ -f media_tracker.db ]; then
        echo "📋 Found existing database, copying to data/..."
        cp media_tracker.db data/media_tracker.db
        echo "✅ Database copied"
    fi
else
    echo "✅ data directory exists"
fi
echo ""

# Get Mac Mini IP address
MAC_MINI_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "unknown")
echo "📍 Your Mac Mini IP address: $MAC_MINI_IP"
echo ""

# Ask about network access
read -p "Do you want to enable network access from iPad/iPhone? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ "$MAC_MINI_IP" != "unknown" ]; then
        echo "🔧 Updating .env for network access..."
        # Update API_BASE_URL in .env
        if grep -q "API_BASE_URL" .env; then
            sed -i '' "s|API_BASE_URL=.*|API_BASE_URL=http://$MAC_MINI_IP:8000|" .env
        else
            echo "API_BASE_URL=http://$MAC_MINI_IP:8000" >> .env
        fi
        echo "✅ Updated API_BASE_URL to http://$MAC_MINI_IP:8000"
        echo "📱 You can access from iPad/iPhone at: http://$MAC_MINI_IP:8501"
    else
        echo "⚠️  Could not detect IP address. Please set API_BASE_URL manually in .env"
    fi
else
    echo "ℹ️  Using localhost only. Edit .env later if you want network access."
fi
echo ""

# Build and start
echo "🔨 Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ Services are running!"
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    echo ""
    echo "🌐 Access the application:"
    echo "   - From Mac Mini: http://localhost:8501"
    if [ "$MAC_MINI_IP" != "unknown" ] && grep -q "$MAC_MINI_IP" .env 2>/dev/null; then
        echo "   - From iPad/iPhone: http://$MAC_MINI_IP:8501"
    fi
    echo ""
    echo "📝 View logs: docker-compose logs -f"
    echo "🛑 Stop services: docker-compose down"
    echo ""
    echo "✨ Setup complete! Test it out and see if you want to keep it here or move to iMac."
else
    echo ""
    echo "❌ Services failed to start. Check logs:"
    echo "   docker-compose logs"
    exit 1
fi

