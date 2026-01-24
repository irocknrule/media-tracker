import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { workoutService } from '../services/workoutService';
import { getErrorMessage } from '../utils/errorHandler';

const MUSCLE_GROUPS = [
  'Chest', 'Back', 'Legs', 'Shoulders', 'Arms', 'Core', 'Glutes',
  'Upper Back', 'Lower Back', 'Hamstrings', 'Quadriceps', 'Calves',
  'Biceps', 'Triceps', 'Forearms'
];

const CARDIO_EXERCISES = ['Running', 'Biking', 'Cycling', 'Cardio', 'Treadmill', 'Elliptical'];

function isCardioExercise(exerciseName) {
  return CARDIO_EXERCISES.some(cardio => 
    exerciseName?.toLowerCase().includes(cardio.toLowerCase())
  );
}

export default function Workouts() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('log');
  const [exercises, setExercises] = useState([]);
  const [workouts, setWorkouts] = useState([]);
  const [workoutRecords, setWorkoutRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [highlightedExerciseId, setHighlightedExerciseId] = useState(null);
  const [previousTab, setPreviousTab] = useState(null);
  const [savedLogWorkoutState, setSavedLogWorkoutState] = useState(null);

  useEffect(() => {
    if (activeTab === 'exercises' || activeTab === 'workouts' || activeTab === 'log' || activeTab === 'history') {
      loadExercises();
    }
    if (activeTab === 'workouts' || activeTab === 'log') {
      loadWorkouts();
    }
    if (activeTab === 'history') {
      loadWorkoutRecords();
    }
  }, [activeTab]);

  const loadExercises = async () => {
    try {
      setLoading(true);
      const data = await workoutService.getExercises();
      setExercises(data || []);
    } catch (err) {
      console.error('Error loading exercises:', err);
      setError(getErrorMessage(err) || 'Failed to load exercises');
    } finally {
      setLoading(false);
    }
  };

  const loadWorkouts = async () => {
    try {
      const data = await workoutService.getWorkouts();
      setWorkouts(data || []);
    } catch (err) {
      console.error('Error loading workouts:', err);
      setError(getErrorMessage(err) || 'Failed to load workouts');
    }
  };

  const loadWorkoutRecords = async (startDate = null, endDate = null) => {
    try {
      setLoading(true);
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      const data = await workoutService.getWorkoutRecords(params);
      setWorkoutRecords(data || []);
    } catch (err) {
      console.error('Error loading workout records:', err);
      setError(getErrorMessage(err) || 'Failed to load workout history');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'log', label: '💪 Log Workout', icon: '💪' },
    { id: 'history', label: '📅 History', icon: '📅' },
    { id: 'exercises', label: '🏋️ Exercises', icon: '🏋️' },
    { id: 'workouts', label: '📋 Workouts', icon: '📋' },
  ];

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <button
            onClick={() => navigate('/')}
            style={styles.homeButton}
            title="Go to Home"
          >
            🏠
          </button>
          <h1 style={styles.title}>💪 Workout Tracker</h1>
        </div>
        <div style={styles.headerActions}>
          <span style={styles.userInfo}>Welcome, {user?.username || 'User'}</span>
          <button onClick={logout} style={styles.logoutButton}>
            Logout
          </button>
        </div>
      </header>

      <div style={styles.content}>
        {/* Tab Navigation */}
        <div style={styles.tabContainer}>
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => {
                // Remember previous tab when switching to exercises
                if (tab.id === 'exercises' && activeTab !== 'exercises') {
                  setPreviousTab(activeTab);
                }
                setActiveTab(tab.id);
                setError('');
              }}
              style={{
                ...styles.tab,
                ...(activeTab === tab.id ? styles.tabActive : {}),
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {error && (
          <div style={styles.error}>
            {error}
          </div>
        )}

        {/* Tab Content */}
        {activeTab === 'log' && (
          <LogWorkoutTab
            exercises={exercises}
            workouts={workouts}
            savedState={savedLogWorkoutState}
            onStateChange={(state) => setSavedLogWorkoutState(state)}
            onWorkoutSaved={() => {
              setError('');
              loadWorkoutRecords();
              setSavedLogWorkoutState(null); // Clear saved state after saving
            }}
            onExerciseClick={(exerciseId) => {
              setPreviousTab('log');
              setHighlightedExerciseId(exerciseId);
              setActiveTab('exercises');
            }}
            setError={setError}
          />
        )}

        {activeTab === 'history' && (
          <HistoryTab
            workoutRecords={workoutRecords}
            exercises={exercises}
            loading={loading}
            onLoadRecords={loadWorkoutRecords}
            onExerciseClick={(exerciseId) => {
              setPreviousTab('history');
              setHighlightedExerciseId(exerciseId);
              setActiveTab('exercises');
            }}
            onRecordDeleted={() => {
              setError('');
              loadWorkoutRecords();
            }}
            onRecordUpdated={() => {
              setError('');
              loadWorkoutRecords();
            }}
            setError={setError}
          />
        )}

        {activeTab === 'exercises' && (
          <ExercisesTab
            exercises={exercises}
            loading={loading}
            highlightedExerciseId={highlightedExerciseId}
            previousTab={previousTab}
            onBack={() => {
              if (previousTab) {
                setActiveTab(previousTab);
                setPreviousTab(null);
              }
            }}
            onExerciseUpdated={loadExercises}
            onExerciseDeleted={loadExercises}
            onHighlightCleared={() => setHighlightedExerciseId(null)}
            setError={setError}
          />
        )}

        {activeTab === 'workouts' && (
          <WorkoutsTab
            workouts={workouts}
            exercises={exercises}
            loading={loading}
            onWorkoutUpdated={loadWorkouts}
            onWorkoutDeleted={loadWorkouts}
            setError={setError}
          />
        )}
      </div>
    </div>
  );
}

// Log Workout Tab
function LogWorkoutTab({ exercises, workouts, savedState, onStateChange, onWorkoutSaved, onExerciseClick, setError }) {
  // Initialize state from savedState if available, otherwise use defaults
  const getInitialState = () => {
    if (savedState && Object.keys(savedState).length > 0) {
      return {
        selectedWorkout: savedState.selectedWorkout || 'custom',
        workoutDate: savedState.workoutDate || new Date().toISOString().split('T')[0],
        workoutTime: savedState.workoutTime || new Date().toTimeString().slice(0, 5),
        duration: savedState.duration || 60,
        exerciseRecords: savedState.exerciseRecords || [],
        selectedWorkoutDetails: savedState.selectedWorkoutDetails || null,
        lastWorkout: savedState.lastWorkout || null,
      };
    }
    return {
      selectedWorkout: 'custom',
      workoutDate: new Date().toISOString().split('T')[0],
      workoutTime: new Date().toTimeString().slice(0, 5),
      duration: 60,
      exerciseRecords: [],
      selectedWorkoutDetails: null,
      lastWorkout: null,
    };
  };

  const initialState = getInitialState();
  const [selectedWorkout, setSelectedWorkout] = useState(initialState.selectedWorkout);
  const [workoutDate, setWorkoutDate] = useState(initialState.workoutDate);
  const [workoutTime, setWorkoutTime] = useState(initialState.workoutTime);
  const [duration, setDuration] = useState(initialState.duration);
  const [exerciseRecords, setExerciseRecords] = useState(initialState.exerciseRecords);
  const [selectedWorkoutDetails, setSelectedWorkoutDetails] = useState(initialState.selectedWorkoutDetails);
  const [lastWorkout, setLastWorkout] = useState(initialState.lastWorkout);
  const [saving, setSaving] = useState(false);
  const [hasRestored, setHasRestored] = useState(!!savedState && Object.keys(savedState).length > 0);
  const [isRestoring, setIsRestoring] = useState(false);

  // Save state whenever it changes (but not when restoring or on initial restore)
  useEffect(() => {
    if (isRestoring) {
      setIsRestoring(false);
      return;
    }
    
    // Don't save on initial mount if we restored from savedState
    if (!hasRestored && savedState && Object.keys(savedState).length > 0) {
      setHasRestored(true);
      return;
    }
    
    const currentState = {
      selectedWorkout,
      workoutDate,
      workoutTime,
      duration,
      exerciseRecords,
      selectedWorkoutDetails,
      lastWorkout,
    };
    if (onStateChange) {
      onStateChange(currentState);
    }
  }, [selectedWorkout, workoutDate, workoutTime, duration, exerciseRecords, selectedWorkoutDetails, lastWorkout, onStateChange, isRestoring, hasRestored, savedState]);

  // Restore state when component mounts or savedState is provided
  useEffect(() => {
    if (savedState && Object.keys(savedState).length > 0) {
      // Check if we need to restore (state is different from current)
      const needsRestore = 
        savedState.selectedWorkout !== selectedWorkout ||
        savedState.workoutDate !== workoutDate ||
        savedState.workoutTime !== workoutTime ||
        savedState.duration !== duration ||
        (savedState.exerciseRecords && savedState.exerciseRecords.length !== exerciseRecords.length);
      
      if (needsRestore) {
        setIsRestoring(true);
        setSelectedWorkout(savedState.selectedWorkout || 'custom');
        setWorkoutDate(savedState.workoutDate || new Date().toISOString().split('T')[0]);
        setWorkoutTime(savedState.workoutTime || new Date().toTimeString().slice(0, 5));
        setDuration(savedState.duration || 60);
        if (savedState.exerciseRecords && savedState.exerciseRecords.length > 0) {
          setExerciseRecords(savedState.exerciseRecords);
        }
        if (savedState.selectedWorkoutDetails) {
          setSelectedWorkoutDetails(savedState.selectedWorkoutDetails);
        }
        if (savedState.lastWorkout) {
          setLastWorkout(savedState.lastWorkout);
        }
        setHasRestored(true);
        
        // Reload workout details if a workout was selected and we don't have details
        if (savedState.selectedWorkout && savedState.selectedWorkout !== 'custom' && !savedState.selectedWorkoutDetails) {
          loadWorkoutDetailsFromState(savedState.selectedWorkout);
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [savedState]);

  const loadWorkoutDetailsFromState = async (workoutId) => {
    try {
      const workout = workouts.find(w => w.id === parseInt(workoutId));
      if (!workout) return;

      const details = await workoutService.getWorkout(workout.id);
      setSelectedWorkoutDetails(details);

      // Try to load last workout
      try {
        const last = await workoutService.getLastWorkoutRecord(workout.id);
        setLastWorkout(last);
      } catch (err) {
        setLastWorkout(null);
      }
    } catch (err) {
      // Silently fail
    }
  };

  useEffect(() => {
    // Don't reload if we're in the middle of restoring state
    if (isRestoring) return;
    
    if (selectedWorkout !== 'custom') {
      loadWorkoutDetails();
    } else {
      setSelectedWorkoutDetails(null);
      setLastWorkout(null);
      // Only clear exercise records if we're not restoring from saved state
      if (!savedState || !savedState.exerciseRecords || savedState.exerciseRecords.length === 0) {
        // Only clear if exerciseRecords is empty to avoid clearing restored data
        if (exerciseRecords.length === 0) {
          setExerciseRecords([]);
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedWorkout, isRestoring]);

  const loadWorkoutDetails = async () => {
    try {
      const workout = workouts.find(w => w.id === parseInt(selectedWorkout));
      if (!workout) return;

      const details = await workoutService.getWorkout(workout.id);
      setSelectedWorkoutDetails(details);

      // Pre-populate exercises
      if (details.exercises && details.exercises.length > 0) {
        const records = details.exercises.map(ex => ({
          exercise_id: ex.exercise_id,
          exercise_name: ex.exercise_name,
          sets: isCardioExercise(ex.exercise_name) ? null : 3,
          reps: isCardioExercise(ex.exercise_name) ? null : 10,
          weight: isCardioExercise(ex.exercise_name) ? null : 0,
          time_seconds: isCardioExercise(ex.exercise_name) ? null : null,
          distance: isCardioExercise(ex.exercise_name) ? null : null,
          distance_unit: isCardioExercise(ex.exercise_name) ? 'mi' : null,
        }));
        setExerciseRecords(records);
      }

      // Try to load last workout
      try {
        const last = await workoutService.getLastWorkoutRecord(workout.id);
        setLastWorkout(last);
      } catch (err) {
        // No previous workout, that's okay
        setLastWorkout(null);
      }
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to load workout details');
    }
  };

  const addExercise = () => {
    setExerciseRecords([
      ...exerciseRecords,
      {
        exercise_id: null,
        exercise_name: '',
        sets: 3,
        reps: 10,
        weight: 0,
        time_seconds: null,
        distance: null,
        distance_unit: 'mi',
      },
    ]);
  };

  const removeExercise = (index) => {
    setExerciseRecords(exerciseRecords.filter((_, i) => i !== index));
  };

  const updateExerciseRecord = (index, field, value) => {
    const updated = [...exerciseRecords];
    updated[index] = { ...updated[index], [field]: value };
    
    // Update exercise_name when exercise_id changes
    if (field === 'exercise_id') {
      const exercise = exercises.find(e => e.id === parseInt(value));
      if (exercise) {
        updated[index].exercise_name = exercise.name;
        const isCardio = isCardioExercise(exercise.name);
        if (isCardio) {
          updated[index].sets = null;
          updated[index].reps = null;
          updated[index].weight = null;
          updated[index].time_seconds = null;
          updated[index].distance = null;
          updated[index].distance_unit = 'mi';
        } else {
          updated[index].time_seconds = null;
          updated[index].distance = null;
          updated[index].distance_unit = null;
        }
      }
    }
    
    setExerciseRecords(updated);
  };

  const handleSave = async (index = null) => {
    if (exerciseRecords.length === 0) {
      setError('Please add at least one exercise');
      return;
    }

    setSaving(true);
    try {
      const workoutDateTime = new Date(`${workoutDate}T${workoutTime}`);
      const workout = selectedWorkout !== 'custom' 
        ? workouts.find(w => w.id === parseInt(selectedWorkout))
        : null;

      const recordsToSave = index !== null 
        ? [exerciseRecords[index]]
        : exerciseRecords.filter(er => er.exercise_id);

      const workoutData = {
        workout_id: workout?.id || null,
        workout_name: workout?.name || 'Custom Workout',
        workout_date: workoutDateTime.toISOString(),
        duration_minutes: duration,
        exercises: recordsToSave.map(er => ({
          exercise_id: er.exercise_id,
          sets: er.sets || null,
          reps: er.reps || null,
          weight: er.weight || null,
          weight_unit: 'lbs',
          time_seconds: er.time_seconds || null,
          distance: er.distance || null,
          distance_unit: er.distance_unit || null,
          notes: null,
        })),
      };

      await workoutService.createWorkoutRecord(workoutData);
      
      if (index !== null) {
        // Individual save - remove that exercise
        setExerciseRecords(exerciseRecords.filter((_, i) => i !== index));
      } else {
        // Full save - clear all
        setExerciseRecords([]);
        setSelectedWorkout('custom');
      }
      
      onWorkoutSaved();
      setError('');
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to save workout');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={styles.tabContent}>
      <h2 style={styles.sectionTitle}>Log Workout</h2>

      <div style={styles.formSection}>
        <div style={styles.formRow}>
          <div style={styles.formGroup}>
            <label>Select Workout</label>
            <select
              value={selectedWorkout}
              onChange={(e) => setSelectedWorkout(e.target.value)}
              style={styles.select}
            >
              <option value="custom">Custom Workout</option>
              {workouts.map(w => (
                <option key={w.id} value={w.id}>{w.name}</option>
              ))}
            </select>
          </div>

          <div style={styles.formGroup}>
            <label>Workout Date</label>
            <input
              type="date"
              value={workoutDate}
              onChange={(e) => setWorkoutDate(e.target.value)}
              style={styles.input}
            />
          </div>

          <div style={styles.formGroup}>
            <label>Time</label>
            <input
              type="time"
              value={workoutTime}
              onChange={(e) => setWorkoutTime(e.target.value)}
              style={styles.input}
            />
          </div>

          <div style={styles.formGroup}>
            <label>Duration (min)</label>
            <input
              type="number"
              value={duration}
              onChange={(e) => setDuration(parseInt(e.target.value) || 0)}
              min="0"
              style={styles.input}
            />
          </div>
        </div>

        {selectedWorkoutDetails && (
          <div style={styles.infoBox}>
            <strong>{selectedWorkoutDetails.name}</strong> includes {selectedWorkoutDetails.exercises?.length || 0} exercises
          </div>
        )}

        {lastWorkout && (
          <div style={styles.lastWorkoutSection}>
            <h3>📊 Last Workout History</h3>
            <p style={styles.caption}>
              Last performed: {new Date(lastWorkout.workout_date).toLocaleString()}
            </p>
            {lastWorkout.exercises && lastWorkout.exercises.length > 0 && (
              <div style={styles.lastWorkoutList}>
                {lastWorkout.exercises.map((ex, idx) => (
                  <div key={idx} style={styles.lastWorkoutItem}>
                    <strong>{ex.exercise_name}</strong>
                    {ex.sets && ex.reps && ex.weight ? (
                      <span>{ex.sets} × {ex.reps} @ {ex.weight} lbs</span>
                    ) : ex.time_seconds ? (
                      <span>{Math.floor(ex.time_seconds / 60)} min</span>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div style={styles.exercisesSection}>
        <div style={styles.exercisesHeader}>
          <h3>📝 Log Exercises</h3>
          <button onClick={addExercise} style={styles.addButton}>
            ➕ Add Exercise
          </button>
        </div>

        {exerciseRecords.map((record, index) => {
          const exercise = exercises.find(e => e.id === record.exercise_id);
          const isCardio = isCardioExercise(record.exercise_name);

          return (
            <div key={index} style={styles.exerciseCard}>
              <div style={styles.exerciseRow}>
                <div style={{ ...styles.formGroup, flex: 2 }}>
                  <label>Exercise</label>
                  <select
                    value={record.exercise_id || ''}
                    onChange={(e) => updateExerciseRecord(index, 'exercise_id', e.target.value)}
                    style={styles.select}
                  >
                    <option value="">Select exercise...</option>
                    {exercises.map(ex => (
                      <option key={ex.id} value={ex.id}>{ex.name}</option>
                    ))}
                  </select>
                  {record.exercise_id && record.exercise_name && (
                    <div style={styles.exerciseLinkContainer}>
                      <button
                        onClick={(e) => {
                          if (e.ctrlKey || e.metaKey) {
                            // Open in new tab
                            e.preventDefault();
                            const url = `${window.location.origin}${window.location.pathname}?tab=exercises&exercise=${record.exercise_id}`;
                            window.open(url, '_blank');
                          } else if (onExerciseClick) {
                            onExerciseClick(record.exercise_id);
                          }
                        }}
                        style={styles.exerciseLink}
                        type="button"
                        title="Click to view details, Ctrl/Cmd+Click to open in new tab"
                      >
                        🔗 {record.exercise_name}
                      </button>
                    </div>
                  )}
                </div>

                {isCardio ? (
                  <>
                    <div style={styles.formGroup}>
                      <label>Time (min)</label>
                      <input
                        type="number"
                        value={record.time_seconds ? Math.floor(record.time_seconds / 60) : ''}
                        onChange={(e) => updateExerciseRecord(index, 'time_seconds', (parseFloat(e.target.value) || 0) * 60)}
                        min="0"
                        step="1"
                        style={styles.input}
                      />
                    </div>
                    <div style={styles.formGroup}>
                      <label>Distance (mi)</label>
                      <input
                        type="number"
                        value={record.distance || ''}
                        onChange={(e) => updateExerciseRecord(index, 'distance', parseFloat(e.target.value) || null)}
                        min="0"
                        step="0.1"
                        style={styles.input}
                      />
                    </div>
                    <div style={styles.formGroup}>
                      <button
                        onClick={() => handleSave(index)}
                        disabled={!record.exercise_id || saving}
                        style={styles.saveButton}
                      >
                        💾
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div style={styles.formGroup}>
                      <label>Sets</label>
                      <input
                        type="number"
                        value={record.sets || ''}
                        onChange={(e) => updateExerciseRecord(index, 'sets', parseInt(e.target.value) || null)}
                        min="1"
                        style={styles.input}
                      />
                    </div>
                    <div style={styles.formGroup}>
                      <label>Reps</label>
                      <input
                        type="number"
                        value={record.reps || ''}
                        onChange={(e) => updateExerciseRecord(index, 'reps', parseInt(e.target.value) || null)}
                        min="1"
                        style={styles.input}
                      />
                    </div>
                    <div style={styles.formGroup}>
                      <label>Weight (lbs)</label>
                      <input
                        type="number"
                        value={record.weight || ''}
                        onChange={(e) => updateExerciseRecord(index, 'weight', parseFloat(e.target.value) || null)}
                        min="0"
                        step="2.5"
                        style={styles.input}
                      />
                    </div>
                    <div style={styles.formGroup}>
                      <button
                        onClick={() => handleSave(index)}
                        disabled={!record.exercise_id || saving}
                        style={styles.saveButton}
                      >
                        💾
                      </button>
                    </div>
                  </>
                )}

                <div style={styles.formGroup}>
                  <button
                    onClick={() => removeExercise(index)}
                    style={styles.removeButton}
                  >
                    ❌
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {exerciseRecords.length > 0 && (
        <div style={styles.saveAllSection}>
          <button
            onClick={() => handleSave()}
            disabled={saving || exerciseRecords.filter(er => er.exercise_id).length === 0}
            style={styles.saveAllButton}
          >
            {saving ? 'Saving...' : '💾 Save All Exercises'}
          </button>
        </div>
      )}
    </div>
  );
}

// Continue with other tab components...

// History Tab
function HistoryTab({ workoutRecords, exercises, loading, onLoadRecords, onExerciseClick, onRecordDeleted, onRecordUpdated, setError }) {
  const [startDate, setStartDate] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() - 90);
    return date.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [editingId, setEditingId] = useState(null);
  const [editFormData, setEditFormData] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    onLoadRecords(startDate, endDate);
  }, [startDate, endDate]);

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this workout?')) return;
    
    try {
      await workoutService.deleteWorkoutRecord(id);
      onRecordDeleted();
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to delete workout');
    }
  };

  const handleEdit = (record) => {
    const workoutDateTime = new Date(record.workout_date);
    const workoutDate = workoutDateTime.toISOString().split('T')[0];
    const workoutTime = workoutDateTime.toTimeString().slice(0, 5);
    
    setEditFormData({
      id: record.id,
      workout_id: record.workout_id,
      workout_name: record.workout_name,
      workout_date: workoutDate,
      workout_time: workoutTime,
      duration_minutes: record.duration_minutes || 60,
      notes: record.notes || '',
      exercises: record.exercises ? record.exercises.map(ex => ({
        id: ex.id,
        exercise_id: ex.exercise_id,
        exercise_name: ex.exercise_name,
        sets: ex.sets,
        reps: ex.reps,
        weight: ex.weight,
        time_seconds: ex.time_seconds,
        distance: ex.distance,
        distance_unit: ex.distance_unit || 'mi',
      })) : [],
    });
    setEditingId(record.id);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditFormData(null);
  };

  const updateExerciseRecord = (index, field, value) => {
    const updated = [...editFormData.exercises];
    updated[index] = { ...updated[index], [field]: value };
    
    if (field === 'exercise_id') {
      const exercise = exercises.find(e => e.id === parseInt(value));
      if (exercise) {
        updated[index].exercise_name = exercise.name;
        const isCardio = isCardioExercise(exercise.name);
        if (isCardio) {
          updated[index].sets = null;
          updated[index].reps = null;
          updated[index].weight = null;
          updated[index].time_seconds = null;
          updated[index].distance = null;
          updated[index].distance_unit = 'mi';
        } else {
          updated[index].time_seconds = null;
          updated[index].distance = null;
          updated[index].distance_unit = null;
        }
      }
    }
    
    setEditFormData({ ...editFormData, exercises: updated });
  };

  const addExercise = () => {
    setEditFormData({
      ...editFormData,
      exercises: [
        ...editFormData.exercises,
        {
          exercise_id: null,
          exercise_name: '',
          sets: 3,
          reps: 10,
          weight: 0,
          time_seconds: null,
          distance: null,
          distance_unit: 'mi',
        },
      ],
    });
  };

  const removeExercise = (index) => {
    setEditFormData({
      ...editFormData,
      exercises: editFormData.exercises.filter((_, i) => i !== index),
    });
  };

  const handleSaveEdit = async () => {
    if (!editFormData.exercises || editFormData.exercises.length === 0) {
      setError('Please add at least one exercise');
      return;
    }

    setSaving(true);
    try {
      const workoutDateTime = new Date(`${editFormData.workout_date}T${editFormData.workout_time}`);
      
      // Delete old record
      await workoutService.deleteWorkoutRecord(editFormData.id);
      
      // Create new record with updated data
      const workoutData = {
        workout_id: editFormData.workout_id,
        workout_name: editFormData.workout_name,
        workout_date: workoutDateTime.toISOString(),
        duration_minutes: editFormData.duration_minutes,
        notes: editFormData.notes || null,
        exercises: editFormData.exercises
          .filter(er => er.exercise_id)
          .map(er => ({
            exercise_id: er.exercise_id,
            sets: er.sets || null,
            reps: er.reps || null,
            weight: er.weight || null,
            weight_unit: 'lbs',
            time_seconds: er.time_seconds || null,
            distance: er.distance || null,
            distance_unit: er.distance_unit || null,
            notes: null,
          })),
      };

      await workoutService.createWorkoutRecord(workoutData);
      
      setEditingId(null);
      setEditFormData(null);
      onRecordUpdated();
      setError('');
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to update workout');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={styles.tabContent}>
      <h2 style={styles.sectionTitle}>Workout History</h2>

      <div style={styles.formRow}>
        <div style={styles.formGroup}>
          <label>From</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            style={styles.input}
          />
        </div>
        <div style={styles.formGroup}>
          <label>To</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            style={styles.input}
          />
        </div>
      </div>

      {loading ? (
        <div style={styles.loading}>Loading...</div>
      ) : workoutRecords.length > 0 ? (
        <div style={styles.success}>
          Found {workoutRecords.length} workouts
        </div>
      ) : (
        <div style={styles.info}>No workouts found in the selected date range.</div>
      )}

      <div style={styles.recordsList}>
        {workoutRecords.map(record => {
          const isEditing = editingId === record.id;
          
          if (isEditing && editFormData) {
            return (
              <div key={record.id} style={styles.recordCard}>
                <h3>✏️ Edit Workout</h3>
                
                <div style={styles.formRow}>
                  <div style={styles.formGroup}>
                    <label>Workout Name</label>
                    <input
                      type="text"
                      value={editFormData.workout_name}
                      onChange={(e) => setEditFormData({ ...editFormData, workout_name: e.target.value })}
                      style={styles.input}
                    />
                  </div>
                  <div style={styles.formGroup}>
                    <label>Workout Date</label>
                    <input
                      type="date"
                      value={editFormData.workout_date}
                      onChange={(e) => setEditFormData({ ...editFormData, workout_date: e.target.value })}
                      style={styles.input}
                    />
                  </div>
                  <div style={styles.formGroup}>
                    <label>Time</label>
                    <input
                      type="time"
                      value={editFormData.workout_time}
                      onChange={(e) => setEditFormData({ ...editFormData, workout_time: e.target.value })}
                      style={styles.input}
                    />
                  </div>
                  <div style={styles.formGroup}>
                    <label>Duration (min)</label>
                    <input
                      type="number"
                      value={editFormData.duration_minutes}
                      onChange={(e) => setEditFormData({ ...editFormData, duration_minutes: parseInt(e.target.value) || 0 })}
                      min="0"
                      style={styles.input}
                    />
                  </div>
                </div>

                <div style={styles.formGroup}>
                  <label>Notes</label>
                  <textarea
                    value={editFormData.notes}
                    onChange={(e) => setEditFormData({ ...editFormData, notes: e.target.value })}
                    style={{ ...styles.input, minHeight: '80px' }}
                  />
                </div>

                <div style={styles.exercisesSection}>
                  <div style={styles.exercisesHeader}>
                    <h4>Exercises</h4>
                    <button onClick={addExercise} style={styles.addButton}>
                      ➕ Add Exercise
                    </button>
                  </div>

                  {editFormData.exercises.map((exerciseRecord, index) => {
                    const exercise = exercises.find(e => e.id === exerciseRecord.exercise_id);
                    const isCardio = isCardioExercise(exerciseRecord.exercise_name);

                    return (
                      <div key={index} style={styles.exerciseCard}>
                        <div style={styles.exerciseRow}>
                          <div style={{ ...styles.formGroup, flex: 2 }}>
                            <label>Exercise</label>
                            <select
                              value={exerciseRecord.exercise_id || ''}
                              onChange={(e) => updateExerciseRecord(index, 'exercise_id', e.target.value)}
                              style={styles.select}
                            >
                              <option value="">Select exercise...</option>
                              {exercises.map(ex => (
                                <option key={ex.id} value={ex.id}>{ex.name}</option>
                              ))}
                            </select>
                            {exerciseRecord.exercise_id && exerciseRecord.exercise_name && (
                              <div style={styles.exerciseLinkContainer}>
                                <button
                                  onClick={(e) => {
                                    if (e.ctrlKey || e.metaKey) {
                                      // Open in new tab
                                      e.preventDefault();
                                      const url = `${window.location.origin}${window.location.pathname}?tab=exercises&exercise=${exerciseRecord.exercise_id}`;
                                      window.open(url, '_blank');
                                    } else if (onExerciseClick) {
                                      onExerciseClick(exerciseRecord.exercise_id);
                                    }
                                  }}
                                  style={styles.exerciseLink}
                                  type="button"
                                  title="Click to view details, Ctrl/Cmd+Click to open in new tab"
                                >
                                  🔗 {exerciseRecord.exercise_name}
                                </button>
                              </div>
                            )}
                          </div>

                          {isCardio ? (
                            <>
                              <div style={styles.formGroup}>
                                <label>Time (min)</label>
                                <input
                                  type="number"
                                  value={exerciseRecord.time_seconds ? Math.floor(exerciseRecord.time_seconds / 60) : ''}
                                  onChange={(e) => updateExerciseRecord(index, 'time_seconds', (parseFloat(e.target.value) || 0) * 60)}
                                  min="0"
                                  step="1"
                                  style={styles.input}
                                />
                              </div>
                              <div style={styles.formGroup}>
                                <label>Distance (mi)</label>
                                <input
                                  type="number"
                                  value={exerciseRecord.distance || ''}
                                  onChange={(e) => updateExerciseRecord(index, 'distance', parseFloat(e.target.value) || null)}
                                  min="0"
                                  step="0.1"
                                  style={styles.input}
                                />
                              </div>
                            </>
                          ) : (
                            <>
                              <div style={styles.formGroup}>
                                <label>Sets</label>
                                <input
                                  type="number"
                                  value={exerciseRecord.sets || ''}
                                  onChange={(e) => updateExerciseRecord(index, 'sets', parseInt(e.target.value) || null)}
                                  min="1"
                                  style={styles.input}
                                />
                              </div>
                              <div style={styles.formGroup}>
                                <label>Reps</label>
                                <input
                                  type="number"
                                  value={exerciseRecord.reps || ''}
                                  onChange={(e) => updateExerciseRecord(index, 'reps', parseInt(e.target.value) || null)}
                                  min="1"
                                  style={styles.input}
                                />
                              </div>
                              <div style={styles.formGroup}>
                                <label>Weight (lbs)</label>
                                <input
                                  type="number"
                                  value={exerciseRecord.weight || ''}
                                  onChange={(e) => updateExerciseRecord(index, 'weight', parseFloat(e.target.value) || null)}
                                  min="0"
                                  step="2.5"
                                  style={styles.input}
                                />
                              </div>
                            </>
                          )}

                          <div style={styles.formGroup}>
                            <button
                              onClick={() => removeExercise(index)}
                              style={styles.removeButton}
                            >
                              ❌
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div style={styles.actionButtons}>
                  <button
                    onClick={handleSaveEdit}
                    disabled={saving}
                    style={styles.saveAllButton}
                  >
                    {saving ? 'Saving...' : '💾 Save Changes'}
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    disabled={saving}
                    style={styles.cancelButton}
                  >
                    ❌ Cancel
                  </button>
                </div>
              </div>
            );
          }

          return (
            <div key={record.id} style={styles.recordCard}>
              <div style={styles.recordHeader}>
                <h3>{record.workout_name}</h3>
                <span style={styles.recordDate}>
                  {new Date(record.workout_date).toLocaleString()}
                </span>
              </div>
              {record.duration_minutes && (
                <p style={styles.caption}>Duration: {record.duration_minutes} minutes</p>
              )}
              {record.notes && (
                <div style={styles.infoBox}>{record.notes}</div>
              )}
              <div style={styles.exercisesList}>
                <strong>Exercises:</strong>
                {record.exercises && record.exercises.map((ex, idx) => (
                  <div key={idx} style={styles.exerciseItem}>
                    <button
                      onClick={(e) => {
                        if (e.ctrlKey || e.metaKey) {
                          // Open in new tab
                          e.preventDefault();
                          const url = `${window.location.origin}${window.location.pathname}?tab=exercises&exercise=${ex.exercise_id}`;
                          window.open(url, '_blank');
                        } else if (onExerciseClick) {
                          onExerciseClick(ex.exercise_id);
                        }
                      }}
                      style={styles.exerciseLink}
                      type="button"
                      title="Click to view details, Ctrl/Cmd+Click to open in new tab"
                    >
                      <strong>{ex.exercise_name}</strong>
                    </button>
                    {ex.sets && ex.reps && ex.weight ? (
                      <span>{ex.sets} × {ex.reps} @ {ex.weight} lbs</span>
                    ) : ex.time_seconds ? (
                      <span>{Math.floor(ex.time_seconds / 60)} min</span>
                    ) : null}
                  </div>
                ))}
              </div>
              <div style={styles.actionButtons}>
                <button
                  onClick={() => handleEdit(record)}
                  style={styles.editButton}
                >
                  ✏️ Edit
                </button>
                <button
                  onClick={() => handleDelete(record.id)}
                  style={styles.deleteButton}
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Exercises Tab
function ExercisesTab({ exercises, loading, highlightedExerciseId, previousTab, onBack, onExerciseUpdated, onExerciseDeleted, onHighlightCleared, setError }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [muscleFilter, setMuscleFilter] = useState('All');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [expandedIds, setExpandedIds] = useState(new Set());

  // Auto-expand highlighted exercise when tab becomes active
  useEffect(() => {
    if (highlightedExerciseId) {
      const newExpanded = new Set(expandedIds);
      newExpanded.add(highlightedExerciseId);
      setExpandedIds(newExpanded);
      
      // Scroll to the exercise card after a short delay to ensure it's rendered
      setTimeout(() => {
        const element = document.getElementById(`exercise-${highlightedExerciseId}`);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 100);
      
      // Clear highlight after expanding
      if (onHighlightCleared) {
        onHighlightCleared();
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [highlightedExerciseId]);
  const [formData, setFormData] = useState({
    name: '',
    primary_muscle: '',
    secondary_muscles: '',
    notes: '',
    image_url: '',
  });
  const [imageFile, setImageFile] = useState(null);
  const [saving, setSaving] = useState(false);

  const filteredExercises = exercises.filter(ex => {
    const matchesSearch = !searchTerm || ex.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesMuscle = muscleFilter === 'All' || ex.primary_muscle === muscleFilter;
    return matchesSearch && matchesMuscle;
  });

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (!file) {
      setImageFile(null);
      return;
    }

    if (!['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'].includes(file.type)) {
      setError('Please upload a valid image file (PNG, JPG, GIF, or WebP)');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError('Image file size must be less than 5MB');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      setImageFile(e.target.result);
      setFormData({ ...formData, image_url: e.target.result });
    };
    reader.onerror = () => {
      setError('Failed to read image file');
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError('Please enter an exercise name');
      return;
    }

    setSaving(true);
    try {
      const exerciseData = {
        name: formData.name,
        primary_muscle: formData.primary_muscle || null,
        secondary_muscles: formData.secondary_muscles || null,
        notes: formData.notes || null,
        image_url: imageFile || formData.image_url || null,
      };

      if (editingId) {
        await workoutService.updateExercise(editingId, exerciseData);
        setEditingId(null);
      } else {
        await workoutService.createExercise(exerciseData);
      }

      setFormData({ name: '', primary_muscle: '', secondary_muscles: '', notes: '', image_url: '' });
      setImageFile(null);
      setShowAddForm(false);
      onExerciseUpdated();
      setError('');
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to save exercise');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this exercise?')) return;
    
    try {
      await workoutService.deleteExercise(id);
      onExerciseDeleted();
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to delete exercise');
    }
  };

  const startEdit = (exercise) => {
    setEditingId(exercise.id);
    setFormData({
      name: exercise.name,
      primary_muscle: exercise.primary_muscle || '',
      secondary_muscles: exercise.secondary_muscles || '',
      notes: exercise.notes || '',
      image_url: exercise.image_url || '',
    });
    setImageFile(null);
    setShowAddForm(true);
  };

  const toggleExpand = (id) => {
    const newExpanded = new Set(expandedIds);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedIds(newExpanded);
  };

  return (
    <div style={styles.tabContent}>
      <div style={styles.sectionHeader}>
        <div style={styles.sectionHeaderLeft}>
          {previousTab && (
            <button
              onClick={onBack}
              style={styles.backButton}
            >
              ← Back to {previousTab === 'log' ? 'Log Workout' : 'Workout History'}
            </button>
          )}
          <h2 style={styles.sectionTitle}>Exercise Library</h2>
        </div>
        <button
          onClick={() => {
            setShowAddForm(!showAddForm);
            setEditingId(null);
            setFormData({ name: '', primary_muscle: '', secondary_muscles: '', notes: '', image_url: '' });
            setImageFile(null);
          }}
          style={styles.addButton}
        >
          {showAddForm ? '❌ Cancel' : '➕ Add Exercise'}
        </button>
      </div>

      {showAddForm && (
        <form onSubmit={handleSubmit} style={styles.formCard}>
          <h3>{editingId ? 'Edit Exercise' : 'Add New Exercise'}</h3>
          
          <div style={styles.formGroup}>
            <label>Exercise Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Barbell Squat"
              style={styles.input}
              required
            />
          </div>

          <div style={styles.formGroup}>
            <label>Primary Muscle Group</label>
            <select
              value={formData.primary_muscle}
              onChange={(e) => setFormData({ ...formData, primary_muscle: e.target.value })}
              style={styles.select}
            >
              <option value="">Select muscle group...</option>
              {MUSCLE_GROUPS.map(muscle => (
                <option key={muscle} value={muscle}>{muscle}</option>
              ))}
            </select>
          </div>

          <div style={styles.formGroup}>
            <label>Secondary Muscles (comma-separated)</label>
            <input
              type="text"
              value={formData.secondary_muscles}
              onChange={(e) => setFormData({ ...formData, secondary_muscles: e.target.value })}
              placeholder="e.g., Core, Lower Back"
              style={styles.input}
            />
          </div>

          <div style={styles.formGroup}>
            <label>Notes / Form Cues</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              placeholder="Tips for proper form..."
              style={{ ...styles.input, minHeight: '100px' }}
            />
          </div>

          <div style={styles.formGroup}>
            <label>Exercise Image/GIF</label>
            <input
              type="file"
              accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
              onChange={handleImageUpload}
              style={styles.input}
            />
            {imageFile && (
              <img src={imageFile} alt="Preview" style={{ maxWidth: '200px', marginTop: '0.5rem', borderRadius: '4px' }} />
            )}
            {!imageFile && formData.image_url && (
              <img src={formData.image_url} alt="Current" style={{ maxWidth: '200px', marginTop: '0.5rem', borderRadius: '4px' }} />
            )}
          </div>

          <button type="submit" disabled={saving} style={styles.saveAllButton}>
            {saving ? 'Saving...' : editingId ? '💾 Update Exercise' : '💾 Add Exercise'}
          </button>
        </form>
      )}

      <div style={styles.filterSection}>
        <div style={{ ...styles.formGroup, flex: 2 }}>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search exercises..."
            style={styles.input}
          />
        </div>
        <div style={styles.formGroup}>
          <select
            value={muscleFilter}
            onChange={(e) => setMuscleFilter(e.target.value)}
            style={styles.select}
          >
            <option value="All">All Muscles</option>
            {MUSCLE_GROUPS.map(muscle => (
              <option key={muscle} value={muscle}>{muscle}</option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div style={styles.loading}>Loading...</div>
      ) : filteredExercises.length > 0 ? (
        <div style={styles.success}>Found {filteredExercises.length} exercises</div>
      ) : (
        <div style={styles.info}>No exercises found. Add some exercises to get started!</div>
      )}

      <div style={styles.exercisesGrid}>
        {filteredExercises.map(exercise => {
          const isExpanded = expandedIds.has(exercise.id);
          const isHighlighted = highlightedExerciseId === exercise.id;
          return (
            <div 
              key={exercise.id} 
              id={`exercise-${exercise.id}`}
              style={{
                ...styles.exerciseLibraryCard,
                ...(isHighlighted ? styles.highlightedCard : {}),
              }}
            >
              <div style={styles.exerciseLibraryHeader}>
                <div>
                  <h3>{exercise.name}</h3>
                  {exercise.primary_muscle && (
                    <span style={styles.muscleTag}>{exercise.primary_muscle}</span>
                  )}
                </div>
                <button
                  onClick={() => toggleExpand(exercise.id)}
                  style={styles.toggleButton}
                >
                  {isExpanded ? '▼' : '▶'}
                </button>
              </div>

              {isExpanded && (
                <div style={styles.exerciseLibraryDetails}>
                  {exercise.image_url && (
                    <img
                      src={exercise.image_url}
                      alt={exercise.name}
                      style={styles.exerciseImage}
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  )}
                  
                  <div style={styles.exerciseInfo}>
                    {exercise.primary_muscle && (
                      <p><strong>Primary Muscle:</strong> {exercise.primary_muscle}</p>
                    )}
                    {exercise.secondary_muscles && (
                      <p><strong>Secondary Muscles:</strong> {exercise.secondary_muscles}</p>
                    )}
                    {exercise.notes && (
                      <div>
                        <strong>Notes:</strong>
                        <p style={styles.notesText}>{exercise.notes}</p>
                      </div>
                    )}
                    
                    <div style={styles.actionButtons}>
                      <button
                        onClick={() => startEdit(exercise)}
                        style={styles.editButton}
                      >
                        ✏️ Edit
                      </button>
                      <button
                        onClick={() => handleDelete(exercise.id)}
                        style={styles.deleteButton}
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Workouts Tab
function WorkoutsTab({ workouts, exercises, loading, onWorkoutUpdated, onWorkoutDeleted, setError }) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [expandedIds, setExpandedIds] = useState(new Set());
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    exercise_ids: [],
  });
  const [workoutDetails, setWorkoutDetails] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    // Load details for all workouts
    const loadDetails = async () => {
      const details = {};
      for (const workout of workouts) {
        try {
          const detail = await workoutService.getWorkout(workout.id);
          details[workout.id] = detail;
        } catch (err) {
          console.error(`Failed to load workout ${workout.id}:`, err);
        }
      }
      setWorkoutDetails(details);
    };
    if (workouts.length > 0) {
      loadDetails();
    }
  }, [workouts]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError('Please enter a workout name');
      return;
    }
    if (formData.exercise_ids.length === 0) {
      setError('Please select at least one exercise');
      return;
    }

    setSaving(true);
    try {
      const workoutData = {
        name: formData.name,
        description: formData.description || null,
        exercise_ids: formData.exercise_ids,
      };

      if (editingId) {
        await workoutService.updateWorkout(editingId, workoutData);
        setEditingId(null);
      } else {
        await workoutService.createWorkout(workoutData);
      }

      setFormData({ name: '', description: '', exercise_ids: [] });
      setShowAddForm(false);
      onWorkoutUpdated();
      setError('');
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to save workout');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this workout template?')) return;
    
    try {
      await workoutService.deleteWorkout(id);
      onWorkoutDeleted();
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to delete workout');
    }
  };

  const startEdit = async (workout) => {
    try {
      const detail = await workoutService.getWorkout(workout.id);
      setEditingId(workout.id);
      setFormData({
        name: workout.name,
        description: workout.description || '',
        exercise_ids: detail.exercises?.map(ex => ex.exercise_id) || [],
      });
      setShowAddForm(true);
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to load workout details');
    }
  };

  const toggleExpand = (id) => {
    const newExpanded = new Set(expandedIds);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedIds(newExpanded);
  };

  return (
    <div style={styles.tabContent}>
      <div style={styles.sectionHeader}>
        <h2 style={styles.sectionTitle}>Workout Templates</h2>
        <button
          onClick={() => {
            setShowAddForm(!showAddForm);
            setEditingId(null);
            setFormData({ name: '', description: '', exercise_ids: [] });
          }}
          style={styles.addButton}
        >
          {showAddForm ? '❌ Cancel' : '➕ Create Workout'}
        </button>
      </div>

      {showAddForm && (
        <form onSubmit={handleSubmit} style={styles.formCard}>
          <h3>{editingId ? 'Edit Workout Template' : 'Create New Workout Template'}</h3>
          
          <div style={styles.formGroup}>
            <label>Workout Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Upper Body Push"
              style={styles.input}
              required
            />
          </div>

          <div style={styles.formGroup}>
            <label>Description (optional)</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Workout notes..."
              style={{ ...styles.input, minHeight: '80px' }}
            />
          </div>

          <div style={styles.formGroup}>
            <label>Select Exercises *</label>
            <select
              multiple
              value={formData.exercise_ids.map(String)}
              onChange={(e) => {
                const selected = Array.from(e.target.selectedOptions, option => parseInt(option.value));
                setFormData({ ...formData, exercise_ids: selected });
              }}
              style={{ ...styles.select, minHeight: '150px' }}
            >
              {exercises.map(ex => (
                <option key={ex.id} value={ex.id}>
                  {ex.name} ({ex.primary_muscle || 'N/A'})
                </option>
              ))}
            </select>
            <small style={styles.helpText}>Hold Ctrl/Cmd to select multiple exercises</small>
          </div>

          <button type="submit" disabled={saving} style={styles.saveAllButton}>
            {saving ? 'Saving...' : editingId ? '💾 Update Workout' : '💾 Create Workout'}
          </button>
        </form>
      )}

      {loading ? (
        <div style={styles.loading}>Loading...</div>
      ) : workouts.length > 0 ? (
        <div style={styles.success}>Found {workouts.length} workout templates</div>
      ) : (
        <div style={styles.info}>No workout templates found. Create one to get started!</div>
      )}

      <div style={styles.workoutsList}>
        {workouts.map(workout => {
          const detail = workoutDetails[workout.id];
          const isExpanded = expandedIds.has(workout.id);
          return (
            <div key={workout.id} style={styles.workoutCard}>
              <div style={styles.workoutHeader}>
                <div>
                  <h3>{workout.name}</h3>
                  {detail && (
                    <span style={styles.exerciseCount}>
                      {detail.exercises?.length || 0} exercises
                    </span>
                  )}
                </div>
                <button
                  onClick={() => toggleExpand(workout.id)}
                  style={styles.toggleButton}
                >
                  {isExpanded ? '▼' : '▶'}
                </button>
              </div>

              {isExpanded && detail && (
                <div style={styles.workoutDetails}>
                  {workout.description && (
                    <div style={styles.infoBox}>{workout.description}</div>
                  )}
                  <div>
                    <strong>Exercises:</strong>
                    <ul style={styles.exercisesList}>
                      {detail.exercises?.map((ex, idx) => (
                        <li key={idx}>
                          {ex.exercise_name} ({ex.primary_muscle || 'N/A'})
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div style={styles.actionButtons}>
                    <button
                      onClick={() => startEdit(workout)}
                      style={styles.editButton}
                    >
                      ✏️ Edit
                    </button>
                    <button
                      onClick={() => handleDelete(workout.id)}
                      style={styles.deleteButton}
                    >
                      🗑️ Delete
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    width: '100%',
    boxSizing: 'border-box',
  },
  header: {
    backgroundColor: 'white',
    padding: 'clamp(0.75rem, 2vw, 1rem) clamp(1rem, 4vw, 2rem)',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    boxSizing: 'border-box',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  homeButton: {
    padding: '0.5rem',
    backgroundColor: 'transparent',
    border: 'none',
    fontSize: '1.5rem',
    cursor: 'pointer',
    borderRadius: '4px',
    transition: 'background-color 0.2s',
  },
  title: {
    margin: 0,
    fontSize: '1.5rem',
    color: '#333',
  },
  headerActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  userInfo: {
    color: '#666',
  },
  logoutButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  content: {
    width: '100%',
    maxWidth: '1200px',
    margin: '0 auto',
    padding: 'clamp(1rem, 3vw, 2rem)',
    boxSizing: 'border-box',
  },
  tabContainer: {
    display: 'flex',
    gap: '0.5rem',
    marginBottom: '2rem',
    borderBottom: '2px solid #ddd',
    overflowX: 'auto',
  },
  tab: {
    padding: '0.75rem 1.5rem',
    backgroundColor: 'transparent',
    border: 'none',
    borderBottom: '3px solid transparent',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '500',
    color: '#666',
    transition: 'all 0.2s',
    whiteSpace: 'nowrap',
  },
  tabActive: {
    color: '#007bff',
    borderBottomColor: '#007bff',
  },
  tabContent: {
    backgroundColor: 'white',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  sectionTitle: {
    marginTop: 0,
    marginBottom: '1.5rem',
    fontSize: '1.5rem',
    color: '#333',
  },
  formSection: {
    marginBottom: '2rem',
  },
  formRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
    marginBottom: '1rem',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  label: {
    fontSize: '0.9rem',
    fontWeight: '500',
    color: '#333',
  },
  input: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
  },
  select: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
    backgroundColor: 'white',
  },
  addButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  saveButton: {
    padding: '0.5rem',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
    minWidth: '40px',
  },
  removeButton: {
    padding: '0.5rem',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
    minWidth: '40px',
  },
  saveAllButton: {
    padding: '0.75rem 2rem',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '600',
  },
  exercisesSection: {
    marginTop: '2rem',
  },
  exercisesHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  exerciseCard: {
    border: '1px solid #ddd',
    borderRadius: '4px',
    padding: '1rem',
    marginBottom: '1rem',
    backgroundColor: '#f9f9f9',
  },
  exerciseRow: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr 1fr 1fr auto auto',
    gap: '1rem',
    alignItems: 'end',
  },
  saveAllSection: {
    marginTop: '2rem',
    textAlign: 'center',
  },
  infoBox: {
    padding: '1rem',
    backgroundColor: '#e7f3ff',
    borderRadius: '4px',
    marginBottom: '1rem',
    border: '1px solid #b3d9ff',
  },
  lastWorkoutSection: {
    marginTop: '1.5rem',
    padding: '1rem',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px',
    border: '1px solid #ddd',
  },
  lastWorkoutList: {
    marginTop: '1rem',
  },
  lastWorkoutItem: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '0.5rem 0',
    borderBottom: '1px solid #ddd',
  },
  caption: {
    fontSize: '0.85rem',
    color: '#666',
    marginTop: '0.25rem',
  },
  recordsList: {
    marginTop: '2rem',
  },
  recordCard: {
    border: '1px solid #ddd',
    borderRadius: '4px',
    padding: '1.5rem',
    marginBottom: '1rem',
    backgroundColor: '#f9f9f9',
  },
  recordHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.5rem',
  },
  recordDate: {
    color: '#666',
    fontSize: '0.9rem',
  },
  exercisesList: {
    marginTop: '1rem',
  },
  exerciseItem: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '0.5rem 0',
    borderBottom: '1px solid #ddd',
  },
  deleteButton: {
    marginTop: '1rem',
    padding: '0.5rem 1rem',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  cancelButton: {
    padding: '0.75rem 2rem',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '600',
  },
  error: {
    padding: '1rem',
    backgroundColor: '#f8d7da',
    color: '#721c24',
    borderRadius: '4px',
    marginBottom: '1rem',
    border: '1px solid #f5c6cb',
  },
  success: {
    padding: '1rem',
    backgroundColor: '#d4edda',
    color: '#155724',
    borderRadius: '4px',
    marginBottom: '1rem',
    border: '1px solid #c3e6cb',
  },
  info: {
    padding: '1rem',
    backgroundColor: '#d1ecf1',
    color: '#0c5460',
    borderRadius: '4px',
    marginBottom: '1rem',
    border: '1px solid #bee5eb',
  },
  loading: {
    padding: '2rem',
    textAlign: 'center',
    color: '#666',
  },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1.5rem',
  },
  sectionHeaderLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  backButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    fontWeight: '500',
    whiteSpace: 'nowrap',
  },
  formCard: {
    border: '1px solid #ddd',
    borderRadius: '4px',
    padding: '1.5rem',
    marginBottom: '2rem',
    backgroundColor: '#f9f9f9',
  },
  filterSection: {
    display: 'flex',
    gap: '1rem',
    marginBottom: '1rem',
  },
  exercisesGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '1rem',
    marginTop: '1rem',
  },
  exerciseLibraryCard: {
    border: '1px solid #ddd',
    borderRadius: '4px',
    padding: '1rem',
    backgroundColor: 'white',
  },
  exerciseLibraryHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.5rem',
  },
  exerciseLibraryDetails: {
    marginTop: '1rem',
  },
  exerciseImage: {
    width: '100%',
    maxWidth: '300px',
    height: 'auto',
    borderRadius: '4px',
    marginBottom: '1rem',
  },
  exerciseInfo: {
    marginTop: '1rem',
  },
  notesText: {
    marginTop: '0.5rem',
    color: '#666',
    whiteSpace: 'pre-wrap',
  },
  muscleTag: {
    display: 'inline-block',
    padding: '0.25rem 0.5rem',
    backgroundColor: '#e7f3ff',
    color: '#007bff',
    borderRadius: '4px',
    fontSize: '0.85rem',
    marginLeft: '0.5rem',
  },
  toggleButton: {
    padding: '0.25rem 0.5rem',
    backgroundColor: 'transparent',
    border: '1px solid #ddd',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  actionButtons: {
    display: 'flex',
    gap: '0.5rem',
    marginTop: '1rem',
  },
  editButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  workoutsList: {
    marginTop: '1rem',
  },
  workoutCard: {
    border: '1px solid #ddd',
    borderRadius: '4px',
    padding: '1rem',
    marginBottom: '1rem',
    backgroundColor: 'white',
  },
  workoutHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.5rem',
  },
  workoutDetails: {
    marginTop: '1rem',
  },
  exerciseCount: {
    display: 'inline-block',
    padding: '0.25rem 0.5rem',
    backgroundColor: '#e7f3ff',
    color: '#007bff',
    borderRadius: '4px',
    fontSize: '0.85rem',
    marginLeft: '0.5rem',
  },
  helpText: {
    display: 'block',
    marginTop: '0.25rem',
    color: '#666',
    fontSize: '0.85rem',
  },
  exerciseLinkContainer: {
    marginTop: '0.5rem',
  },
  exerciseLink: {
    padding: '0.25rem 0.5rem',
    backgroundColor: 'transparent',
    color: '#007bff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    textDecoration: 'underline',
    display: 'inline-block',
    transition: 'color 0.2s',
    fontWeight: '500',
  },
  exerciseLinkHover: {
    color: '#0056b3',
    textDecoration: 'underline',
  },
  highlightedCard: {
    border: '2px solid #007bff',
    boxShadow: '0 0 10px rgba(0, 123, 255, 0.3)',
  },
};
