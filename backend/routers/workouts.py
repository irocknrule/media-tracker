from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, date
from collections import defaultdict
from backend.database import get_db
from backend.models import (
    Exercise as ExerciseModel,
    Workout as WorkoutModel,
    WorkoutExercise as WorkoutExerciseModel,
    WorkoutRecord as WorkoutRecordModel,
    ExerciseRecord as ExerciseRecordModel,
    SetRecord as SetRecordModel,
    HabitLog as HabitLogModel
)
from backend.schemas import (
    Exercise,
    ExerciseCreate,
    ExerciseUpdate,
    Workout,
    WorkoutCreate,
    WorkoutUpdate,
    WorkoutWithExercises,
    WorkoutExerciseDetail,
    WorkoutRecord,
    WorkoutRecordCreate,
    WorkoutRecordUpdate,
    WorkoutRecordWithExercises,
    ExerciseRecord,
    SetRecord,
    ExerciseProgress,
    ExerciseProgressEntry,
    WorkoutAnalytics
)

router = APIRouter(prefix="/workouts", tags=["workouts"])


# ============================================================================
# EXERCISE ENDPOINTS
# ============================================================================

@router.post("/exercises", response_model=Exercise, status_code=status.HTTP_201_CREATED)
def create_exercise(exercise: ExerciseCreate, db: Session = Depends(get_db)):
    """Create a new exercise"""
    # Check if exercise with same name already exists
    existing = db.query(ExerciseModel).filter(
        func.lower(ExerciseModel.name) == func.lower(exercise.name)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exercise '{exercise.name}' already exists"
        )
    
    db_exercise = ExerciseModel(**exercise.model_dump())
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)
    return db_exercise


@router.get("/exercises", response_model=List[Exercise])
def get_exercises(
    muscle: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all exercises, optionally filtered by muscle group or search term"""
    query = db.query(ExerciseModel)
    
    if muscle:
        query = query.filter(
            (ExerciseModel.primary_muscle.ilike(f"%{muscle}%")) |
            (ExerciseModel.secondary_muscles.ilike(f"%{muscle}%"))
        )
    
    if search:
        query = query.filter(ExerciseModel.name.ilike(f"%{search}%"))
    
    exercises = query.order_by(ExerciseModel.name).offset(skip).limit(limit).all()
    return exercises


@router.get("/exercises/{exercise_id}", response_model=Exercise)
def get_exercise(exercise_id: int, db: Session = Depends(get_db)):
    """Get a specific exercise by ID"""
    exercise = db.query(ExerciseModel).filter(ExerciseModel.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise


@router.put("/exercises/{exercise_id}", response_model=Exercise)
def update_exercise(
    exercise_id: int,
    exercise_update: ExerciseUpdate,
    db: Session = Depends(get_db)
):
    """Update an exercise"""
    db_exercise = db.query(ExerciseModel).filter(ExerciseModel.id == exercise_id).first()
    if not db_exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    # Check for name conflicts if name is being updated
    if exercise_update.name and exercise_update.name != db_exercise.name:
        existing = db.query(ExerciseModel).filter(
            func.lower(ExerciseModel.name) == func.lower(exercise_update.name),
            ExerciseModel.id != exercise_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Exercise '{exercise_update.name}' already exists"
            )
    
    # Update fields
    for field, value in exercise_update.model_dump(exclude_unset=True).items():
        setattr(db_exercise, field, value)
    
    db.commit()
    db.refresh(db_exercise)
    return db_exercise


@router.delete("/exercises/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(exercise_id: int, db: Session = Depends(get_db)):
    """Delete an exercise"""
    db_exercise = db.query(ExerciseModel).filter(ExerciseModel.id == exercise_id).first()
    if not db_exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    db.delete(db_exercise)
    db.commit()
    return None


@router.get("/exercises/{exercise_id}/progress", response_model=ExerciseProgress)
def get_exercise_progress(
    exercise_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get progress history for a specific exercise"""
    exercise = db.query(ExerciseModel).filter(ExerciseModel.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    # Query exercise records
    query = db.query(ExerciseRecordModel).join(WorkoutRecordModel).filter(
        ExerciseRecordModel.exercise_id == exercise_id
    )
    
    if start_date:
        query = query.filter(WorkoutRecordModel.workout_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(WorkoutRecordModel.workout_date <= datetime.combine(end_date, datetime.max.time()))
    
    records = query.order_by(WorkoutRecordModel.workout_date).all()
    
    # Build history
    history = []
    pr_weight = 0.0
    pr_volume = 0.0
    pr_reps = 0
    
    for record in records:
        volume = None
        one_rep_max = None
        
        if record.sets and record.reps and record.weight:
            volume = record.sets * record.reps * record.weight
            # Epley formula for 1RM estimation
            if record.reps == 1:
                one_rep_max = record.weight
            else:
                one_rep_max = record.weight * (1 + record.reps / 30.0)
        
        # Get workout date
        workout_record = db.query(WorkoutRecordModel).filter(
            WorkoutRecordModel.id == record.workout_record_id
        ).first()
        
        history.append(ExerciseProgressEntry(
            date=workout_record.workout_date,
            sets=record.sets,
            reps=record.reps,
            weight=record.weight,
            volume=volume,
            one_rep_max=one_rep_max
        ))
        
        # Track PRs
        if record.weight and record.weight > pr_weight:
            pr_weight = record.weight
        if volume and volume > pr_volume:
            pr_volume = volume
        if record.reps and record.reps > pr_reps:
            pr_reps = record.reps
    
    return ExerciseProgress(
        exercise_id=exercise.id,
        exercise_name=exercise.name,
        history=history,
        personal_record_weight=pr_weight if pr_weight > 0 else None,
        personal_record_volume=pr_volume if pr_volume > 0 else None,
        personal_record_reps=pr_reps if pr_reps > 0 else None
    )


# ============================================================================
# WORKOUT TEMPLATE ENDPOINTS
# ============================================================================

@router.post("/templates", response_model=WorkoutWithExercises, status_code=status.HTTP_201_CREATED)
def create_workout(workout: WorkoutCreate, db: Session = Depends(get_db)):
    """Create a new workout template"""
    # Check if workout with same name exists
    existing = db.query(WorkoutModel).filter(
        func.lower(WorkoutModel.name) == func.lower(workout.name)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workout '{workout.name}' already exists"
        )
    
    # Create workout
    db_workout = WorkoutModel(
        name=workout.name,
        description=workout.description
    )
    db.add(db_workout)
    db.flush()  # Get the workout ID
    
    # Add exercises
    for idx, exercise_id in enumerate(workout.exercise_ids):
        exercise = db.query(ExerciseModel).filter(ExerciseModel.id == exercise_id).first()
        if not exercise:
            raise HTTPException(status_code=404, detail=f"Exercise with ID {exercise_id} not found")
        
        workout_exercise = WorkoutExerciseModel(
            workout_id=db_workout.id,
            exercise_id=exercise_id,
            order_index=idx
        )
        db.add(workout_exercise)
    
    db.commit()
    db.refresh(db_workout)
    
    # Return with exercises
    return _get_workout_with_exercises(db_workout.id, db)


@router.get("/templates", response_model=List[Workout])
def get_workouts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all workout templates"""
    workouts = db.query(WorkoutModel).order_by(WorkoutModel.name).offset(skip).limit(limit).all()
    return workouts


@router.get("/templates/{workout_id}", response_model=WorkoutWithExercises)
def get_workout(workout_id: int, db: Session = Depends(get_db)):
    """Get a specific workout template with exercises"""
    return _get_workout_with_exercises(workout_id, db)


@router.put("/templates/{workout_id}", response_model=WorkoutWithExercises)
def update_workout(
    workout_id: int,
    workout_update: WorkoutUpdate,
    db: Session = Depends(get_db)
):
    """Update a workout template"""
    db_workout = db.query(WorkoutModel).filter(WorkoutModel.id == workout_id).first()
    if not db_workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    
    # Check for name conflicts
    if workout_update.name and workout_update.name != db_workout.name:
        existing = db.query(WorkoutModel).filter(
            func.lower(WorkoutModel.name) == func.lower(workout_update.name),
            WorkoutModel.id != workout_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workout '{workout_update.name}' already exists"
            )
    
    # Update basic fields
    if workout_update.name:
        db_workout.name = workout_update.name
    if workout_update.description is not None:
        db_workout.description = workout_update.description
    
    # Update exercises if provided
    if workout_update.exercise_ids is not None:
        # Delete existing exercise associations
        db.query(WorkoutExerciseModel).filter(
            WorkoutExerciseModel.workout_id == workout_id
        ).delete()
        
        # Add new exercises
        for idx, exercise_id in enumerate(workout_update.exercise_ids):
            exercise = db.query(ExerciseModel).filter(ExerciseModel.id == exercise_id).first()
            if not exercise:
                raise HTTPException(status_code=404, detail=f"Exercise with ID {exercise_id} not found")
            
            workout_exercise = WorkoutExerciseModel(
                workout_id=workout_id,
                exercise_id=exercise_id,
                order_index=idx
            )
            db.add(workout_exercise)
    
    db.commit()
    db.refresh(db_workout)
    
    return _get_workout_with_exercises(workout_id, db)


@router.delete("/templates/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(workout_id: int, db: Session = Depends(get_db)):
    """Delete a workout template"""
    db_workout = db.query(WorkoutModel).filter(WorkoutModel.id == workout_id).first()
    if not db_workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    
    db.delete(db_workout)
    db.commit()
    return None


# ============================================================================
# WORKOUT RECORD ENDPOINTS
# ============================================================================

@router.post("/records", response_model=WorkoutRecordWithExercises, status_code=status.HTTP_201_CREATED)
def create_workout_record(record: WorkoutRecordCreate, db: Session = Depends(get_db)):
    """Log a workout session"""
    # Validate workout_id if provided
    if record.workout_id:
        workout = db.query(WorkoutModel).filter(WorkoutModel.id == record.workout_id).first()
        if not workout:
            raise HTTPException(status_code=404, detail="Workout template not found")
    
    # Create workout record
    db_record = WorkoutRecordModel(
        workout_id=record.workout_id,
        workout_name=record.workout_name,
        workout_date=record.workout_date,
        duration_minutes=record.duration_minutes,
        notes=record.notes
    )
    db.add(db_record)
    db.flush()  # Get the record ID
    
    # Add exercise records
    for exercise_data in record.exercises:
        # Get exercise name
        exercise = db.query(ExerciseModel).filter(
            ExerciseModel.id == exercise_data.exercise_id
        ).first()
        if not exercise:
            raise HTTPException(status_code=404, detail=f"Exercise with ID {exercise_data.exercise_id} not found")
        
        # Calculate sets, reps, and weight from set_records if provided
        sets_count = None
        avg_reps = None
        avg_weight = None
        
        if exercise_data.set_records and len(exercise_data.set_records) > 0:
            sets_count = len(exercise_data.set_records)
            total_reps = sum(sr.reps for sr in exercise_data.set_records)
            avg_reps = total_reps // sets_count if sets_count > 0 else None
            weights = [sr.weight for sr in exercise_data.set_records if sr.weight]
            avg_weight = sum(weights) / len(weights) if weights else None
        else:
            # Use legacy fields if set_records not provided
            sets_count = exercise_data.sets
            avg_reps = exercise_data.reps
            avg_weight = exercise_data.weight
        
        exercise_record = ExerciseRecordModel(
            workout_record_id=db_record.id,
            exercise_id=exercise_data.exercise_id,
            exercise_name=exercise.name,
            sets=sets_count,
            reps=avg_reps,
            weight=avg_weight,
            weight_unit=exercise_data.weight_unit,
            time_seconds=exercise_data.time_seconds,
            distance=exercise_data.distance,
            distance_unit=exercise_data.distance_unit,
            notes=exercise_data.notes
        )
        db.add(exercise_record)
        db.flush()  # Get the exercise_record ID
        
        # Create individual set records if provided
        if exercise_data.set_records and len(exercise_data.set_records) > 0:
            for set_idx, set_data in enumerate(exercise_data.set_records, start=1):
                set_record = SetRecordModel(
                    exercise_record_id=exercise_record.id,
                    set_number=set_data.set_number if hasattr(set_data, 'set_number') and set_data.set_number else set_idx,
                    reps=set_data.reps,
                    weight=set_data.weight,
                    weight_unit=set_data.weight_unit or exercise_data.weight_unit or "lbs",
                    notes=set_data.notes
                )
                db.add(set_record)
    
    # Create/update habit log entry for this workout
    if record.duration_minutes:
        # Convert workout_date (datetime) to date
        workout_date = record.workout_date.date() if isinstance(record.workout_date, datetime) else record.workout_date
        
        # Delete existing exercise_workout habit logs for this date (to avoid duplicates)
        db.query(HabitLogModel).filter(
            HabitLogModel.date == workout_date,
            HabitLogModel.habit_type == "exercise_workout"
        ).delete()
        
        # Create new habit log entry
        habit_log = HabitLogModel(
            date=workout_date,
            habit_type="exercise_workout",
            metric_name="minutes",
            value=float(record.duration_minutes),
            unit="min"
        )
        db.add(habit_log)
    
    db.commit()
    db.refresh(db_record)
    
    # Return with exercises
    return _get_workout_record_with_exercises(db_record.id, db)


@router.get("/records", response_model=List[WorkoutRecordWithExercises])
def get_workout_records(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    workout_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get workout records, optionally filtered"""
    query = db.query(WorkoutRecordModel)
    
    if start_date:
        query = query.filter(WorkoutRecordModel.workout_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(WorkoutRecordModel.workout_date <= datetime.combine(end_date, datetime.max.time()))
    if workout_id:
        query = query.filter(WorkoutRecordModel.workout_id == workout_id)
    
    records = query.order_by(desc(WorkoutRecordModel.workout_date)).offset(skip).limit(limit).all()
    
    # Build response with exercises
    result = []
    for record in records:
        result.append(_get_workout_record_with_exercises(record.id, db))
    
    return result


@router.get("/records/{record_id}", response_model=WorkoutRecordWithExercises)
def get_workout_record(record_id: int, db: Session = Depends(get_db)):
    """Get a specific workout record"""
    return _get_workout_record_with_exercises(record_id, db)


@router.get("/records/{workout_id}/last", response_model=WorkoutRecordWithExercises)
def get_last_workout_record(workout_id: int, db: Session = Depends(get_db)):
    """Get the last workout record for a specific workout template"""
    record = db.query(WorkoutRecordModel).filter(
        WorkoutRecordModel.workout_id == workout_id
    ).order_by(desc(WorkoutRecordModel.workout_date)).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="No previous workout found")
    
    return _get_workout_record_with_exercises(record.id, db)


@router.put("/records/{record_id}", response_model=WorkoutRecordWithExercises)
def update_workout_record(
    record_id: int,
    record_update: WorkoutRecordUpdate,
    db: Session = Depends(get_db)
):
    """Update a workout record"""
    db_record = db.query(WorkoutRecordModel).filter(WorkoutRecordModel.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Workout record not found")
    
    # Store old date for habit log cleanup if date changes
    old_date = db_record.workout_date.date() if isinstance(db_record.workout_date, datetime) else db_record.workout_date
    
    for field, value in record_update.model_dump(exclude_unset=True).items():
        setattr(db_record, field, value)
    
    # Get new workout date
    workout_date = db_record.workout_date.date() if isinstance(db_record.workout_date, datetime) else db_record.workout_date
    
    # If date changed, delete old habit log
    if old_date != workout_date:
        db.query(HabitLogModel).filter(
            HabitLogModel.date == old_date,
            HabitLogModel.habit_type == "exercise_workout"
        ).delete()
    
    # Always delete existing habit log for current date (will recreate if duration_minutes exists)
    db.query(HabitLogModel).filter(
        HabitLogModel.date == workout_date,
        HabitLogModel.habit_type == "exercise_workout"
    ).delete()
    
    # Create new habit log entry if duration_minutes is set
    if db_record.duration_minutes:
        habit_log = HabitLogModel(
            date=workout_date,
            habit_type="exercise_workout",
            metric_name="minutes",
            value=float(db_record.duration_minutes),
            unit="min"
        )
        db.add(habit_log)
    
    db.commit()
    db.refresh(db_record)
    
    return _get_workout_record_with_exercises(record_id, db)


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout_record(record_id: int, db: Session = Depends(get_db)):
    """Delete a workout record"""
    db_record = db.query(WorkoutRecordModel).filter(WorkoutRecordModel.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Workout record not found")
    
    # Get workout date before deleting
    workout_date = db_record.workout_date.date() if isinstance(db_record.workout_date, datetime) else db_record.workout_date
    
    # Delete the workout record
    db.delete(db_record)
    
    # Delete associated habit log
    db.query(HabitLogModel).filter(
        HabitLogModel.date == workout_date,
        HabitLogModel.habit_type == "exercise_workout"
    ).delete()
    
    db.commit()
    return None


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/analytics/summary", response_model=WorkoutAnalytics)
def get_workout_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get workout analytics summary"""
    # Build query for workout records
    query = db.query(WorkoutRecordModel)
    
    if start_date:
        query = query.filter(WorkoutRecordModel.workout_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(WorkoutRecordModel.workout_date <= datetime.combine(end_date, datetime.max.time()))
    
    workout_records = query.all()
    workout_record_ids = [r.id for r in workout_records]
    
    # Get all exercise records for these workouts
    exercise_records = db.query(ExerciseRecordModel).filter(
        ExerciseRecordModel.workout_record_id.in_(workout_record_ids)
    ).all() if workout_record_ids else []
    
    # Calculate metrics
    total_workouts = len(workout_records)
    total_exercises_logged = len(exercise_records)
    unique_exercises = len(set(r.exercise_id for r in exercise_records))
    
    # Calculate total volume (use set_records if available, otherwise fall back to legacy fields)
    total_volume = 0.0
    for record in exercise_records:
        # Check if set_records exist for more accurate volume calculation
        set_records = db.query(SetRecordModel).filter(
            SetRecordModel.exercise_record_id == record.id
        ).all()
        
        if set_records:
            # Calculate volume from individual sets
            for sr in set_records:
                total_volume += sr.reps * sr.weight
        elif record.sets and record.reps and record.weight:
            # Fall back to legacy calculation
            total_volume += record.sets * record.reps * record.weight
    
    # Most frequent exercises
    exercise_counts = defaultdict(int)
    for record in exercise_records:
        exercise_counts[record.exercise_name] += 1
    
    most_frequent = [
        {"exercise_name": name, "count": count}
        for name, count in sorted(exercise_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
    
    # Workout frequency by month
    month_counts = defaultdict(int)
    for record in workout_records:
        month_key = record.workout_date.strftime("%Y-%m")
        month_counts[month_key] += 1
    
    frequency_by_month = [
        {"month": month, "count": count}
        for month, count in sorted(month_counts.items())
    ]
    
    # Muscle group distribution
    muscle_distribution = defaultdict(int)
    for record in exercise_records:
        exercise = db.query(ExerciseModel).filter(ExerciseModel.id == record.exercise_id).first()
        if exercise and exercise.primary_muscle:
            muscle_distribution[exercise.primary_muscle] += 1
    
    return WorkoutAnalytics(
        total_workouts=total_workouts,
        total_exercises_logged=total_exercises_logged,
        unique_exercises=unique_exercises,
        total_volume=total_volume,
        most_frequent_exercises=most_frequent,
        workout_frequency_by_month=frequency_by_month,
        muscle_group_distribution=dict(muscle_distribution)
    )


@router.get("/analytics/personal-records")
def get_personal_records(db: Session = Depends(get_db)):
    """Get personal records for all exercises"""
    exercises = db.query(ExerciseModel).all()
    
    prs = []
    for exercise in exercises:
        # Get all records for this exercise
        records = db.query(ExerciseRecordModel).filter(
            ExerciseRecordModel.exercise_id == exercise.id
        ).all()
        
        if not records:
            continue
        
        # Find PRs (check set_records first for accuracy, then fall back to legacy fields)
        max_weight = None
        max_reps = None
        max_volume = None
        
        # Check set_records for more accurate PRs
        for record in records:
            set_records = db.query(SetRecordModel).filter(
                SetRecordModel.exercise_record_id == record.id
            ).all()
            
            if set_records:
                # Use set_records for PRs
                for sr in set_records:
                    if sr.weight and (max_weight is None or sr.weight > max_weight):
                        max_weight = sr.weight
                    if sr.reps and (max_reps is None or sr.reps > max_reps):
                        max_reps = sr.reps
                    volume = sr.reps * sr.weight
                    if max_volume is None or volume > max_volume:
                        max_volume = volume
            else:
                # Fall back to legacy fields
                if record.weight and (max_weight is None or record.weight > max_weight):
                    max_weight = record.weight
                if record.reps and (max_reps is None or record.reps > max_reps):
                    max_reps = record.reps
                if record.sets and record.reps and record.weight:
                    volume = record.sets * record.reps * record.weight
                    if max_volume is None or volume > max_volume:
                        max_volume = volume
        
        if max_weight or max_reps or max_volume:
            prs.append({
                "exercise_id": exercise.id,
                "exercise_name": exercise.name,
                "primary_muscle": exercise.primary_muscle,
                "max_weight": max_weight,
                "max_reps": max_reps,
                "max_volume": max_volume
            })
    
    return sorted(prs, key=lambda x: x["exercise_name"])


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_workout_with_exercises(workout_id: int, db: Session) -> WorkoutWithExercises:
    """Helper to get workout with exercise details"""
    workout = db.query(WorkoutModel).filter(WorkoutModel.id == workout_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    
    # Get exercises in order
    workout_exercises = db.query(WorkoutExerciseModel).filter(
        WorkoutExerciseModel.workout_id == workout_id
    ).order_by(WorkoutExerciseModel.order_index).all()
    
    exercise_details = []
    for we in workout_exercises:
        exercise = db.query(ExerciseModel).filter(ExerciseModel.id == we.exercise_id).first()
        if exercise:
            exercise_details.append(WorkoutExerciseDetail(
                id=we.id,
                exercise_id=exercise.id,
                exercise_name=exercise.name,
                primary_muscle=exercise.primary_muscle,
                order_index=we.order_index,
                notes=we.notes
            ))
    
    return WorkoutWithExercises(
        id=workout.id,
        name=workout.name,
        description=workout.description,
        created_at=workout.created_at,
        updated_at=workout.updated_at,
        exercises=exercise_details
    )


def _get_workout_record_with_exercises(record_id: int, db: Session) -> WorkoutRecordWithExercises:
    """Helper to get workout record with exercise records"""
    record = db.query(WorkoutRecordModel).filter(WorkoutRecordModel.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Workout record not found")
    
    # Get exercise records
    exercise_records = db.query(ExerciseRecordModel).filter(
        ExerciseRecordModel.workout_record_id == record_id
    ).all()
    
    # Build exercise records with set_records
    exercise_list = []
    for er in exercise_records:
        # Get set records for this exercise record
        set_records = db.query(SetRecordModel).filter(
            SetRecordModel.exercise_record_id == er.id
        ).order_by(SetRecordModel.set_number).all()
        
        # Create ExerciseRecord with set_records
        exercise_dict = {
            "id": er.id,
            "workout_record_id": er.workout_record_id,
            "exercise_id": er.exercise_id,
            "exercise_name": er.exercise_name,
            "sets": er.sets,
            "reps": er.reps,
            "weight": er.weight,
            "weight_unit": er.weight_unit,
            "time_seconds": er.time_seconds,
            "distance": er.distance,
            "distance_unit": er.distance_unit,
            "notes": er.notes,
            "created_at": er.created_at,
            "set_records": [SetRecord.model_validate(sr) for sr in set_records] if set_records else []
        }
        exercise_list.append(ExerciseRecord(**exercise_dict))
    
    return WorkoutRecordWithExercises(
        id=record.id,
        workout_id=record.workout_id,
        workout_name=record.workout_name,
        workout_date=record.workout_date,
        duration_minutes=record.duration_minutes,
        notes=record.notes,
        created_at=record.created_at,
        exercises=exercise_list
    )

