# TV Shows Structure Migration Guide

## Overview

The TV shows feature has been enhanced to provide a **Plex-like experience** with separate management of show-level and season-level data, including distinct posters for both the overall show and individual seasons.

## What's New

### Database Structure Changes

#### Old Structure (Single Table)
- One `tv_shows` table containing all data
- Each row represented a single season
- Show metadata was duplicated across seasons

#### New Structure (Two Tables)
1. **`tv_shows` table** - Show-level data:
   - `id` - Unique show identifier
   - `title` - Show title
   - `year` - Overall show year
   - `genres` - Comma-separated genres
   - `overall_rating` - Overall show rating (0-10)
   - `show_thumbnail_url` - Main show poster
   - `created_at` - Creation timestamp

2. **`tv_show_seasons` table** - Season-level data:
   - `id` - Unique season identifier
   - `show_id` - Foreign key to show
   - `season_number` - Season number
   - `watched_date` - When you watched it
   - `rating` - Season-specific rating (0-10)
   - `notes` - Season-specific notes
   - `season_thumbnail_url` - Season-specific poster
   - `created_at` - Creation timestamp

### Key Benefits

✅ **Separate Posters**: Upload distinct posters for the show and each season  
✅ **Better Organization**: Show metadata (year, genres, overall rating) stored once  
✅ **Plex-Style Display**: Seasons grouped by year with individual posters  
✅ **Flexible Management**: Add/delete individual seasons without affecting the show  
✅ **Backward Compatibility**: Legacy endpoint maintains old API behavior

## Migration Steps

### 1. Backup Your Database

**IMPORTANT**: Always backup your database before migration!

```bash
cp media_tracker.db media_tracker.db.backup
```

### 2. Run the Migration Script

```bash
cd /Users/zubair/media-tracker
python migrate_tv_shows_structure.py
```

#### What the Migration Does:

1. Creates new table structure (`tv_shows_new` and `tv_show_seasons`)
2. Groups existing entries by show title
3. Creates one show entry per unique title
4. Migrates each season to the new `tv_show_seasons` table
5. Preserves all existing data (thumbnails, ratings, notes, dates)
6. Renames old table to `tv_shows_old` (for backup)
7. Renames new table to `tv_shows`

### 3. Verify Migration

After migration:
- Check that all shows appear correctly
- Verify season data is intact
- Test adding new shows/seasons

### 4. Clean Up (Optional)

Once you've verified everything works:

```bash
sqlite3 media_tracker.db "DROP TABLE tv_shows_old;"
```

## Using the New System

### Manual Entry (Recommended for Full Control)

Navigate to **Manual Entry → TV Show**:

1. **Show Information Section**:
   - Enter show title, year, genres
   - Set overall show rating
   - Upload main show poster

2. **Season Details Section**:
   - Enter season number
   - Set watched date and season rating
   - Add season-specific notes
   - Upload season-specific poster

3. Click "Add TV Show with Season"

### Quick Entry (From Search/API)

Navigate to **TV Shows → Add TV Show**:

1. Search for a show
2. Select from results
3. Choose a season from the grid
4. Fill in watched date and rating
5. Add

### Display Features

#### Grid View
- Shows display with their **main show poster**
- Shows season count, year, genres, overall rating

#### Details View (Plex-Style)
- **Seasons grouped by year** (based on watched date)
- Each season shows its **individual poster**
- Quick delete buttons for seasons
- Show-level delete removes entire show

## API Changes

### New Endpoints

#### Show Management
- `GET /tv-shows/` - List all shows with seasons
- `GET /tv-shows/{show_id}` - Get specific show with seasons
- `POST /tv-shows/` - Create new show (metadata only)
- `PUT /tv-shows/{show_id}` - Update show metadata
- `DELETE /tv-shows/{show_id}` - Delete show and all seasons

#### Season Management
- `GET /tv-shows/{show_id}/seasons` - Get all seasons for a show
- `GET /tv-shows/seasons/{season_id}` - Get specific season
- `POST /tv-shows/seasons` - Create new season
- `PUT /tv-shows/seasons/{season_id}` - Update season
- `DELETE /tv-shows/seasons/{season_id}` - Delete season

#### Legacy Endpoint (Backward Compatible)
- `POST /tv-shows/legacy` - Old-style single call (creates/updates show and adds season)

### Example: Adding a Show with Seasons

```python
import requests

# 1. Create the show
show_data = {
    "title": "Party Down",
    "year": 2009,
    "genres": "Comedy, Drama",
    "overall_rating": 8.5,
    "show_thumbnail_url": "https://example.com/party-down-poster.jpg"
}
response = requests.post("http://localhost:8000/tv-shows/", json=show_data)
show_id = response.json()["id"]

# 2. Add Season 1
season_data = {
    "show_id": show_id,
    "season_number": 1,
    "watched_date": "2024-01-15",
    "rating": 8.0,
    "notes": "Great start!",
    "season_thumbnail_url": "https://example.com/party-down-s1.jpg"
}
requests.post("http://localhost:8000/tv-shows/seasons", json=season_data)

# 3. Add Season 2
season_data = {
    "show_id": show_id,
    "season_number": 2,
    "watched_date": "2024-02-10",
    "rating": 9.0,
    "season_thumbnail_url": "https://example.com/party-down-s2.jpg"
}
requests.post("http://localhost:8000/tv-shows/seasons", json=season_data)
```

## Troubleshooting

### Migration Fails

- **Error**: "table tv_shows already exists"
  - **Solution**: The migration may have partially run. Check if `tv_shows_old` exists. If yes, manually restore from backup.

### Shows Not Appearing

- **Error**: Frontend shows no TV shows after migration
  - **Solution**: Check that the backend is using the updated models. Restart the backend server.

### Missing Posters

- **Problem**: Old thumbnails not displaying
  - **Solution**: The migration copies thumbnails from old `thumbnail_url` to both `show_thumbnail_url` and `season_thumbnail_url`. You can update them individually via the UI or API.

### Database Locked

- **Error**: "database is locked" during migration
  - **Solution**: Stop the backend server before running migration, then restart after completion.

## Rollback

If you need to rollback:

```bash
# Stop the backend
# Restore from backup
cp media_tracker.db.backup media_tracker.db

# Revert code changes
git checkout HEAD -- backend/models.py backend/schemas.py backend/routers/tv_shows.py frontend/app.py
```

## Data Model Reference

### Show Model (Python)
```python
class TVShow(Base):
    id: int
    title: str
    year: Optional[int]
    genres: Optional[str]
    overall_rating: Optional[float]
    show_thumbnail_url: Optional[str]
    created_at: datetime
    seasons: List[TVShowSeason]  # Relationship
```

### Season Model (Python)
```python
class TVShowSeason(Base):
    id: int
    show_id: int
    season_number: int
    watched_date: date
    rating: Optional[float]
    notes: Optional[str]
    season_thumbnail_url: Optional[str]
    created_at: datetime
    show: TVShow  # Back-reference
```

## Future Enhancements

Potential improvements to consider:
- Episode-level tracking
- Rewatch tracking (multiple dates per season)
- Series progress percentage
- Episode count and air dates from API
- Custom season ordering/special seasons
- Show/season tags and categories

## Support

For issues or questions:
1. Check the migration script output for errors
2. Verify database backup exists
3. Check backend logs for API errors
4. Review this guide's troubleshooting section

