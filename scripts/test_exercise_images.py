#!/usr/bin/env python3
"""
Script to test which exercise image URLs are working and which are broken.
"""

import sys
from pathlib import Path
import requests
from time import sleep

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Exercise

# Database setup
DATABASE_URL = "sqlite:///./media_tracker.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def test_image_url(url: str) -> bool:
    """Test if an image URL is accessible"""
    if not url:
        return False
    
    # Local files are always "accessible"
    if url.startswith('/obsidian/'):
        return True
    
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code == 200
    except:
        try:
            # Some servers don't support HEAD, try GET
            response = requests.get(url, timeout=5, stream=True)
            return response.status_code == 200
        except:
            return False


def test_all_exercise_images():
    """Test all exercise image URLs"""
    
    print("=" * 70)
    print("TESTING ALL EXERCISE IMAGE URLS")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        exercises = db.query(Exercise).all()
        
        working = []
        broken = []
        no_image = []
        
        print(f"\nTesting {len(exercises)} exercises...\n")
        
        for exercise in exercises:
            if not exercise.image_url:
                no_image.append(exercise.name)
                print(f"  ⚠️  {exercise.name}: No image URL")
                continue
            
            print(f"  Testing: {exercise.name}...", end=" ")
            
            if test_image_url(exercise.image_url):
                working.append((exercise.name, exercise.image_url))
                print("✓ Working")
            else:
                broken.append((exercise.name, exercise.image_url))
                print("✗ BROKEN")
            
            sleep(0.1)  # Be nice to servers
        
        print("\n" + "=" * 70)
        print("TEST RESULTS")
        print("=" * 70)
        
        print(f"\n✅ Working: {len(working)}")
        print(f"❌ Broken: {len(broken)}")
        print(f"⚠️  No Image: {len(no_image)}")
        
        if broken:
            print("\n" + "=" * 70)
            print("BROKEN IMAGE URLS:")
            print("=" * 70)
            for name, url in broken:
                print(f"\n  {name}:")
                print(f"    {url}")
        
        if no_image:
            print("\n" + "=" * 70)
            print("EXERCISES WITHOUT IMAGES:")
            print("=" * 70)
            for name in no_image:
                print(f"  - {name}")
        
    finally:
        db.close()


if __name__ == "__main__":
    test_all_exercise_images()

