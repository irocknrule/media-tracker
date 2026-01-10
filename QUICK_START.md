# Quick Start - Docker Deployment

## On Your Current Machine

1. **Copy environment template:**
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` file** with your API keys (optional):
   ```bash
   nano .env
   ```

3. **Prepare database directory:**
   ```bash
   mkdir -p data
   # If you have existing database:
   cp media_tracker.db data/media_tracker.db
   ```

## Transfer to iMac

### Option 1: Using Git (Recommended)
```bash
git add .
git commit -m "Add Docker configuration"
git push

# On iMac:
git clone <your-repo-url>
cd media-tracker
```

### Option 2: Direct Transfer
- Copy entire `media-tracker` folder to iMac (via USB, network share, etc.)
- Don't forget to transfer `media_tracker.db` if you have existing data

## On the iMac

1. **Install Docker Desktop** (if not already installed)
   - https://www.docker.com/products/docker-desktop

2. **Set up environment:**
   ```bash
   cd /path/to/media-tracker
   cp env.example .env
   nano .env  # Add your API keys if needed
   ```

3. **For network access from iPad/iPhone:**
   
   Find your iMac's IP address:
   ```bash
   ipconfig getifaddr en0
   ```
   
   Edit `.env` and set:
   ```bash
   API_BASE_URL=http://<your-imac-ip>:8000
   ```
   Example: `API_BASE_URL=http://192.168.1.100:8000`

4. **Start the application:**
   ```bash
   docker-compose up -d
   ```

5. **Access the app:**
   - From iMac: http://localhost:8501
   - From iPad/iPhone: http://<your-imac-ip>:8501

## Useful Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Rebuild after code changes
docker-compose up -d --build
```

See `DEPLOYMENT.md` for detailed instructions.

