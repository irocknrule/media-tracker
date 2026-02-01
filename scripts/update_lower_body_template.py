#!/usr/bin/env python3
"""
Update the 'Lower Body' workout template with recommended exercises for:
  barbell, bench, squat rack, smaller bar, plates, adjustable dumbbell up to 100lbs.

Keeps: Barbell Squat, Dumbbell Lunges.
Adds: Bulgarian Split Squat, Barbell Hip Thrust, Calf Raises.
(No Romanian Deadlift here — do it on full body compound day.)
Removes: any machine-only exercises (e.g. Leg Press) if present.

Run from project root: python scripts/update_lower_body_template.py
"""

import os
import sqlite3
import sys


def find_database_path():
    """Find the database file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(script_dir, "..", "data", "media_tracker.db"),
        os.path.join(script_dir, "..", "media_tracker.db"),
        "data/media_tracker.db",
        "media_tracker.db",
    ]
    for path in paths:
        full = os.path.abspath(path)
        if os.path.exists(full):
            return full
    return None


# Recommended order: compound first, then single-leg, then isolation.
# Romanian Deadlift omitted — you do it on full body compound day.
# Goblet Squat last = optional (add when you have time).
RECOMMENDED_EXERCISES = [
    ("Barbell Squat", "Quadriceps"),
    ("Bulgarian Split Squat", "Quadriceps"),
    ("Dumbbell Lunges", "Quadriceps"),
    ("Barbell Hip Thrust", "Glutes"),
    ("Single-Leg RDL", "Hamstrings"),
    ("Calf Raises", "Calves"),
    ("Goblet Squat", "Quadriceps"),  # optional
]

# Alternative names to match existing exercises in DB (e.g. "Lunges" or "dumbell-lunges")
NAME_ALIASES = {
    "dumbbell lunges": ["dumbbell lunges", "dumbell lunges", "lunges", "dumbbell lunge"],
    "barbell squat": ["barbell squat", "barbell back squat"],
    "bulgarian split squat": ["bulgarian split squat", "bulgarian split squats"],
    "barbell hip thrust": ["barbell hip thrust", "hip thrust", "hip thrusts"],
    "single-leg rdl": ["single-leg rdl", "single leg rdl", "single-leg deadlift", "single leg deadlift"],
    "calf raises": ["calf raises", "standing calf raise", "dumbbell calf raises"],
    "goblet squat": ["goblet squat", "dumbbell goblet squat", "dumbbell-goblet-squat"],
}


def normalize(s: str) -> str:
    """Normalize for comparison: lowercase, hyphens to spaces, collapse spaces."""
    return " ".join(s.lower().replace("-", " ").split())


def get_or_create_exercise(cursor, canonical_name: str, primary_muscle: str) -> int:
    """Return exercise id by exact or case-insensitive name; create if missing."""
    cursor.execute(
        "SELECT id, name FROM exercises WHERE LOWER(TRIM(name)) = LOWER(?)",
        (canonical_name.strip(),),
    )
    row = cursor.fetchone()
    if row:
        return row[0]

    # Try aliases (match normalized names)
    key = normalize(canonical_name)
    aliases = NAME_ALIASES.get(key, [key])
    cursor.execute("SELECT id, name FROM exercises")
    for row in cursor.fetchall():
        if normalize(row["name"]) in aliases:
            return row["id"]

    # Create (include created_at/updated_at so API response validation doesn't fail)
    cursor.execute(
        """INSERT INTO exercises (name, primary_muscle, created_at, updated_at)
           VALUES (?, ?, datetime('now'), datetime('now'))""",
        (canonical_name, primary_muscle),
    )
    return cursor.lastrowid


def main():
    db_path = find_database_path()
    if not db_path:
        print("Could not find media_tracker.db. Run from project root or set path.")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find "Lower Body" workout (case-insensitive)
    cursor.execute(
        "SELECT id, name FROM workouts WHERE LOWER(TRIM(name)) = 'lower body'"
    )
    row = cursor.fetchone()
    if not row:
        print("No workout named 'Lower Body' found. Create it in the app first, or create it here.")
        # Optionally create the template
        cursor.execute(
            """INSERT INTO workouts (name, description, created_at, updated_at)
               VALUES (?, ?, datetime('now'), datetime('now'))""",
            ("Lower Body", "Barbell, bench, squat rack, dumbbell. Squat, RDL, split squat, lunges, hip thrust, calves."),
        )
        workout_id = cursor.lastrowid
        print(f"Created workout 'Lower Body' (id={workout_id}).")
    else:
        workout_id = row[0]
        print(f"Updating workout '{row[1]}' (id={workout_id}).")

    exercise_ids = []
    for canonical_name, primary_muscle in RECOMMENDED_EXERCISES:
        eid = get_or_create_exercise(cursor, canonical_name, primary_muscle)
        exercise_ids.append(eid)
        cursor.execute("SELECT name FROM exercises WHERE id = ?", (eid,))
        print(f"  {cursor.fetchone()[0]} (id={eid})")

    # Replace template exercises
    cursor.execute("DELETE FROM workout_exercises WHERE workout_id = ?", (workout_id,))
    for idx, eid in enumerate(exercise_ids):
        cursor.execute(
            "INSERT INTO workout_exercises (workout_id, exercise_id, order_index) VALUES (?, ?, ?)",
            (workout_id, eid, idx),
        )

    conn.commit()
    conn.close()
    print("Done. Lower Body template updated.")


if __name__ == "__main__":
    main()
