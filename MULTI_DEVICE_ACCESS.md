# Multi-Device Access Guide

## Overview

When you host the Media Tracker on your iMac, **you can access it from ANY device on your WiFi network** - Mac Mini, iPad, iPhone, or any other device with a web browser.

## How It Works

```
┌─────────────┐
│   iMac      │  ← App runs here (Docker containers)
│  (Server)   │  ← Database stored here
└──────┬──────┘
       │
       │ WiFi Network
       │
   ┌───┴────┬──────────┬──────────┐
   │        │          │          │
┌──▼──┐ ┌──▼──┐   ┌───▼───┐  ┌───▼───┐
│Mac  │ │iPad │   │iPhone │  │Laptop │
│Mini │ │     │   │       │  │       │
└─────┘ └─────┘   └───────┘  └───────┘
  All access: http://<imac-ip>:8501
```

## Key Points

### ✅ Shared Database
- **Single database** stored on iMac
- **All devices** read from and write to the same database
- **Real-time sync** - changes appear immediately on all devices

### ✅ Any Device Can Input Data
- Add movies from iPad ✅
- Add books from Mac Mini ✅
- Track habits from iPhone ✅
- View analytics from any device ✅

### ✅ No Special Software Needed
- Just a web browser (Safari, Chrome, Firefox, etc.)
- No apps to install
- Works on any device with internet access

## Setup Instructions

### Step 1: Find Your iMac's IP Address

On the iMac, run:
```bash
ipconfig getifaddr en0
```

Example output: `192.168.1.100`

### Step 2: Configure for Network Access

Edit `.env` file on iMac:
```bash
API_BASE_URL=http://192.168.1.100:8000
```

Replace `192.168.1.100` with your actual iMac IP address.

### Step 3: Start the Application

```bash
docker-compose up -d
```

### Step 4: Access from Any Device

**From Mac Mini:**
1. Open any web browser
2. Go to: `http://192.168.1.100:8501`
3. Login with your credentials
4. Start using the app!

**From iPad/iPhone:**
1. Open Safari (or any browser)
2. Type in address bar: `http://192.168.1.100:8501`
3. Login with your credentials
4. Use the app normally

**From Any Other Device:**
- Same process - just use the iMac's IP address

## Example Use Cases

### Scenario 1: Adding Media from Different Devices

1. **Morning on iPad**: Add a book you finished reading
2. **Afternoon on Mac Mini**: Add a movie you watched
3. **Evening on iPhone**: Add a TV show episode
4. **All data appears on all devices** - everything is synced!

### Scenario 2: Viewing Analytics

1. **On iMac**: View year-end analytics
2. **On iPad**: Check your reading progress
3. **On Mac Mini**: Compare this year vs last year
4. **Same data everywhere**

### Scenario 3: Habit Tracking

1. **Morning on iPhone**: Log your workout
2. **Evening on iPad**: Log meditation session
3. **Weekend on Mac Mini**: Review weekly habit calendar
4. **All entries in one place**

## Security & Access

### Login Credentials
- **Same login for all devices** - use your username/password
- **Session-based** - you'll need to login on each device
- **Secure** - password-protected access

### Network Requirements
- ✅ **Same WiFi network** - all devices must be on the same local network
- ✅ **iMac must be running** - the app needs to be running on iMac
- ✅ **Firewall** - ensure ports 8000 and 8501 are open on iMac

### Data Storage
- 💾 **Database on iMac only** - all data is stored on the iMac
- 🔄 **No local copies** - devices don't store data locally
- ✅ **Backup on iMac** - backup the database on the iMac

## Troubleshooting

### Can't Access from Other Devices

1. **Check iMac IP address:**
   ```bash
   ipconfig getifaddr en0
   ```

2. **Verify .env configuration:**
   ```bash
   cat .env | grep API_BASE_URL
   ```
   Should show: `API_BASE_URL=http://<your-imac-ip>:8000`

3. **Check firewall:**
   - System Preferences > Security & Privacy > Firewall
   - Ensure Docker/containers are allowed

4. **Verify same network:**
   - All devices must be on the same WiFi network
   - Check WiFi network name matches

5. **Test connectivity:**
   ```bash
   # From Mac Mini, test if iMac is reachable
   ping <imac-ip>
   
   # Test if port is open
   curl http://<imac-ip>:8501
   ```

### Changes Not Appearing

- **Refresh the browser** - sometimes browser cache needs refresh
- **Check if app is running:**
  ```bash
  docker-compose ps
  ```
- **Check logs for errors:**
  ```bash
  docker-compose logs -f
  ```

## Best Practices

1. **Bookmark the URL** on each device for easy access
2. **Use consistent login** - same credentials everywhere
3. **Regular backups** - backup the database on iMac regularly
4. **Static IP** - consider setting a static IP for iMac (optional)
5. **Network name** - note your WiFi network name for troubleshooting

## FAQ

**Q: Can I access from outside my home network?**
A: Not by default. The current setup is for local network only. For external access, you'd need to set up port forwarding or use a VPN (not covered in this guide).

**Q: What if iMac goes to sleep?**
A: The app will be unavailable. Configure iMac to not sleep, or use "Prevent automatic sleeping" in Energy Saver settings.

**Q: Can multiple people use it at the same time?**
A: Yes! Multiple devices can access simultaneously. The database handles concurrent access.

**Q: Will my data be safe?**
A: Yes, data is stored locally on your iMac. It's not sent to any external servers (except for media search APIs like OMDB).

**Q: What if I lose my iMac IP address?**
A: You can always find it again with `ipconfig getifaddr en0` on the iMac. Consider setting a static IP address for reliability.

## Summary

✅ **One app on iMac** → Accessible from all devices  
✅ **One shared database** → All devices see the same data  
✅ **Any device can input** → Add data from anywhere  
✅ **Real-time sync** → Changes appear immediately  
✅ **No special software** → Just a web browser needed  

Enjoy using your Media Tracker from any device! 🎉

