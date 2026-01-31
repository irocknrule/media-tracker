# Database Backup Guide

## Overview

This guide explains how to backup your Media Tracker database to cloud services like Microsoft OneDrive, Dropbox, Google Drive, or iCloud Drive.

## Why Backup?

- 💾 **Protect your data** - Never lose your media tracking history
- 🔄 **Easy recovery** - Restore from backup if something goes wrong
- ☁️ **Off-site storage** - Cloud backup protects against hardware failure
- 📱 **Access from anywhere** - View backups from any device

## Supported Cloud Services

✅ **Microsoft OneDrive**  
✅ **Dropbox**  
✅ **Google Drive**  
✅ **iCloud Drive**  
✅ **Any folder that syncs to cloud**

## Quick Setup

### Step 1: Choose Your Cloud Service

**OneDrive (Recommended for Mac):**
```bash
# Personal OneDrive (often here on Mac)
BACKUP_DIR="$HOME/OneDrive/MediaTracker-Backups"
# Or if OneDrive is under CloudStorage:
BACKUP_DIR="$HOME/Library/CloudStorage/OneDrive-Personal/MediaTracker-Backups"
```
You can set this in your project `.env` as `BACKUP_DIR=...` so the backup scripts use it without editing the script.

**Dropbox:**
```bash
BACKUP_DIR="$HOME/Dropbox/MediaTracker-Backups"
```

**Google Drive:**
```bash
BACKUP_DIR="$HOME/Google Drive/MediaTracker-Backups"
```

**iCloud Drive:**
```bash
BACKUP_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/MediaTracker-Backups"
```

### Step 2: Configure Backup Script

**For Docker deployment (recommended):**
```bash
# Edit the backup script
nano backup-db-docker.sh

# Update BACKUP_DIR to your preferred cloud service
BACKUP_DIR="$HOME/OneDrive/MediaTracker-Backups"
```

**For non-Docker deployment:**
```bash
# Edit the backup script
nano backup-db.sh

# Update BACKUP_DIR to your preferred cloud service
BACKUP_DIR="$HOME/OneDrive/MediaTracker-Backups"
```

### Step 3: Make Script Executable

```bash
chmod +x backup-db-docker.sh
# or
chmod +x backup-db.sh
```

### Step 4: Test Manual Backup

```bash
# For Docker
./backup-db-docker.sh

# For non-Docker
./backup-db.sh
```

You should see:
```
✅ Backup created successfully!
   File: media_tracker_20240115_143022.db
   Latest copy: ~/OneDrive/MediaTracker-Backups/media_tracker_latest.db
   Location: ~/OneDrive/MediaTracker-Backups
```

The scripts also write **media_tracker_latest.db** (overwritten each run) so your cloud folder always has one current copy for quick restore. To disable, set `KEEP_LATEST_COPY=0` when running the script.

## Automated Backups

### Option 1: macOS LaunchAgent (Recommended)

Create an automated backup that runs daily:

```bash
# Create the plist file
nano ~/Library/LaunchAgents/com.mediatracker.backup.plist
```

Add this content (adjust paths as needed):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mediatracker.backup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/zubair/media-tracker/backup-db-docker.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>RunAtLoad</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/mediatracker-backup.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/mediatracker-backup.error.log</string>
</dict>
</plist>
```

Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.mediatracker.backup.plist
```

This will backup daily at 2:00 AM.

### Option 2: Cron Job (Alternative)

```bash
# Edit crontab
crontab -e

# Add this line for daily backup at 2 AM
0 2 * * * /Users/zubair/media-tracker/backup-db-docker.sh >> /tmp/mediatracker-backup.log 2>&1
```

### Option 3: Docker Compose with Scheduled Task

You can also add a backup service to `docker-compose.yml`:

```yaml
services:
  # ... existing services ...
  
  backup:
    image: alpine:latest
    container_name: media-tracker-backup
    volumes:
      - ./data:/data:ro
      - $HOME/OneDrive/MediaTracker-Backups:/backups
    command: >
      sh -c "
        apk add --no-cache sqlite &&
        while true; do
          cp /data/media_tracker.db /backups/media_tracker_$(date +%Y%m%d_%H%M%S).db &&
          sleep 86400
        done
      "
    restart: unless-stopped
```

## Backup Management

### View Your Backups

```bash
# List all backups
ls -lh ~/OneDrive/MediaTracker-Backups/

# View backup details
ls -lht ~/OneDrive/MediaTracker-Backups/ | head -10
```

### Restore from Backup

**Method 1: Manual Restore**

```bash
# Stop the application
docker-compose down

# Copy backup to data directory
cp ~/OneDrive/MediaTracker-Backups/media_tracker_20240115_143022.db \
   ./data/media_tracker.db

# Start the application
docker-compose up -d
```

**Method 2: Using Restore Script**

Create `restore-db.sh`:
```bash
#!/bin/bash
BACKUP_FILE="$1"
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./restore-db.sh <backup-file>"
    exit 1
fi

docker-compose down
cp "$BACKUP_FILE" ./data/media_tracker.db
docker-compose up -d
echo "✅ Database restored from: $BACKUP_FILE"
```

Usage:
```bash
chmod +x restore-db.sh
./restore-db.sh ~/OneDrive/MediaTracker-Backups/media_tracker_20240115_143022.db
```

### Cleanup Old Backups

The backup scripts include optional cleanup code. To enable it, uncomment these lines:

```bash
# In backup-db-docker.sh or backup-db.sh
KEEP_BACKUPS=30  # Keep last 30 backups
echo "🧹 Cleaning old backups (keeping last $KEEP_BACKUPS)..."
cd "$BACKUP_DIR"
ls -t media_tracker_*.db | tail -n +$((KEEP_BACKUPS + 1)) | xargs rm -f
```

## Cloud Service Setup

### Microsoft OneDrive

1. **Install OneDrive** (if not already installed)
   - Download from: https://www.microsoft.com/microsoft-365/onedrive/download

2. **Set up sync folder**
   - OneDrive folder is typically: `~/OneDrive`
   - Create subfolder: `~/OneDrive/MediaTracker-Backups`

3. **Configure backup script:**
   ```bash
   BACKUP_DIR="$HOME/OneDrive/MediaTracker-Backups"
   ```

### Dropbox

1. **Install Dropbox** (if not already installed)
   - Download from: https://www.dropbox.com/downloading

2. **Set up sync folder**
   - Dropbox folder is typically: `~/Dropbox`
   - Create subfolder: `~/Dropbox/MediaTracker-Backups`

3. **Configure backup script:**
   ```bash
   BACKUP_DIR="$HOME/Dropbox/MediaTracker-Backups"
   ```

### Google Drive

1. **Install Google Drive for Desktop**
   - Download from: https://www.google.com/drive/download/

2. **Set up sync folder**
   - Google Drive folder is typically: `~/Google Drive`
   - Create subfolder: `~/Google Drive/MediaTracker-Backups`

3. **Configure backup script:**
   ```bash
   BACKUP_DIR="$HOME/Google Drive/MediaTracker-Backups"
   ```

### iCloud Drive

1. **Enable iCloud Drive**
   - System Preferences > Apple ID > iCloud > iCloud Drive

2. **Set up sync folder**
   - iCloud Drive path: `~/Library/Mobile Documents/com~apple~CloudDocs`
   - Create subfolder: `~/Library/Mobile Documents/com~apple~CloudDocs/MediaTracker-Backups`

3. **Configure backup script:**
   ```bash
   BACKUP_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/MediaTracker-Backups"
   ```

## Backup Frequency Recommendations

- **Daily backups** - Recommended for active use
- **Weekly backups** - Acceptable for light use
- **Before major changes** - Always backup before migrations or updates

## Verification

### Check Backup Integrity

The backup scripts automatically verify integrity if `sqlite3` is installed:

```bash
# Manual verification
sqlite3 ~/OneDrive/MediaTracker-Backups/media_tracker_20240115_143022.db "PRAGMA integrity_check;"
```

Should output: `ok`

### Test Restore

Periodically test restoring from a backup to ensure they work:

```bash
# Create a test restore
docker-compose down
cp ~/OneDrive/MediaTracker-Backups/media_tracker_20240115_143022.db \
   ./data/media_tracker.db.test

# Verify it works
sqlite3 ./data/media_tracker.db.test "SELECT COUNT(*) FROM movies;"

# Restore original
cp ./data/media_tracker.db ./data/media_tracker.db.test
docker-compose up -d
```

## Troubleshooting

### Backup Fails: "Directory not writable"

```bash
# Check permissions
ls -ld ~/OneDrive/MediaTracker-Backups

# Fix permissions
chmod 755 ~/OneDrive/MediaTracker-Backups
```

### Cloud Service Not Syncing

1. Check cloud service status
2. Verify folder is set to sync
3. Check available disk space
4. Restart cloud service app

### Container Not Found

If using Docker and container isn't running:
- The script will fallback to host volume backup
- Or start containers: `docker-compose up -d`

### Backup File Too Large

SQLite databases can grow large. Consider:
- Regular cleanup of old backups
- Compressing backups (add to script)
- Using cloud service with sufficient storage

## Best Practices

1. ✅ **Automate backups** - Set up daily automated backups
2. ✅ **Verify regularly** - Check backup integrity monthly
3. ✅ **Test restores** - Periodically test restoring from backup
4. ✅ **Multiple locations** - Consider backing up to multiple cloud services
5. ✅ **Version history** - Cloud services often provide version history
6. ✅ **Monitor storage** - Ensure cloud service has enough space

## Summary

✅ **Easy setup** - Configure backup directory to cloud service folder  
✅ **Automated** - Set up daily backups with LaunchAgent or cron  
✅ **Secure** - Data stored in your cloud account  
✅ **Accessible** - View backups from any device  
✅ **Reliable** - Automatic integrity checks  

Your media tracking data is now safely backed up to the cloud! ☁️

