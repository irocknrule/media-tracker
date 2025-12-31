# Personal Media Tracker

A secure local media tracking application to track Movies, TV Shows, Books, and Music throughout the year with year-end analytics and year-over-year comparisons.

## Features

- **Media Tracking**: Track Movies, TV Shows, Books, and Music (albums, records, bands)
- **Secure Access**: Password-protected authentication
- **Analytics**: Year-end summaries and year-over-year comparisons
- **Modern UI**: Streamlit frontend with intuitive forms
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
│   │   ├── analytics.py
│   │   └── auth.py
│   └── schemas.py           # Pydantic schemas
├── frontend/
│   └── app.py               # Streamlit application
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

3. Run the backend (FastAPI):
```bash
uvicorn backend.main:app --reload
```

4. Run the frontend (Streamlit):
```bash
streamlit run frontend/app.py
```

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

