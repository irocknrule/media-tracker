#!/bin/bash

# Database Backup Script for Media Tracker
# This script backs up the database to a cloud service (OneDrive, Dropbox, etc.)

set -e

# Configuration - set BACKUP_DIR in .env or export (e.g. your OneDrive folder)
BACKUP_DIR="${BACKUP_DIR:-$HOME/OneDrive/MediaTracker-Backups}"
# Alternative cloud services:
# BACKUP_DIR="$HOME/Library/CloudStorage/OneDrive-Personal/MediaTracker-Backups"
# BACKUP_DIR="$HOME/Dropbox/MediaTracker-Backups"
# BACKUP_DIR="$HOME/Google Drive/MediaTracker-Backups"
# Also keep a single "latest" copy (overwritten each run) for easy restore. Set to 0 to disable.
KEEP_LATEST_COPY="${KEEP_LATEST_COPY:-1}"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_SOURCE="$PROJECT_DIR/data/media_tracker.db"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILENAME="media_tracker_${TIMESTAMP}.db"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILENAME"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔄 Starting database backup..."
echo ""

# Check if database exists
if [ ! -f "$DB_SOURCE" ]; then
    echo -e "${RED}❌ Database file not found: $DB_SOURCE${NC}"
    echo "   Make sure the application has been run at least once."
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if backup directory is writable
if [ ! -w "$BACKUP_DIR" ]; then
    echo -e "${RED}❌ Backup directory is not writable: $BACKUP_DIR${NC}"
    exit 1
fi

# Create backup
echo "📋 Source: $DB_SOURCE"
echo "💾 Destination: $BACKUP_PATH"
echo ""

# Copy database file
cp "$DB_SOURCE" "$BACKUP_PATH"

if [ $? -eq 0 ]; then
    # Optionally keep a single "latest" copy (overwritten each run) so cloud always has current DB
    [ "$KEEP_LATEST_COPY" = "1" ] && cp "$DB_SOURCE" "$BACKUP_DIR/media_tracker_latest.db"
    # Get file size
    FILE_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
    echo -e "${GREEN}✅ Backup created successfully!${NC}"
    echo "   File: $BACKUP_FILENAME"
    echo "   Size: $FILE_SIZE"
    echo "   Location: $BACKUP_DIR"
    echo ""
    
    # Optional: Keep only last N backups (uncomment to enable)
    # KEEP_BACKUPS=30
    # echo "🧹 Cleaning old backups (keeping last $KEEP_BACKUPS)..."
    # cd "$BACKUP_DIR"
    # ls -t media_tracker_*.db | tail -n +$((KEEP_BACKUPS + 1)) | xargs rm -f
    # echo "✅ Cleanup complete"
    
    # Optional: Verify backup integrity
    if command -v sqlite3 &> /dev/null; then
        echo "🔍 Verifying backup integrity..."
        if sqlite3 "$BACKUP_PATH" "PRAGMA integrity_check;" | grep -q "ok"; then
            echo -e "${GREEN}✅ Backup integrity verified${NC}"
        else
            echo -e "${YELLOW}⚠️  Backup integrity check failed${NC}"
        fi
    fi
    
    [ "$KEEP_LATEST_COPY" = "1" ] && echo "   Latest copy: $BACKUP_DIR/media_tracker_latest.db"
    echo ""
    echo -e "${GREEN}✨ Backup complete!${NC}"
    echo "   Your database is now backed up to: $BACKUP_DIR"
    echo "   The cloud service will sync this automatically."
else
    echo -e "${RED}❌ Backup failed!${NC}"
    exit 1
fi

