#!/bin/bash

# Quick fix script for network access issues
# This script updates .env with the correct IP address and rebuilds containers

echo "=========================================="
echo "Media Tracker Network Access Fix"
echo "=========================================="
echo ""

# Get iMac IP address
IMAC_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)

if [ -z "$IMAC_IP" ]; then
    echo "❌ Could not determine IP address. Check your network connection."
    exit 1
fi

echo "Found iMac IP address: $IMAC_IP"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from env.example..."
    cp env.example .env
fi

# Update API_BASE_URL
echo "Updating API_BASE_URL in .env..."
if grep -q "^API_BASE_URL=" .env; then
    # Use sed with different syntax for macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|^API_BASE_URL=.*|API_BASE_URL=http://$IMAC_IP:8000|" .env
    else
        sed -i "s|^API_BASE_URL=.*|API_BASE_URL=http://$IMAC_IP:8000|" .env
    fi
else
    echo "API_BASE_URL=http://$IMAC_IP:8000" >> .env
fi

# Update VITE_API_BASE_URL
echo "Updating VITE_API_BASE_URL in .env..."
if grep -q "^VITE_API_BASE_URL=" .env; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|^VITE_API_BASE_URL=.*|VITE_API_BASE_URL=http://$IMAC_IP:8000|" .env
    else
        sed -i "s|^VITE_API_BASE_URL=.*|VITE_API_BASE_URL=http://$IMAC_IP:8000|" .env
    fi
else
    echo "VITE_API_BASE_URL=http://$IMAC_IP:8000" >> .env
fi

echo "✅ Updated .env file"
echo ""
echo "Current configuration:"
grep "API_BASE_URL" .env
grep "VITE_API_BASE_URL" .env
echo ""

# Ask if user wants to rebuild
read -p "Rebuild containers now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Rebuilding containers..."
    docker-compose down
    docker-compose up -d --build
    echo ""
    echo "✅ Containers rebuilt"
    echo ""
    echo "You can now access the app from other devices at:"
    echo "   http://$IMAC_IP:3000"
    echo ""
    echo "⚠️  Don't forget to check macOS Firewall settings if it still doesn't work!"
    echo "   System Settings > Network > Firewall > Options"
else
    echo ""
    echo "To apply changes, run:"
    echo "   docker-compose down"
    echo "   docker-compose up -d --build"
fi
