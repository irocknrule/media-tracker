from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import date, datetime, timedelta
from collections import defaultdict
from backend.database import get_db
from backend.models import HabitLog as HabitLogModel
from backend.schemas import (
    HabitLog, 
    HabitLogCreate, 
    HabitLogBatchCreate,
    HabitLogResponse,
    HabitCalendarEntry
)

router = APIRouter(prefix="/habits", tags=["habits"])


@router.get("/", response_model=List[HabitLogResponse])
def get_habits(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get all habit logs, optionally filtered by date range"""
    query = db.query(HabitLogModel)
    
    if start_date:
        query = query.filter(HabitLogModel.date >= start_date)
    if end_date:
        query = query.filter(HabitLogModel.date <= end_date)
    
    logs = query.order_by(HabitLogModel.date.desc(), HabitLogModel.habit_type).all()
    
    # Group by date
    grouped = defaultdict(lambda: {"date": None, "habits": defaultdict(list)})
    
    for log in logs:
        if grouped[log.date]["date"] is None:
            grouped[log.date]["date"] = log.date
        
        habit_key = log.habit_type
        grouped[log.date]["habits"][habit_key].append({
            "metric_name": log.metric_name,
            "value": log.value,
            "unit": log.unit
        })
    
    # Convert to response format
    result = []
    for log_date, data in sorted(grouped.items(), reverse=True):
        result.append(HabitLogResponse(
            date=data["date"],
            habits=dict(data["habits"])
        ))
    
    return result


@router.get("/date/{log_date}", response_model=HabitLogResponse)
def get_habits_by_date(
    log_date: date,
    db: Session = Depends(get_db)
):
    """Get all habit logs for a specific date"""
    logs = db.query(HabitLogModel).filter(HabitLogModel.date == log_date).all()
    
    if not logs:
        return HabitLogResponse(date=log_date, habits={})
    
    # Group by habit_type
    habits = defaultdict(list)
    for log in logs:
        habits[log.habit_type].append({
            "metric_name": log.metric_name,
            "value": log.value,
            "unit": log.unit
        })
    
    return HabitLogResponse(date=log_date, habits=dict(habits))


@router.get("/date/{log_date}/detailed", response_model=List[HabitLog])
def get_habits_by_date_detailed(
    log_date: date,
    db: Session = Depends(get_db)
):
    """Get all habit logs for a specific date with full details including IDs"""
    logs = db.query(HabitLogModel).filter(HabitLogModel.date == log_date).all()
    return logs


@router.get("/calendar", response_model=List[HabitCalendarEntry])
def get_calendar_entries(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get calendar entries showing which habits were completed on each date"""
    query = db.query(HabitLogModel)
    
    if start_date:
        query = query.filter(HabitLogModel.date >= start_date)
    if end_date:
        query = query.filter(HabitLogModel.date <= end_date)
    
    logs = query.all()
    
    # Group by date and collect unique habit types
    grouped = defaultdict(set)
    for log in logs:
        grouped[log.date].add(log.habit_type)
    
    # Convert to response format
    result = []
    for log_date, habit_types in sorted(grouped.items()):
        result.append(HabitCalendarEntry(
            date=log_date,
            habit_types=list(habit_types)
        ))
    
    return result


@router.post("/", response_model=List[HabitLog], status_code=status.HTTP_201_CREATED)
def create_habit_logs(
    batch: HabitLogBatchCreate,
    db: Session = Depends(get_db)
):
    """Create multiple habit logs for a single date"""
    # Delete existing logs for this date first (to allow updates)
    db.query(HabitLogModel).filter(HabitLogModel.date == batch.date).delete()
    
    # Create new logs
    created_logs = []
    for log_data in batch.logs:
        db_log = HabitLogModel(
            date=batch.date,
            habit_type=log_data.habit_type,
            metric_name=log_data.metric_name,
            value=log_data.value,
            unit=log_data.unit
        )
        db.add(db_log)
        created_logs.append(db_log)
    
    db.commit()
    
    # Refresh all created logs
    for log in created_logs:
        db.refresh(log)
    
    return created_logs


@router.delete("/date/{log_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habits_by_date(
    log_date: date,
    db: Session = Depends(get_db)
):
    """Delete all habit logs for a specific date"""
    db.query(HabitLogModel).filter(HabitLogModel.date == log_date).delete()
    db.commit()
    return None


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit_log(
    habit_id: int,
    db: Session = Depends(get_db)
):
    """Delete a specific habit log by ID"""
    habit_log = db.query(HabitLogModel).filter(HabitLogModel.id == habit_id).first()
    if not habit_log:
        raise HTTPException(status_code=404, detail="Habit log not found")
    
    db.delete(habit_log)
    db.commit()
    return None


@router.get("/analytics/summary")
def get_habits_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get analytics summary for habits within a date range"""
    query = db.query(HabitLogModel)
    
    if start_date:
        query = query.filter(HabitLogModel.date >= start_date)
    if end_date:
        query = query.filter(HabitLogModel.date <= end_date)
    
    logs = query.all()
    
    # Initialize summary data
    summary = {
        "total_days_with_habits": 0,
        "exercise": {
            "total_sessions": 0,
            "total_minutes": 0.0,
            "total_distance_miles": 0.0,
            "total_elevation_feet": 0.0,
            "workout_sessions": 0,
            "yoga_sessions": 0,
            "running_sessions": 0,
            "biking_sessions": 0
        },
        "mindfulness": {
            "total_sessions": 0,
            "total_minutes": 0.0
        },
        "music": {
            "total_sessions": 0,
            "total_minutes": 0.0,
            "guitar_sessions": 0,
            "drums_sessions": 0
        },
        "daily_breakdown": defaultdict(lambda: {
            "exercise_count": 0,
            "mindfulness_count": 0,
            "music_count": 0,
            "total_minutes": 0.0
        }),
        "habit_type_counts": defaultdict(int)
    }
    
    # Process logs - track unique sessions by (date, habit_type)
    dates_with_habits = set()
    sessions_seen = set()  # Track (date, habit_type) to count sessions correctly
    
    for log in logs:
        dates_with_habits.add(log.date)
        session_key = (log.date, log.habit_type)
        is_new_session = session_key not in sessions_seen
        
        if is_new_session:
            sessions_seen.add(session_key)
            summary["habit_type_counts"][log.habit_type] += 1
        
        # Exercise habits
        if "exercise" in log.habit_type:
            # Count session only once per (date, habit_type)
            if is_new_session:
                summary["exercise"]["total_sessions"] += 1
                if "workout" in log.habit_type:
                    summary["exercise"]["workout_sessions"] += 1
                elif "yoga" in log.habit_type:
                    summary["exercise"]["yoga_sessions"] += 1
                elif "running" in log.habit_type:
                    summary["exercise"]["running_sessions"] += 1
                elif "biking" in log.habit_type:
                    summary["exercise"]["biking_sessions"] += 1
                summary["daily_breakdown"][str(log.date)]["exercise_count"] += 1
            
            # Sum metrics (can have multiple metrics per session)
            if log.metric_name.lower() == "minutes":
                summary["exercise"]["total_minutes"] += log.value
                summary["daily_breakdown"][str(log.date)]["total_minutes"] += log.value
            elif log.metric_name.lower() == "distance":
                summary["exercise"]["total_distance_miles"] += log.value
            elif log.metric_name.lower() == "elevation":
                summary["exercise"]["total_elevation_feet"] += log.value
        
        # Mindfulness habits
        elif "mindfulness" in log.habit_type:
            if is_new_session:
                summary["mindfulness"]["total_sessions"] += 1
                summary["daily_breakdown"][str(log.date)]["mindfulness_count"] += 1
            
            if log.metric_name.lower() == "minutes":
                summary["mindfulness"]["total_minutes"] += log.value
                summary["daily_breakdown"][str(log.date)]["total_minutes"] += log.value
        
        # Music habits
        elif "music" in log.habit_type:
            if is_new_session:
                summary["music"]["total_sessions"] += 1
                summary["daily_breakdown"][str(log.date)]["music_count"] += 1
                if "guitar" in log.habit_type:
                    summary["music"]["guitar_sessions"] += 1
                elif "drums" in log.habit_type:
                    summary["music"]["drums_sessions"] += 1
            
            if log.metric_name.lower() == "minutes":
                summary["music"]["total_minutes"] += log.value
                summary["daily_breakdown"][str(log.date)]["total_minutes"] += log.value
    
    summary["total_days_with_habits"] = len(dates_with_habits)
    
    # Convert daily_breakdown to list format
    daily_list = []
    for date_str, data in sorted(summary["daily_breakdown"].items()):
        daily_list.append({
            "date": date_str,
            "exercise_count": data["exercise_count"],
            "mindfulness_count": data["mindfulness_count"],
            "music_count": data["music_count"],
            "total_minutes": data["total_minutes"]
        })
    
    summary["daily_breakdown"] = daily_list
    summary["habit_type_counts"] = dict(summary["habit_type_counts"])
    
    return summary

