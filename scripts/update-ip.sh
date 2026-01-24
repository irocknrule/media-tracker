#!/bin/bash

# Get current IP address
CURRENT_IP=$(ipconfig getifaddr en0)

if [ -z "$CURRENT_IP" ]; then
    echo "Error: Could not get IP address. Make sure you're connected to WiFi."
    exit 1
fi

echo "Current IP address: $CURRENT_IP"

# Update .env file
ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found"
    exit 1
fi

# Backup current .env
cp "$ENV_FILE" "$ENV_FILE.backup"

# Update API_BASE_URL
sed -i '' "s|API_BASE_URL=http://.*:8000|API_BASE_URL=http://$CURRENT_IP:8000|" "$ENV_FILE"

echo "Updated .env file with IP: $CURRENT_IP"
echo ""
echo "Restarting Docker containers..."
docker-compose down
docker-compose up -d

echo ""
echo "✅ Done! Access your app at:"
echo "   Local: http://localhost:8501"
echo "   Network: http://$CURRENT_IP:8501"


