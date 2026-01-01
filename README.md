# Personal Media Tracker

A secure local media tracking application to track Movies, TV Shows, Books, Music, and Daily Habits throughout the year with comprehensive analytics and year-over-year comparisons.

## Features

- **Media Tracking**: Track Movies, TV Shows, Books, and Music (albums, records, bands)
- **Daily Habit Tracker**: Log and track daily habits including:
  - Exercise (Workout, Yoga, Running, Biking) with metrics for minutes, distance, and elevation
  - Mindfulness (Meditation) with time tracking
  - Music Practice (Guitar, Drums) with practice time
- **Calendar Views**: Visualize habit completion with Monthly, Quarterly, and Yearly calendar views
- **Habit Analytics**: Comprehensive analytics with charts showing:
  - Total sessions, minutes, distances, and elevations
  - Daily activity trends
  - Habit type distributions
  - Time frame filters (Month, Quarter, Year, Custom)
- **Secure Access**: Password-protected authentication
- **Analytics**: Year-end summaries and year-over-year comparisons for media
- **Modern UI**: Streamlit frontend with intuitive forms and interactive charts
- **RESTful API**: FastAPI backend with comprehensive routes

## Architecture

- **Frontend**: Streamlit web interface
- **Backend**: FastAPI REST API
- **Database**: SQLite (local storage)
- **Authentication**: Session-based password protection

## Project Structure

```
media-tracker/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models.py            # Database models
│   ├── database.py          # Database setup
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── movies.py
│   │   ├── tv_shows.py
│   │   ├── books.py
│   │   ├── music.py
│   │   ├── habits.py
│   │   ├── analytics.py
│   │   └── auth.py
│   └── schemas.py           # Pydantic schemas
├── frontend/
│   └── app.py               # Streamlit application
├── migrate_add_habits.py    # Database migration for habit tracking
├── requirements.txt
└── README.md
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
python -m backend.database
```

   This will automatically run all migrations including the habit tracking tables. If you need to run the habit migration separately:
```bash
python migrate_add_habits.py
```

3. Set up API keys (optional but recommended):
   
   **OMDB API Key** (REQUIRED for movie search):
   - Get a free API key from: http://www.omdbapi.com/apikey.aspx
   - Set it as an environment variable before running the backend:
     ```bash
     # On macOS/Linux:
     export OMDB_API_KEY="your_api_key_here"
     
     # On Windows (PowerShell):
     $env:OMDB_API_KEY="your_api_key_here"
     
     # On Windows (Command Prompt):
     set OMDB_API_KEY=your_api_key_here
     ```
   - **Note**: Without this key, movie search will return empty results.
   
   **Last.fm API Key** (OPTIONAL - for better music search):
   - Get a free API key from: https://www.last.fm/api/account/create
   - Set it as an environment variable:
     ```bash
     export LASTFM_API_KEY="your_api_key_here"
     ```
   - If not set, a default demo key will be used (may have rate limits).
   
   **Note**: TV Shows and Books search work without API keys (they use free APIs: TVMaze and Open Library).

4. Run the backend (FastAPI):
```bash
uvicorn backend.main:app --reload
```

5. Run the frontend (Streamlit):
```bash
streamlit run frontend/app.py
```

## Usage

### Media Tracker
- Navigate to **Media Tracker** tab to track Movies, TV Shows, Books, and Music
- Use search functionality to find media items from external APIs
- Add ratings, notes, and custom thumbnails
- View analytics by year with visual summaries

### Habit Tracker
- Navigate to **Habit Tracker** tab to log daily habits
- **Log Habits**: Select a date and log your daily activities:
  - Exercise: Workout (minutes), Yoga (minutes), Running (distance/elevation), Biking (distance/elevation)
  - Mindfulness: Meditation (minutes)
  - Music Practice: Guitar (minutes), Drums (minutes)
- **Calendar**: View habit completion across different time periods:
  - Monthly view with habit icons on each day
  - Quarterly view showing 3 months side-by-side
  - Yearly view with all 12 months
- **Analytics**: View comprehensive statistics:
  - Total sessions, minutes, distances, and elevations
  - Breakdown by habit type with charts
  - Daily activity trends
  - Filter by time frame (This Month, This Quarter, This Year, Last Month, Last Quarter, Last Year, or Custom date range)
- **Delete Options**: 
  - Delete individual habit entries if entered by mistake
  - Delete all habits for a specific day

## Default Credentials

- Username: `admin`
- Password: `admin123` (change this in production!)

## Free Hosting Options

### Recommended for Personal Use:

1. **Render.com** (Free Tier)
   - Free PostgreSQL database
   - Free web services
   - Automatic SSL
   - Good for FastAPI + Streamlit

2. **Railway.app** (Free Tier)
   - $5 free credit monthly
   - Easy deployment
   - PostgreSQL included

3. **Fly.io** (Free Tier)
   - 3 shared VMs for free
   - Good for containerized apps

4. **PythonAnywhere** (Free Tier)
   - Free tier with limitations
   - Good for Streamlit apps

5. **Streamlit Cloud** (Free)
   - Direct Streamlit hosting
   - Free for public repos
   - Easy deployment

**Note**: For a truly personal app, you might also consider running it locally or on a Raspberry Pi for maximum privacy.

## Security Considerations

- Change default password in production
- Use environment variables for sensitive data
- Consider adding API key authentication for backend
- Enable HTTPS in production

