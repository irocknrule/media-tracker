#!/bin/bash

# Hostname (mDNS/Bonjour) troubleshooting for Media Tracker
# Run this on BOTH the Mac (server) and the other device (client) to find where resolution fails

echo "=========================================="
echo "Hostname Troubleshooting: Mohammads-Mac-mini.local"
echo "=========================================="
echo ""

HOSTNAME="Mohammads-Mac-mini.local"
API_PORT=8000
FRONTEND_PORT=3000

# --- On the Mac (server) ---
echo "=== PART 1: Mac running Docker (server) ==="
echo ""

echo "1. Hostname settings:"
echo "   ComputerName:  $(scutil --get ComputerName 2>/dev/null || echo 'N/A')"
echo "   LocalHostName: $(scutil --get LocalHostName 2>/dev/null || echo 'N/A')"
echo "   hostname:      $(hostname 2>/dev/null)"
echo "   Expected:      $HOSTNAME"
echo ""

echo "2. Does this Mac resolve its own hostname?"
if ping -c 1 -t 2 "$HOSTNAME" >/dev/null 2>&1; then
    echo "   ✅ ping $HOSTNAME works on this Mac"
    ping -c 1 "$HOSTNAME" | head -2
else
    echo "   ❌ ping $HOSTNAME FAILS on this Mac"
    echo "   → Fix: Ensure LocalHostName matches. Run: scutil --get LocalHostName"
    echo "   → Or try: sudo killall -HUP mDNSResponder"
fi
echo ""

echo "3. Is mDNS (Bonjour) running?"
if pgrep -x mDNSResponder >/dev/null; then
    echo "   ✅ mDNSResponder is running"
else
    echo "   ❌ mDNSResponder is not running (unusual on macOS)"
fi
echo ""

echo "4. Can this Mac reach the app via hostname?"
if curl -s -o /dev/null -w "%{http_code}" "http://$HOSTNAME:$API_PORT/health" 2>/dev/null | grep -q 200; then
    echo "   ✅ Backend: http://$HOSTNAME:$API_PORT/health returns 200"
else
    echo "   ❌ Backend not reachable at http://$HOSTNAME:$API_PORT/health"
fi
if curl -s -o /dev/null -w "%{http_code}" "http://$HOSTNAME:$FRONTEND_PORT" 2>/dev/null | grep -q 200; then
    echo "   ✅ Frontend: http://$HOSTNAME:$FRONTEND_PORT returns 200"
else
    echo "   ❌ Frontend not reachable at http://$HOSTNAME:$FRONTEND_PORT"
fi
echo ""

# --- On the other device (client) ---
echo "=== PART 2: Other device (client) - run these there ==="
echo ""
echo "On the OTHER computer/phone, run these and note results:"
echo ""
echo "  A) Resolve hostname to IP:"
echo "     ping -c 1 $HOSTNAME"
echo "     (Linux/Mac). On Windows: ping $HOSTNAME"
echo ""
echo "  B) If ping fails:"
echo "     - Windows: .local often needs 'Bonjour Print Services' or similar"
echo "     - Android: .local often does NOT work; use IP or an mDNS app"
echo "     - Linux: install avahi-daemon and avahi-utils"
echo ""
echo "  C) If ping works, test API:"
echo "     curl http://$HOSTNAME:$API_PORT/health"
echo ""
echo "  D) Then open in browser:"
echo "     http://$HOSTNAME:$FRONTEND_PORT"
echo ""
echo "=========================================="
echo "Common causes of hostname failure:"
echo "  • Other device doesn't support mDNS (.local)"
echo "  • Different subnet / VLAN (mDNS doesn't cross routers)"
echo "  • Firewall blocking mDNS (UDP port 5353)"
echo "  • LocalHostName has spaces/special chars (use only letters, numbers, hyphens)"
echo "=========================================="
