#!/usr/bin/env python3
"""
Convert all exercise image URLs to base64 data URIs stored directly in the database.
This matches the behavior of book/movie thumbnails.
"""

import sys
from pathlib import Path
import base64
import mimetypes

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Exercise

DATABASE_URL = "sqlite:///./media_tracker.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def get_image_data_from_url(url: str) -> tuple[bytes, str]:
    """Download image from URL and return bytes and mime type"""
    try:
        import requests
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': url.rsplit('/', 1)[0] + '/',
        }
        
        response = requests.get(url, headers=headers, timeout=15, verify=False, allow_redirects=True)
        response.raise_for_status()
        
        data = response.content
        
        # Determine mime type from URL extension or Content-Type header
        mime_type = response.headers.get('Content-Type', '').split(';')[0]
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = mimetypes.guess_type(url)[0] or 'image/gif'
        
        return data, mime_type
    except Exception as e:
        print(f"    ✗ Failed to download: {e}")
        return None, None


def get_image_data_from_file(file_path: str) -> tuple[bytes, str]:
    """Read image from local file and return bytes and mime type"""
    try:
        # Convert relative path to absolute
        base_path = Path(__file__).parent.parent
        full_path = base_path / file_path.lstrip('/')
        
        if not full_path.exists():
            print(f"    ✗ File not found: {full_path}")
            return None, None
        
        with open(full_path, 'rb') as f:
            data = f.read()
        
        # Determine mime type from file extension
        mime_type = mimetypes.guess_type(str(full_path))[0] or 'image/gif'
        
        return data, mime_type
    except Exception as e:
        print(f"    ✗ Failed to read file: {e}")
        return None, None


def convert_to_base64_data_uri(image_data: bytes, mime_type: str) -> str:
    """Convert image bytes to base64 data URI"""
    base64_data = base64.b64encode(image_data).decode('utf-8')
    return f"data:{mime_type};base64,{base64_data}"


def convert_all_exercise_images():
    """Convert all exercise images to base64 data URIs"""
    
    print("=" * 70)
    print("CONVERTING EXERCISE IMAGES TO BASE64")
    print("=" * 70)
    print("\nThis will download all external images and convert them to")
    print("base64 data URIs stored directly in the database.\n")
    
    db = SessionLocal()
    
    try:
        exercises = db.query(Exercise).filter(Exercise.image_url.isnot(None)).all()
        
        print(f"Found {len(exercises)} exercises with images\n")
        
        converted = 0
        skipped = 0
        failed = 0
        
        for exercise in exercises:
            print(f"Processing: {exercise.name}")
            
            # Skip if already base64
            if exercise.image_url.startswith('data:'):
                print(f"  ⊙ Already base64, skipping")
                skipped += 1
                continue
            
            # Check if it's a local file or external URL
            if exercise.image_url.startswith('/obsidian/') or exercise.image_url.startswith('obsidian/'):
                print(f"  → Reading from local file...")
                image_data, mime_type = get_image_data_from_file(exercise.image_url)
            elif exercise.image_url.startswith('http://') or exercise.image_url.startswith('https://'):
                print(f"  → Downloading from URL...")
                image_data, mime_type = get_image_data_from_url(exercise.image_url)
            else:
                print(f"  ✗ Unknown URL format: {exercise.image_url}")
                failed += 1
                continue
            
            if image_data:
                # Convert to base64 data URI
                data_uri = convert_to_base64_data_uri(image_data, mime_type)
                
                # Calculate size
                size_kb = len(image_data) / 1024
                
                # Update database
                old_url = exercise.image_url
                exercise.image_url = data_uri
                
                print(f"  ✓ Converted ({size_kb:.1f} KB)")
                print(f"    Old: {old_url[:70]}...")
                print(f"    New: {data_uri[:70]}...")
                
                converted += 1
            else:
                print(f"  ✗ Failed to get image data")
                failed += 1
            
            print()
        
        # Commit all changes
        db.commit()
        
        print("=" * 70)
        print("CONVERSION COMPLETE")
        print("=" * 70)
        print(f"\n✓ Converted: {converted}")
        print(f"⊙ Skipped (already base64): {skipped}")
        print(f"✗ Failed: {failed}")
        print(f"\nTotal exercises with images: {len(exercises)}")
        
        if converted > 0:
            print("\n🎉 All images are now stored directly in the database!")
            print("   Images will work offline and won't break if external URLs change.")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    convert_all_exercise_images()

