# Deployment Guide - Docker on iMac

This guide explains how to containerize and deploy the Media Tracker application on your iMac using Docker.

## Prerequisites

1. **Docker Desktop** installed on your iMac
   - Download from: https://www.docker.com/products/docker-desktop
   - Ensure it's running before proceeding

2. **Find your iMac's IP address** (for network access)
   ```bash
   # On macOS:
   ipconfig getifaddr en0
   # Or check in System Preferences > Network
   ```

## Quick Start

### 1. Prepare the Environment

```bash
# Navigate to the project directory
cd /path/to/media-tracker

# Copy the example environment file
cp .env.example .env

# Edit .env file with your API keys (optional but recommended)
nano .env  # or use your preferred editor
```

### 2. Migrate Existing Database (if applicable)

If you have an existing `media_tracker.db` file:

```bash
# Create data directory
mkdir -p data

# Copy your existing database
cp media_tracker.db data/media_tracker.db
```

### 3. Build and Start Containers

```bash
# Build and start both services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Access the Application

- **From the iMac**: http://localhost:8501
- **From other devices on same WiFi**: http://<your-imac-ip>:8501
  - Example: http://192.168.1.100:8501

## Multi-Device Access

**Yes! You can access and input data from ANY device on your WiFi network.**

### How It Works

Once the app is running on the iMac:
- ✅ **All devices share the same database** (stored on iMac)
- ✅ **Any device can add/edit data** - changes sync immediately
- ✅ **Web-based interface** - works on any device with a browser
- ✅ **No special software needed** - just open a web browser

### Supported Devices

You can access from:
- ✅ **Mac Mini** - Open browser to `http://<imac-ip>:8501`
- ✅ **iPad** - Open Safari to `http://<imac-ip>:8501`
- ✅ **iPhone** - Open Safari to `http://<imac-ip>:8501`
- ✅ **Any laptop/computer** on the same WiFi
- ✅ **Any tablet or device** with a web browser

### Example Setup

1. **iMac running the app**: `192.168.1.100`
2. **Mac Mini accesses**: `http://192.168.1.100:8501`
3. **iPad accesses**: `http://192.168.1.100:8501`
4. **All devices see the same data** - add a movie on iPad, see it on Mac Mini instantly

### Important Notes

- 🔒 **All devices use the same login** (username/password)
- 💾 **Data is stored on iMac** - all devices read/write to the same database
- 🌐 **Must be on same WiFi network** - devices need to be on the same local network
- ⚡ **Real-time sync** - changes appear immediately on all devices
- 🔐 **Single source of truth** - database lives on iMac only

## Configuration for Network Access

To access from iPad/iPhone on the same WiFi network:

### Option 1: Update .env file (Recommended)

Edit `.env` file and set:
```bash
API_BASE_URL=http://<your-imac-ip>:8000
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

### Option 2: Use environment variable at runtime

```bash
API_BASE_URL=http://<your-imac-ip>:8000 docker-compose up -d
```

**Important**: Replace `<your-imac-ip>` with your actual iMac IP address (e.g., `192.168.1.100`)

## Managing the Application

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop Services
```bash
docker-compose down
```

### Start Services
```bash
docker-compose up -d
```

### Restart Services
```bash
docker-compose restart
```

### Rebuild After Code Changes
```bash
docker-compose up -d --build
```

### Check Service Status
```bash
docker-compose ps
```

## Database Management

### Backup Database
```bash
# The database is stored in ./data/media_tracker.db
# Simply copy this file to backup
cp data/media_tracker.db data/media_tracker.db.backup
```

### Restore Database
```bash
# Stop services first
docker-compose down

# Replace database file
cp your_backup.db data/media_tracker.db

# Start services
docker-compose up -d
```

### Initialize New Database
```bash
# Stop services
docker-compose down

# Remove existing database
rm data/media_tracker.db

# Start services (database will be auto-initialized)
docker-compose up -d

# Run initialization
docker-compose exec backend python -m backend.database
```

## Moving to Another iMac

### Method 1: Using Git (Recommended)

1. **On current machine:**
   ```bash
   # Commit your code (excluding database)
   git add .
   git commit -m "Add Docker configuration"
   git push
   ```

2. **On new iMac:**
   ```bash
   # Clone repository
   git clone <your-repo-url>
   cd media-tracker
   
   # Copy database if needed
   # (transfer media_tracker.db separately via USB/network)
   
   # Set up environment
   cp .env.example .env
   # Edit .env with your settings
   
   # Start services
   docker-compose up -d
   ```

### Method 2: Direct Transfer

1. **Transfer project directory:**
   ```bash
   # On current machine, create archive (excluding large files)
   tar -czf media-tracker.tar.gz \
     --exclude='__pycache__' \
     --exclude='*.pyc' \
     --exclude='.git' \
     --exclude='data' \
     media-tracker/
   
   # Transfer to new iMac (via USB, network share, etc.)
   ```

2. **Transfer database separately:**
   ```bash
   # Copy database file
   scp media_tracker.db user@new-imac:/path/to/media-tracker/data/
   ```

3. **On new iMac:**
   ```bash
   cd /path/to/media-tracker
   cp .env.example .env
   # Edit .env file
   docker-compose up -d
   ```

## Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker ps

# Check logs for errors
docker-compose logs

# Rebuild containers
docker-compose up -d --build
```

### Can't access from other devices
1. Check firewall settings on iMac
2. Verify IP address is correct
3. Ensure both devices are on same WiFi network
4. Check `API_BASE_URL` in `.env` matches your iMac's IP

### Database issues
```bash
# Check database file permissions
ls -la data/media_tracker.db

# Ensure data directory exists
mkdir -p data
```

### Port already in use
```bash
# Check what's using the ports
lsof -i :8000
lsof -i :8501

# Change ports in docker-compose.yml if needed
```

## Auto-start on Boot (Optional)

To automatically start the application when iMac boots:

1. **Create a launchd plist file:**
   ```bash
   sudo nano /Library/LaunchDaemons/com.mediatracker.docker.plist
   ```

2. **Add this content:**
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.mediatracker.docker</string>
       <key>ProgramArguments</key>
       <array>
           <string>/usr/local/bin/docker-compose</string>
           <string>-f</string>
           <string>/path/to/media-tracker/docker-compose.yml</string>
           <string>up</string>
           <string>-d</string>
       </array>
       <key>RunAtLoad</key>
       <true/>
       <key>KeepAlive</key>
       <true/>
       <key>WorkingDirectory</key>
       <string>/path/to/media-tracker</string>
   </dict>
   </plist>
   ```

3. **Load the service:**
   ```bash
   sudo launchctl load /Library/LaunchDaemons/com.mediatracker.docker.plist
   ```

## Security Notes

- Change default password in production
- Consider using a reverse proxy (nginx) with SSL for HTTPS
- Restrict CORS origins in production (currently set to `*`)
- Keep Docker and dependencies updated
- Regularly backup your database

## Performance Tips

- The application is lightweight and should run smoothly on any modern iMac
- Monitor resource usage: `docker stats`
- Database is stored in `./data/` directory - ensure adequate disk space
- Consider using an external drive for database if storage is a concern

