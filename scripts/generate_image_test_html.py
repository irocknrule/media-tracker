#!/usr/bin/env python3
"""
Generate an HTML file to test all exercise image URLs in a browser.
This bypasses SSL certificate issues that Python's requests library may have.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Exercise

DATABASE_URL = "sqlite:///./media_tracker.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def generate_test_html():
    """Generate HTML file to test all image URLs"""
    
    db = SessionLocal()
    
    try:
        exercises = db.query(Exercise).order_by(Exercise.name).all()
        
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Exercise Image Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a1a;
            color: #fff;
        }
        h1 {
            text-align: center;
            color: #4CAF50;
        }
        .exercise {
            margin: 20px 0;
            padding: 15px;
            border: 2px solid #333;
            border-radius: 8px;
            background: #2a2a2a;
        }
        .exercise h3 {
            margin-top: 0;
            color: #4CAF50;
        }
        .image-container {
            margin: 10px 0;
            text-align: center;
        }
        img {
            max-width: 400px;
            border: 2px solid #444;
            border-radius: 4px;
            background: #fff;
        }
        .url {
            font-size: 12px;
            color: #888;
            word-break: break-all;
            margin: 5px 0;
        }
        .status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
            margin: 10px 0;
        }
        .status.loading {
            background: #FFA500;
            color: #000;
        }
        .status.success {
            background: #4CAF50;
            color: #fff;
        }
        .status.error {
            background: #f44336;
            color: #fff;
        }
        .summary {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #333;
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #4CAF50;
        }
        .summary div {
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <h1>Exercise Image URL Test</h1>
    <div class="summary">
        <div>Total: <span id="total">0</span></div>
        <div style="color: #4CAF50;">✓ Working: <span id="working">0</span></div>
        <div style="color: #f44336;">✗ Broken: <span id="broken">0</span></div>
    </div>
"""
        
        for exercise in exercises:
            if not exercise.image_url:
                continue
            
            # Escape special characters for JavaScript
            name = exercise.name.replace("'", "\\'")
            url = exercise.image_url.replace("'", "\\'")
            
            html += f"""
    <div class="exercise">
        <h3>{exercise.name}</h3>
        <div class="status loading" id="status-{exercise.id}">Loading...</div>
        <div class="url">{exercise.image_url}</div>
        <div class="image-container">
            <img src="{exercise.image_url}" 
                 id="img-{exercise.id}"
                 onload="imageLoaded({exercise.id})" 
                 onerror="imageError({exercise.id}, '{url}')">
        </div>
    </div>
"""
        
        html += """
    <script>
        let working = 0;
        let broken = 0;
        const total = document.querySelectorAll('img').length;
        document.getElementById('total').textContent = total;
        
        function imageLoaded(id) {
            const status = document.getElementById('status-' + id);
            status.textContent = '✓ Image Loaded Successfully';
            status.className = 'status success';
            working++;
            document.getElementById('working').textContent = working;
        }
        
        function imageError(id, url) {
            const status = document.getElementById('status-' + id);
            status.textContent = '✗ Failed to Load Image';
            status.className = 'status error';
            broken++;
            document.getElementById('broken').textContent = broken;
            console.error('Failed to load:', url);
        }
    </script>
</body>
</html>
"""
        
        output_path = Path(__file__).parent.parent / "test_exercise_images.html"
        output_path.write_text(html)
        
        print("=" * 70)
        print("HTML TEST FILE GENERATED")
        print("=" * 70)
        print(f"\nFile location: {output_path}")
        print("\nTo test the images:")
        print(f"  1. Open this file in your browser:")
        print(f"     file://{output_path}")
        print(f"  2. Or run: open {output_path}")
        print("\nThe HTML file will show which images load successfully")
        print("in your browser (bypassing Python SSL issues).")
        print("=" * 70)
        
    finally:
        db.close()


if __name__ == "__main__":
    generate_test_html()

