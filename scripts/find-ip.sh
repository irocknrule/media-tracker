#!/bin/bash

# Script to find your Mac's IP address for network access

echo "Finding your Mac's IP address..."
echo ""

# Method 1: Try different network interfaces
echo "Method 1: Checking common network interfaces..."
for interface in en0 en1 en2; do
    IP=$(ipconfig getifaddr $interface 2>/dev/null)
    if [ -n "$IP" ]; then
        echo "  ✅ Found IP on $interface: $IP"
        FOUND_IP=$IP
    fi
done

# Method 2: Use networksetup (macOS specific)
echo ""
echo "Method 2: Using networksetup..."
ACTIVE_SERVICE=$(networksetup -listallnetworkservices | grep -v "^An asterisk" | grep "^\*" | sed 's/^*//' | head -1)
if [ -n "$ACTIVE_SERVICE" ]; then
    echo "  Active network service: $ACTIVE_SERVICE"
    IP=$(networksetup -getinfo "$ACTIVE_SERVICE" | grep "IP address" | awk '{print $3}')
    if [ -n "$IP" ]; then
        echo "  ✅ Found IP: $IP"
        FOUND_IP=$IP
    fi
fi

# Method 3: Use route command
echo ""
echo "Method 3: Using route command..."
ROUTE_IP=$(route get default 2>/dev/null | grep interface | awk '{print $2}' | xargs -I {} ipconfig getifaddr {} 2>/dev/null)
if [ -n "$ROUTE_IP" ]; then
    echo "  ✅ Found IP via default route: $ROUTE_IP"
    FOUND_IP=$ROUTE_IP
fi

# Method 4: Check System Preferences style
echo ""
echo "Method 4: Checking all network interfaces..."
ifconfig | grep -E "^[a-z]|inet " | grep -B1 "inet " | grep -v "127.0.0.1" | grep "inet " | awk '{print $2}' | head -1 | while read ip; do
    if [ -n "$ip" ]; then
        echo "  ✅ Found IP: $ip"
        FOUND_IP=$ip
    fi
done

# Method 5: Use scutil
echo ""
echo "Method 5: Using scutil..."
SCUTIL_IP=$(scutil --nwi | grep "addresses" | head -1 | awk '{print $NF}')
if [ -n "$SCUTIL_IP" ]; then
    echo "  ✅ Found IP via scutil: $SCUTIL_IP"
    FOUND_IP=$SCUTIL_IP
fi

echo ""
echo "=========================================="
if [ -n "$FOUND_IP" ]; then
    echo "✅ Your Mac's IP address is: $FOUND_IP"
    echo ""
    echo "To use this IP, update your .env file:"
    echo "  API_BASE_URL=http://$FOUND_IP:8000"
    echo "  VITE_API_BASE_URL=http://$FOUND_IP:8000"
    echo ""
    echo "Then rebuild: docker-compose up -d --build"
else
    echo "❌ Could not automatically find IP address"
    echo ""
    echo "Please try one of these methods manually:"
    echo ""
    echo "1. System Settings > Network > [Your Connection] > Details"
    echo "   Look for 'IP Address'"
    echo ""
    echo "2. Terminal: ifconfig | grep 'inet ' | grep -v 127.0.0.1"
    echo ""
    echo "3. Terminal: networksetup -getinfo 'Wi-Fi'"
    echo "   (Replace 'Wi-Fi' with your connection name)"
fi
echo "=========================================="
