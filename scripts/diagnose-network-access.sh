#!/bin/bash

# Network Access Diagnostic Script for Media Tracker
# This script helps diagnose why the app can't be accessed from other devices

echo "=========================================="
echo "Media Tracker Network Access Diagnostic"
echo "=========================================="
echo ""

# 1. Check if Docker is running
echo "1. Checking Docker status..."
if docker ps > /dev/null 2>&1; then
    echo "   ✅ Docker is running"
else
    echo "   ❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi
echo ""

# 2. Check if containers are running
echo "2. Checking container status..."
if docker-compose ps | grep -q "Up"; then
    echo "   ✅ Containers are running"
    docker-compose ps
else
    echo "   ❌ Containers are not running. Start them with: docker-compose up -d"
    exit 1
fi
echo ""

# 3. Get iMac IP address
echo "3. Finding iMac IP address..."
IMAC_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)
if [ -z "$IMAC_IP" ]; then
    echo "   ❌ Could not determine IP address. Check your network connection."
    exit 1
else
    echo "   ✅ iMac IP address: $IMAC_IP"
fi
echo ""

# 4. Check port bindings
echo "4. Checking port bindings..."
BACKEND_PORT=$(docker-compose ps backend 2>/dev/null | grep -oP '0\.0\.0\.0:\K[0-9]+(?=->8000)' || echo "")
FRONTEND_PORT=$(docker-compose ps frontend-react 2>/dev/null | grep -oP '0\.0\.0\.0:\K[0-9]+(?=->80)' || echo "")

if [ -n "$BACKEND_PORT" ] && [ "$BACKEND_PORT" = "8000" ]; then
    echo "   ✅ Backend port 8000 is bound to 0.0.0.0 (accessible from network)"
else
    echo "   ⚠️  Backend port might not be accessible from network"
fi

if [ -n "$FRONTEND_PORT" ] && [ "$FRONTEND_PORT" = "3000" ]; then
    echo "   ✅ Frontend port 3000 is bound to 0.0.0.0 (accessible from network)"
else
    echo "   ⚠️  Frontend port might not be accessible from network"
fi
echo ""

# 5. Test local connectivity
echo "5. Testing local connectivity..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Backend is responding on localhost:8000"
else
    echo "   ❌ Backend is NOT responding on localhost:8000"
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "   ✅ Frontend is responding on localhost:3000"
else
    echo "   ❌ Frontend is NOT responding on localhost:3000"
fi
echo ""

# 6. Test network connectivity
echo "6. Testing network connectivity (from iMac's IP)..."
if curl -s http://$IMAC_IP:8000/health > /dev/null 2>&1; then
    echo "   ✅ Backend is accessible via IP: http://$IMAC_IP:8000"
else
    echo "   ❌ Backend is NOT accessible via IP: http://$IMAC_IP:8000"
    echo "      This might be a firewall issue!"
fi

if curl -s http://$IMAC_IP:3000 > /dev/null 2>&1; then
    echo "   ✅ Frontend is accessible via IP: http://$IMAC_IP:3000"
else
    echo "   ❌ Frontend is NOT accessible via IP: http://$IMAC_IP:3000"
    echo "      This might be a firewall issue!"
fi
echo ""

# 7. Check firewall status
echo "7. Checking macOS Firewall status..."
FIREWALL_STATUS=$(/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null | grep -i "enabled" || echo "unknown")
if echo "$FIREWALL_STATUS" | grep -qi "enabled"; then
    echo "   ⚠️  macOS Firewall is ENABLED"
    echo "      You may need to allow Docker/containers through the firewall"
    echo "      Go to: System Settings > Network > Firewall > Options"
    echo "      Add Docker Desktop or allow incoming connections"
else
    echo "   ✅ macOS Firewall is disabled or not blocking"
fi
echo ""

# 8. Check .env configuration
echo "8. Checking .env configuration..."
if [ -f .env ]; then
    if grep -q "API_BASE_URL=http://backend:8000" .env || grep -q "API_BASE_URL=http://localhost:8000" .env; then
        echo "   ⚠️  API_BASE_URL is set to localhost or backend"
        echo "      For network access, it should be: API_BASE_URL=http://$IMAC_IP:8000"
    elif grep -q "API_BASE_URL=http://$IMAC_IP:8000" .env; then
        echo "   ✅ API_BASE_URL is correctly set to iMac IP"
    else
        echo "   ⚠️  Could not verify API_BASE_URL configuration"
    fi
    
    if grep -q "VITE_API_BASE_URL=http://localhost:8000" .env; then
        echo "   ⚠️  VITE_API_BASE_URL is set to localhost"
        echo "      For network access, it should be: VITE_API_BASE_URL=http://$IMAC_IP:8000"
        echo "      Note: You'll need to rebuild after changing this: docker-compose up -d --build"
    elif grep -q "VITE_API_BASE_URL=http://$IMAC_IP:8000" .env; then
        echo "   ✅ VITE_API_BASE_URL is correctly set to iMac IP"
    else
        echo "   ⚠️  Could not verify VITE_API_BASE_URL configuration"
    fi
else
    echo "   ⚠️  .env file not found"
fi
echo ""

# 9. Summary and recommendations
echo "=========================================="
echo "SUMMARY & RECOMMENDATIONS"
echo "=========================================="
echo ""
echo "To access from another computer on the same network:"
echo ""
echo "1. Use this URL on the other computer:"
echo "   http://$IMAC_IP:3000"
echo ""
echo "2. If it doesn't work, check:"
echo "   a) macOS Firewall: System Settings > Network > Firewall"
echo "      - Allow Docker Desktop through firewall"
echo "      - Or temporarily disable firewall to test"
echo ""
echo "3. Update .env file if needed:"
echo "   API_BASE_URL=http://$IMAC_IP:8000"
echo "   VITE_API_BASE_URL=http://$IMAC_IP:8000"
echo "   Then rebuild: docker-compose up -d --build"
echo ""
echo "4. Verify both devices are on the same WiFi network"
echo ""
echo "5. Test from the other computer:"
echo "   ping $IMAC_IP"
echo "   curl http://$IMAC_IP:8000/health"
echo ""
