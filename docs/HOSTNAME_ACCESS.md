# Hostname-Based Access from Other Devices

This guide explains how to set up your Media Tracker app running in Docker to be accessible via a hostname (like `mediatracker.local`) from other devices on your local network.

## Overview

Instead of accessing your app via IP addresses (e.g., `http://192.168.1.100:3000`), you can use a hostname (e.g., `http://mediatracker.local:3000`). This is more convenient and works even if your IP address changes.

## Prerequisites

1. Docker and Docker Compose installed and running
2. All devices on the same local network (same WiFi)
3. macOS host (for mDNS/Bonjour - the easiest option)

## Step 1: Set Up Hostname on macOS

macOS uses mDNS (Bonjour) which automatically makes your Mac discoverable via hostname. By default, your Mac's hostname is typically `yourcomputername.local`.

### Find Your Current Hostname

```bash
# Check your current hostname
scutil --get ComputerName

# Check your local hostname (used for .local access)
scutil --get LocalHostName

# Check what other devices will see
hostname
```

The hostname will be something like `MacBook-Pro.local` or `zubairs-mac.local`.

### Set a Custom Hostname (Optional)

If you want a custom hostname like `mediatracker.local`:

1. **System Settings**:
   - Open **System Settings** > **General** > **Sharing**
   - Change **Computer Name** to `mediatracker` (or your preferred name)
   - The hostname will become `mediatracker.local`

2. **Or via Terminal**:
   ```bash
   # Set computer name (requires admin password)
   sudo scutil --set ComputerName "mediatracker"
   sudo scutil --set LocalHostName "mediatracker"
   sudo scutil --set HostName "mediatracker"
   
   # Restart mDNS responder to apply changes
   sudo killall -HUP mDNSResponder
   ```

### Verify Hostname Resolution

On the Mac running Docker:
```bash
# Test that your hostname resolves
ping -c 1 $(hostname).local

# Get the IP address
hostname -I
```

## Step 2: Configure Docker for Hostname Access

### Option A: Using Environment Variables (Recommended)

1. **Create or update `.env` file** in the project root:
   ```bash
   # Get your hostname (run this command to find it)
   # hostname
   
   # Set API_BASE_URL to use your hostname
   API_BASE_URL=http://mediatracker.local:8000
   
   # Set VITE_API_BASE_URL for React frontend build
   VITE_API_BASE_URL=http://mediatracker.local:8000
   ```

   **Important**: Replace `mediatracker.local` with your actual hostname (e.g., `MacBook-Pro.local` or whatever `hostname` returns with `.local` appended).

2. **Update `docker-compose.yml`** (already configured, but verify):

   The `docker-compose.yml` already uses environment variables. Make sure it looks like this:

   ```yaml
   frontend-react:
     build:
       context: ./frontend-react
       dockerfile: Dockerfile
       args:
         - VITE_API_BASE_URL=${VITE_API_BASE_URL:-http://localhost:8000}
   ```

### Option B: Manual Configuration

If you prefer to hardcode the hostname:

1. **Update `docker-compose.yml`**:
   ```yaml
   frontend-react:
     build:
       context: ./frontend-react
       dockerfile: Dockerfile
       args:
         - VITE_API_BASE_URL=http://mediatracker.local:8000  # Replace with your hostname
   ```

## Step 3: Rebuild and Start Containers

After updating configuration:

```bash
# Stop existing containers
docker-compose down

# Rebuild containers with new configuration
docker-compose up -d --build

# Check logs to verify everything started correctly
docker-compose logs -f
```

## Step 4: Configure Other Devices

### iOS/iPadOS (iPhone/iPad)

iOS devices automatically resolve `.local` hostnames via mDNS, so no configuration is needed!

Just access:
- `http://mediatracker.local:3000` (React frontend)
- `http://mediatracker.local:8501` (Streamlit frontend)

### Android

Android doesn't natively support mDNS/Bonjour. You have two options:

1. **Use IP Address** (simpler):
   - Find the Mac's IP: `ipconfig getifaddr en0` on the Mac
   - Access via: `http://192.168.1.100:3000` (replace with actual IP)

2. **Install mDNS Browser App**:
   - Install an mDNS browser app from Play Store
   - Or use a DNS app that supports `.local` resolution

### Windows

Windows 10+ supports mDNS, but may need configuration:

1. **Enable mDNS**:
   - Windows should resolve `.local` hostnames automatically
   - If it doesn't work, install **Bonjour Print Services** from Apple

2. **Or add to hosts file** (alternative):
   ```powershell
   # Open Notepad as Administrator
   # Edit C:\Windows\System32\drivers\etc\hosts
   # Add line:
   192.168.1.100 mediatracker.local
   ```

### Linux

Most Linux distributions support mDNS via `avahi-daemon`:

```bash
# Install avahi-daemon (if not already installed)
sudo apt-get install avahi-daemon  # Ubuntu/Debian
# or
sudo yum install avahi-daemon      # CentOS/RHEL

# Enable and start service
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon
```

After installation, `.local` hostnames should resolve automatically.

## Step 5: Access the Application

Once everything is configured:

### From the Mac running Docker:
- React Frontend: `http://localhost:3000` or `http://mediatracker.local:3000`
- Streamlit Frontend: `http://localhost:8501` or `http://mediatracker.local:8501`

### From Other Devices:
- React Frontend: `http://mediatracker.local:3000`
- Streamlit Frontend: `http://mediatracker.local:8501`

**Replace `mediatracker.local` with your actual hostname!**

## Troubleshooting

### Hostname doesn't resolve on other devices

1. **Verify mDNS is working on Mac**:
   ```bash
   # Check mDNSResponder is running
   ps aux | grep mDNSResponder
   
   # Restart mDNS if needed
   sudo killall -HUP mDNSResponder
   ```

2. **Check firewall settings**:
   - macOS: **System Settings** > **Network** > **Firewall**
   - Make sure incoming connections are allowed for ports 3000, 8000, and 8501

3. **Verify devices are on same network**:
   ```bash
   # On Mac, check network interface
   ipconfig getifaddr en0
   
   # On other device, ping the Mac's IP
   ping 192.168.1.100  # Replace with actual IP
   ```

### Frontend can't connect to backend

1. **Check API_BASE_URL is correct**:
   ```bash
   # Verify environment variable is set
   docker-compose exec frontend-react env | grep VITE_API_BASE_URL
   ```

2. **Check backend is accessible**:
   ```bash
   # Test backend directly
   curl http://mediatracker.local:8000/health
   ```

3. **Rebuild frontend with correct API URL**:
   ```bash
   docker-compose down
   # Update .env or docker-compose.yml
   docker-compose up -d --build
   ```

### Ports are not accessible

1. **Check ports are exposed**:
   ```bash
   docker-compose ps
   # Should show ports mapped (e.g., 0.0.0.0:3000->80/tcp)
   ```

2. **Check if ports are already in use**:
   ```bash
   lsof -i :3000
   lsof -i :8000
   lsof -i :8501
   ```

3. **Verify Docker is binding to all interfaces**:
   - Ports in `docker-compose.yml` should be `"3000:80"` (not `"127.0.0.1:3000:80"`)

## Dynamic Hostname Script

If your Mac's hostname might change, you can create a script to automatically update the configuration:

```bash
#!/bin/bash
# update-hostname.sh

# Get current hostname
HOSTNAME=$(hostname)
FULL_HOSTNAME="${HOSTNAME}.local"

# Update .env file
sed -i '' "s|API_BASE_URL=.*|API_BASE_URL=http://${FULL_HOSTNAME}:8000|" .env
sed -i '' "s|VITE_API_BASE_URL=.*|VITE_API_BASE_URL=http://${FULL_HOSTNAME}:8000|" .env

echo "Updated configuration to use hostname: ${FULL_HOSTNAME}"
echo "Rebuilding containers..."
docker-compose down
docker-compose up -d --build
```

Make it executable and run before starting containers:
```bash
chmod +x update-hostname.sh
./update-hostname.sh
```

## Security Notes

- Access is limited to your local network (not exposed to internet)
- No SSL/HTTPS by default (for local network use)
- Consider setting up a reverse proxy with SSL if needed
- Keep default admin password secure or change it

## Summary

1. ✅ Set up hostname on macOS (usually automatic)
2. ✅ Update `.env` with `API_BASE_URL=http://yourhostname.local:8000`
3. ✅ Update `.env` with `VITE_API_BASE_URL=http://yourhostname.local:8000`
4. ✅ Rebuild containers: `docker-compose up -d --build`
5. ✅ Access from other devices: `http://yourhostname.local:3000`

Your app will now be accessible via hostname from any device on your local network!
