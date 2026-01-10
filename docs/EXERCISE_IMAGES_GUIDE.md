# Adding Exercise Images Guide

This guide explains how to add GIF images to your exercises in the workout tracker.

## Overview

All 45 exercises in your database currently don't have images. You have multiple options to add them:

## Option 1: Use Existing Obsidian GIFs (Quickest)

You already have some GIFs in your `obsidian/_assets/` folder:
- `deadlift-2.gif`
- `Romanian-Deadlift.gif`
- `bai-tap-bent-over-barbell-row.gif`
- `dumbbell-rear-delt-fly.webp`
- `opposite_arm_leg_dumbbell_straight_leg_deadlift.gif`

### To use these:
```bash
cd /Users/zubair/media-tracker
source .venv/bin/activate
python scripts/fetch_exercise_images.py
# Select option 1
```

This will map the existing GIFs to the matching exercises.

## Option 2: Use Free ExerciseDB API (Recommended for Most Exercises)

ExerciseDB provides free exercise GIFs and images.

### Setup:
1. Get a free API key:
   - Go to: https://rapidapi.com/justin-WFnsXH_t6/api/exercisedb
   - Sign up for free (no credit card required)
   - Subscribe to the free tier (10 requests/month, or upgrade for more)
   - Copy your API key

2. Set the environment variable:
   ```bash
   export RAPIDAPI_KEY=your_key_here
   ```

3. Run the script:
   ```bash
   cd /Users/zubair/media-tracker
   source .venv/bin/activate
   python scripts/fetch_exercise_images.py
   # Select option 2 or 3 (recommended)
   ```

### What it does:
- Fetches high-quality exercise GIFs from ExerciseDB
- Automatically maps them to your exercises
- Updates the database with image URLs
- Handles rate limiting to be nice to the API

## Option 3: Manual Entry via Frontend (Most Control)

You can now add image URLs directly in the frontend:

1. Go to **Workout Tracker → Exercises**
2. Find an exercise without an image (marked with ⚠️ No image)
3. Click the **✏️ Edit** button
4. Enter an image URL in the "Image URL" field
5. Click **💾 Save**

### Where to find free exercise images:
- **ExerciseDB**: https://rapidapi.com/justin-WFnsXH_t6/api/exercisedb (free tier available)
- **FitNotes Wiki**: Various open-source exercise animations
- **Your own photos/GIFs**: Upload to a hosting service and use the URL

### Example image URLs:
```
https://v2.exercisedb.io/image/deadlift.gif
https://v2.exercisedb.io/image/barbell-squat.gif
```

## Option 4: Use Local Files

If you have local GIF files:

1. Create an `assets` folder in your project:
   ```bash
   mkdir -p /Users/zubair/media-tracker/frontend/assets
   ```

2. Copy your GIF files there

3. Update exercises to use relative paths like:
   ```
   /assets/deadlift.gif
   ```

4. Configure your Streamlit app to serve static files (add to `frontend/app.py`):
   ```python
   # At the top of the file
   st.set_page_config(page_title="...", ...)
   ```

## Checking Which Exercises Need Images

Run this command to see which exercises are missing images:

```bash
cd /Users/zubair/media-tracker
source .venv/bin/activate
python3 -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Exercise

engine = create_engine('sqlite:///./media_tracker.db')
Session = sessionmaker(bind=engine)
db = Session()

exercises = db.query(Exercise).filter(
    (Exercise.image_url == None) | (Exercise.image_url == '')
).all()

print(f'Exercises without images: {len(exercises)}')
for ex in exercises:
    print(f'  - {ex.name}')
"
```

## Recommended Approach

**Best strategy for adding all images:**

1. **First**, use Option 1 to map your existing Obsidian GIFs (covers ~5 exercises)
2. **Then**, use Option 2 with the ExerciseDB API (covers most remaining exercises)
3. **Finally**, manually add URLs for any remaining exercises via the frontend

This combination will give you the best coverage with minimal effort!

## Copyright Notice

When using images from the web:
- ✅ ExerciseDB API - Free to use with attribution
- ✅ Your own photos/GIFs - You own the rights
- ❌ Random Google Images - May be copyrighted
- ❌ YouTube video screenshots - Copyright issues

Always prefer legitimate free sources or create your own content.

## Troubleshooting

### Script says "RAPIDAPI_KEY environment variable not set"
Solution: Export the key before running:
```bash
export RAPIDAPI_KEY=your_key_here
python scripts/fetch_exercise_images.py
```

### Image URL doesn't work in the app
- Make sure the URL is publicly accessible
- Check that it's a direct link to an image file (.gif, .png, .jpg, .webp)
- Test the URL in a browser first

### Want to see the images in the app
After adding image URLs, you'll see them when:
- Viewing exercise details (upcoming feature)
- Logging workouts (can be enhanced)
- In the exercise library (shows ✓ Has image indicator)

## Future Enhancements

Potential improvements:
1. Display exercise GIFs in the exercise library
2. Show form hints with GIFs when logging workouts
3. Upload files directly through the frontend
4. Bulk import from a CSV file
5. Integration with more free exercise APIs

