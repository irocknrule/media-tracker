import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { habitService } from '../services/habitService';
import { getErrorMessage } from '../utils/errorHandler';

export default function Habits() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('log'); // 'log', 'calendar', 'analytics'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Log Habits tab state
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [existingHabits, setExistingHabits] = useState([]);
  const [formData, setFormData] = useState({
    exercise_workout: { checked: false, minutes: '' },
    exercise_yoga: { checked: false, minutes: '' },
    exercise_running: { checked: false, distance: '', elevation: '' },
    exercise_biking: { checked: false, distance: '', elevation: '' },
    mindfulness_meditation: { checked: false, minutes: '' },
    music_guitar: { checked: false, minutes: '' },
    music_drums: { checked: false, minutes: '' },
  });

  // Calendar tab state
  const [calendarView, setCalendarView] = useState('Monthly'); // 'Monthly', 'Quarterly', 'Yearly'
  const [calendarMonth, setCalendarMonth] = useState(new Date());
  const [calendarQuarter, setCalendarQuarter] = useState(new Date());
  const [calendarYear, setCalendarYear] = useState(new Date().getFullYear());
  const [calendarData, setCalendarData] = useState({});

  // Analytics tab state
  const [analyticsTimeframe, setAnalyticsTimeframe] = useState('This Month');
  const [analyticsStartDate, setAnalyticsStartDate] = useState(null);
  const [analyticsEndDate, setAnalyticsEndDate] = useState(null);
  const [analyticsData, setAnalyticsData] = useState(null);

  // Load existing habits when date changes
  useEffect(() => {
    if (activeTab === 'log') {
      loadExistingHabits();
    }
  }, [selectedDate, activeTab]);

  // Load calendar data when calendar view changes
  useEffect(() => {
    if (activeTab === 'calendar') {
      loadCalendarData();
    }
  }, [calendarView, calendarMonth, calendarQuarter, calendarYear, activeTab]);

  // Load analytics data when timeframe changes
  useEffect(() => {
    if (activeTab === 'analytics') {
      calculateAnalyticsDates();
    }
  }, [analyticsTimeframe, analyticsStartDate, analyticsEndDate, activeTab]);

  const loadExistingHabits = async () => {
    try {
      setLoading(true);
      setError('');
      const [summaryData, detailedData] = await Promise.all([
        habitService.getByDate(selectedDate),
        habitService.getByDateDetailed(selectedDate),
      ]);

      setExistingHabits(detailedData || []);

      // Load form data from existing habits
      const habits = summaryData?.habits || {};
      const newFormData = {
        exercise_workout: { checked: false, minutes: '' },
        exercise_yoga: { checked: false, minutes: '' },
        exercise_running: { checked: false, distance: '', elevation: '' },
        exercise_biking: { checked: false, distance: '', elevation: '' },
        mindfulness_meditation: { checked: false, minutes: '' },
        music_guitar: { checked: false, minutes: '' },
        music_drums: { checked: false, minutes: '' },
      };

      for (const [habitType, metrics] of Object.entries(habits)) {
        if (habitType in newFormData) {
          newFormData[habitType].checked = true;
          for (const metric of metrics) {
            const metricName = metric.metric_name.toLowerCase();
            if (metricName === 'minutes') {
              newFormData[habitType].minutes = String(metric.value);
            } else if (metricName === 'distance') {
              newFormData[habitType].distance = String(metric.value);
            } else if (metricName === 'elevation') {
              newFormData[habitType].elevation = String(metric.value);
            }
          }
        }
      }

      setFormData(newFormData);
    } catch (err) {
      console.error('Error loading habits:', err);
      setError(getErrorMessage(err) || 'Failed to load habits');
    } finally {
      setLoading(false);
    }
  };

  const loadCalendarData = async () => {
    try {
      setLoading(true);
      setError('');
      let startDate, endDate;

      if (calendarView === 'Monthly') {
        const year = calendarMonth.getFullYear();
        const month = calendarMonth.getMonth();
        startDate = new Date(year, month, 1).toISOString().split('T')[0];
        endDate = new Date(year, month + 1, 0).toISOString().split('T')[0];
      } else if (calendarView === 'Quarterly') {
        const year = calendarQuarter.getFullYear();
        const month = calendarQuarter.getMonth();
        const quarter = Math.floor(month / 3);
        const startMonth = quarter * 3;
        startDate = new Date(year, startMonth, 1).toISOString().split('T')[0];
        endDate = new Date(year, startMonth + 3, 0).toISOString().split('T')[0];
      } else {
        // Yearly
        startDate = `${calendarYear}-01-01`;
        endDate = `${calendarYear}-12-31`;
      }

      const data = await habitService.getCalendar(startDate, endDate);
      const habitDataMap = {};
      for (const entry of data) {
        const entryDate = entry.date.split('T')[0];
        habitDataMap[entryDate] = entry.habit_types || [];
      }
      setCalendarData(habitDataMap);
    } catch (err) {
      console.error('Error loading calendar data:', err);
      setError(getErrorMessage(err) || 'Failed to load calendar data');
    } finally {
      setLoading(false);
    }
  };

  const calculateAnalyticsDates = () => {
    const today = new Date();
    let startDate = null;
    let endDate = null;

    if (analyticsTimeframe === 'This Month') {
      startDate = new Date(today.getFullYear(), today.getMonth(), 1);
      endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    } else if (analyticsTimeframe === 'This Quarter') {
      const quarter = Math.floor(today.getMonth() / 3);
      const startMonth = quarter * 3;
      startDate = new Date(today.getFullYear(), startMonth, 1);
      endDate = new Date(today.getFullYear(), startMonth + 3, 0);
    } else if (analyticsTimeframe === 'This Year') {
      startDate = new Date(today.getFullYear(), 0, 1);
      endDate = new Date(today.getFullYear(), 11, 31);
    } else if (analyticsTimeframe === 'Last Month') {
      const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      startDate = new Date(lastMonth.getFullYear(), lastMonth.getMonth(), 1);
      endDate = new Date(lastMonth.getFullYear(), lastMonth.getMonth() + 1, 0);
    } else if (analyticsTimeframe === 'Last Quarter') {
      const quarter = Math.floor(today.getMonth() / 3);
      const lastQuarter = quarter === 0 ? 3 : quarter - 1;
      const year = lastQuarter === 3 ? today.getFullYear() - 1 : today.getFullYear();
      const startMonth = lastQuarter * 3;
      startDate = new Date(year, startMonth, 1);
      endDate = new Date(year, startMonth + 3, 0);
    } else if (analyticsTimeframe === 'Last Year') {
      startDate = new Date(today.getFullYear() - 1, 0, 1);
      endDate = new Date(today.getFullYear() - 1, 11, 31);
    } else if (analyticsTimeframe === 'Custom') {
      // Custom dates are already set
      return;
    }

    if (startDate && endDate) {
      setAnalyticsStartDate(startDate.toISOString().split('T')[0]);
      setAnalyticsEndDate(endDate.toISOString().split('T')[0]);
    }
  };

  useEffect(() => {
    if (activeTab === 'analytics' && analyticsStartDate && analyticsEndDate) {
      loadAnalyticsData();
    }
  }, [analyticsStartDate, analyticsEndDate, activeTab]);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await habitService.getAnalytics(analyticsStartDate, analyticsEndDate);
      setAnalyticsData(data);
    } catch (err) {
      console.error('Error loading analytics:', err);
      setError(getErrorMessage(err) || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteHabit = async (habitId) => {
    try {
      setLoading(true);
      setError('');
      await habitService.delete(habitId);
      setSuccess('Habit deleted successfully!');
      loadExistingHabits();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      console.error('Error deleting habit:', err);
      setError(getErrorMessage(err) || 'Failed to delete habit');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAllHabits = async () => {
    if (!window.confirm('Are you sure you want to delete all habits for this day?')) {
      return;
    }
    try {
      setLoading(true);
      setError('');
      await habitService.deleteByDate(selectedDate);
      setSuccess('All habits deleted successfully!');
      loadExistingHabits();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      console.error('Error deleting habits:', err);
      setError(getErrorMessage(err) || 'Failed to delete habits');
    } finally {
      setLoading(false);
    }
  };

  const handleClearForm = () => {
    setFormData({
      exercise_workout: { checked: false, minutes: '' },
      exercise_yoga: { checked: false, minutes: '' },
      exercise_running: { checked: false, distance: '', elevation: '' },
      exercise_biking: { checked: false, distance: '', elevation: '' },
      mindfulness_meditation: { checked: false, minutes: '' },
      music_guitar: { checked: false, minutes: '' },
      music_drums: { checked: false, minutes: '' },
    });
  };

  const handleSaveHabits = async () => {
    try {
      setLoading(true);
      setError('');
      setSuccess('');

      const logs = [];

      // Exercise Workout
      if (formData.exercise_workout.checked && formData.exercise_workout.minutes) {
        logs.push({
          habit_type: 'exercise_workout',
          metric_name: 'minutes',
          value: parseFloat(formData.exercise_workout.minutes),
          unit: 'min',
        });
      }

      // Exercise Yoga
      if (formData.exercise_yoga.checked && formData.exercise_yoga.minutes) {
        logs.push({
          habit_type: 'exercise_yoga',
          metric_name: 'minutes',
          value: parseFloat(formData.exercise_yoga.minutes),
          unit: 'min',
        });
      }

      // Exercise Running
      if (formData.exercise_running.checked) {
        if (formData.exercise_running.distance) {
          logs.push({
            habit_type: 'exercise_running',
            metric_name: 'distance',
            value: parseFloat(formData.exercise_running.distance),
            unit: 'mi',
          });
        }
        if (formData.exercise_running.elevation) {
          logs.push({
            habit_type: 'exercise_running',
            metric_name: 'elevation',
            value: parseFloat(formData.exercise_running.elevation),
            unit: 'ft',
          });
        }
      }

      // Exercise Biking
      if (formData.exercise_biking.checked) {
        if (formData.exercise_biking.distance) {
          logs.push({
            habit_type: 'exercise_biking',
            metric_name: 'distance',
            value: parseFloat(formData.exercise_biking.distance),
            unit: 'mi',
          });
        }
        if (formData.exercise_biking.elevation) {
          logs.push({
            habit_type: 'exercise_biking',
            metric_name: 'elevation',
            value: parseFloat(formData.exercise_biking.elevation),
            unit: 'ft',
          });
        }
      }

      // Mindfulness Meditation
      if (formData.mindfulness_meditation.checked && formData.mindfulness_meditation.minutes) {
        logs.push({
          habit_type: 'mindfulness_meditation',
          metric_name: 'minutes',
          value: parseFloat(formData.mindfulness_meditation.minutes),
          unit: 'min',
        });
      }

      // Music Guitar
      if (formData.music_guitar.checked && formData.music_guitar.minutes) {
        logs.push({
          habit_type: 'music_guitar',
          metric_name: 'minutes',
          value: parseFloat(formData.music_guitar.minutes),
          unit: 'min',
        });
      }

      // Music Drums
      if (formData.music_drums.checked && formData.music_drums.minutes) {
        logs.push({
          habit_type: 'music_drums',
          metric_name: 'minutes',
          value: parseFloat(formData.music_drums.minutes),
          unit: 'min',
        });
      }

      if (logs.length === 0) {
        setError('Please select at least one habit to save');
        setLoading(false);
        return;
      }

      await habitService.create(selectedDate, logs);
      setSuccess(`Successfully saved ${logs.length} habit${logs.length !== 1 ? 's' : ''}!`);
      loadExistingHabits();
      setTimeout(() => setSuccess(''), 5000);
    } catch (err) {
      console.error('Error saving habits:', err);
      setError(getErrorMessage(err) || 'Failed to save habits');
    } finally {
      setLoading(false);
    }
  };

  const formatHabitTypeName = (habitType) => {
    const parts = habitType.split('_');
    return parts.slice(1).map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  const renderLogHabitsTab = () => {
    // Group existing habits by type
    const habitsByType = {};
    for (const log of existingHabits) {
      const habitType = log.habit_type || '';
      if (!habitsByType[habitType]) {
        habitsByType[habitType] = [];
      }
      habitsByType[habitType].push(log);
    }

    return (
      <div style={styles.tabContent}>
        <h2 style={styles.tabTitle}>📝 Log Daily Habits</h2>

        {/* Date Picker */}
        <div style={styles.formSection}>
          <label style={styles.label}>Date:</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            style={styles.dateInput}
          />
        </div>

        {/* Existing Habits */}
        {existingHabits.length > 0 && (
          <div style={styles.formSection}>
            <h3 style={styles.sectionTitle}>📋 Currently Saved Habits</h3>
            {Object.entries(habitsByType).map(([habitType, logs]) => (
              <details key={habitType} style={styles.habitDetails}>
                <summary style={styles.habitSummary}>
                  <strong>{formatHabitTypeName(habitType)}</strong> ({logs.length} metric{logs.length !== 1 ? 's' : ''})
                </summary>
                {logs.map((log) => (
                  <div key={log.id} style={styles.habitItem}>
                    <div style={styles.habitItemContent}>
                      <span>
                        {log.metric_name.charAt(0).toUpperCase() + log.metric_name.slice(1)}: {log.value} {log.unit}
                      </span>
                      <button
                        onClick={() => handleDeleteHabit(log.id)}
                        style={styles.deleteButton}
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </div>
                ))}
              </details>
            ))}
            <button
              onClick={handleDeleteAllHabits}
              style={styles.deleteAllButton}
            >
              🗑️ Delete All Habits for This Day
            </button>
          </div>
        )}

        {/* Exercise Section */}
        <div style={styles.formSection}>
          <h3 style={styles.sectionTitle}>🏋️ Exercise</h3>

          {/* Workout */}
          <div style={styles.habitRow}>
            <label style={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={formData.exercise_workout.checked}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    exercise_workout: {
                      ...formData.exercise_workout,
                      checked: e.target.checked,
                    },
                  })
                }
                style={styles.checkbox}
              />
              Workout
            </label>
            {formData.exercise_workout.checked && (
              <input
                type="number"
                min="0"
                step="1"
                placeholder="Minutes"
                value={formData.exercise_workout.minutes}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    exercise_workout: {
                      ...formData.exercise_workout,
                      minutes: e.target.value,
                    },
                  })
                }
                style={styles.numberInput}
              />
            )}
          </div>

          {/* Yoga */}
          <div style={styles.habitRow}>
            <label style={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={formData.exercise_yoga.checked}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    exercise_yoga: {
                      ...formData.exercise_yoga,
                      checked: e.target.checked,
                    },
                  })
                }
                style={styles.checkbox}
              />
              Yoga
            </label>
            {formData.exercise_yoga.checked && (
              <input
                type="number"
                min="0"
                step="1"
                placeholder="Minutes"
                value={formData.exercise_yoga.minutes}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    exercise_yoga: {
                      ...formData.exercise_yoga,
                      minutes: e.target.value,
                    },
                  })
                }
                style={styles.numberInput}
              />
            )}
          </div>

          {/* Running */}
          <div style={styles.habitRow}>
            <label style={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={formData.exercise_running.checked}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    exercise_running: {
                      ...formData.exercise_running,
                      checked: e.target.checked,
                    },
                  })
                }
                style={styles.checkbox}
              />
              Running
            </label>
            {formData.exercise_running.checked && (
              <div style={styles.twoColumnInputs}>
                <div>
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    placeholder="Distance"
                    value={formData.exercise_running.distance}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        exercise_running: {
                          ...formData.exercise_running,
                          distance: e.target.value,
                        },
                      })
                    }
                    style={styles.numberInput}
                  />
                  <span style={styles.unitLabel}>mi</span>
                </div>
                <div>
                  <input
                    type="number"
                    min="0"
                    step="1"
                    placeholder="Elevation"
                    value={formData.exercise_running.elevation}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        exercise_running: {
                          ...formData.exercise_running,
                          elevation: e.target.value,
                        },
                      })
                    }
                    style={styles.numberInput}
                  />
                  <span style={styles.unitLabel}>ft</span>
                </div>
              </div>
            )}
          </div>

          {/* Biking */}
          <div style={styles.habitRow}>
            <label style={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={formData.exercise_biking.checked}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    exercise_biking: {
                      ...formData.exercise_biking,
                      checked: e.target.checked,
                    },
                  })
                }
                style={styles.checkbox}
              />
              Biking
            </label>
            {formData.exercise_biking.checked && (
              <div style={styles.twoColumnInputs}>
                <div>
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    placeholder="Distance"
                    value={formData.exercise_biking.distance}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        exercise_biking: {
                          ...formData.exercise_biking,
                          distance: e.target.value,
                        },
                      })
                    }
                    style={styles.numberInput}
                  />
                  <span style={styles.unitLabel}>mi</span>
                </div>
                <div>
                  <input
                    type="number"
                    min="0"
                    step="1"
                    placeholder="Elevation"
                    value={formData.exercise_biking.elevation}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        exercise_biking: {
                          ...formData.exercise_biking,
                          elevation: e.target.value,
                        },
                      })
                    }
                    style={styles.numberInput}
                  />
                  <span style={styles.unitLabel}>ft</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Mindfulness Section */}
        <div style={styles.formSection}>
          <h3 style={styles.sectionTitle}>🧠 Mindfulness</h3>

          {/* Meditation */}
          <div style={styles.habitRow}>
            <label style={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={formData.mindfulness_meditation.checked}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    mindfulness_meditation: {
                      ...formData.mindfulness_meditation,
                      checked: e.target.checked,
                    },
                  })
                }
                style={styles.checkbox}
              />
              Meditation
            </label>
            {formData.mindfulness_meditation.checked && (
              <input
                type="number"
                min="0"
                step="1"
                placeholder="Minutes"
                value={formData.mindfulness_meditation.minutes}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    mindfulness_meditation: {
                      ...formData.mindfulness_meditation,
                      minutes: e.target.value,
                    },
                  })
                }
                style={styles.numberInput}
              />
            )}
          </div>
        </div>

        {/* Music Section */}
        <div style={styles.formSection}>
          <h3 style={styles.sectionTitle}>🎵 Music Practice</h3>

          {/* Guitar */}
          <div style={styles.habitRow}>
            <label style={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={formData.music_guitar.checked}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    music_guitar: {
                      ...formData.music_guitar,
                      checked: e.target.checked,
                    },
                  })
                }
                style={styles.checkbox}
              />
              Guitar
            </label>
            {formData.music_guitar.checked && (
              <input
                type="number"
                min="0"
                step="1"
                placeholder="Minutes"
                value={formData.music_guitar.minutes}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    music_guitar: {
                      ...formData.music_guitar,
                      minutes: e.target.value,
                    },
                  })
                }
                style={styles.numberInput}
              />
            )}
          </div>

          {/* Drums */}
          <div style={styles.habitRow}>
            <label style={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={formData.music_drums.checked}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    music_drums: {
                      ...formData.music_drums,
                      checked: e.target.checked,
                    },
                  })
                }
                style={styles.checkbox}
              />
              Drums
            </label>
            {formData.music_drums.checked && (
              <input
                type="number"
                min="0"
                step="1"
                placeholder="Minutes"
                value={formData.music_drums.minutes}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    music_drums: {
                      ...formData.music_drums,
                      minutes: e.target.value,
                    },
                  })
                }
                style={styles.numberInput}
              />
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div style={styles.buttonRow}>
          <button onClick={handleClearForm} style={styles.secondaryButton}>
            Clear All
          </button>
          <button
            onClick={handleSaveHabits}
            disabled={loading}
            style={styles.primaryButton}
          >
            {loading ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    );
  };

  const renderCalendarTab = () => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (calendarView === 'Monthly') {
      return renderMonthlyCalendar();
    } else if (calendarView === 'Quarterly') {
      return renderQuarterlyCalendar();
    } else {
      return renderYearlyCalendar();
    }
  };

  const renderMonthlyCalendar = () => {
    const year = calendarMonth.getFullYear();
    const month = calendarMonth.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const navigateMonth = (direction) => {
      const newMonth = new Date(calendarMonth);
      if (direction === 'prev') {
        newMonth.setMonth(month - 1);
      } else {
        newMonth.setMonth(month + 1);
      }
      setCalendarMonth(newMonth);
    };

    const getHabitIcons = (dateStr) => {
      const habits = calendarData[dateStr] || [];
      const icons = [];
      for (const habitType of habits) {
        if (habitType.includes('exercise')) {
          icons.push('🤸');
        } else if (habitType.includes('mindfulness')) {
          icons.push('🧘');
        } else if (habitType.includes('music')) {
          icons.push('🎵');
        } else {
          icons.push('✓');
        }
      }
      return icons;
    };

    return (
      <div style={styles.tabContent}>
        <h2 style={styles.tabTitle}>📅 Calendar View</h2>

        {/* Navigation */}
        <div style={styles.calendarNavigation}>
          <button onClick={() => navigateMonth('prev')} style={styles.navButton}>
            ← Previous
          </button>
          <h3 style={styles.calendarTitle}>
            {calendarMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
          </h3>
          <button onClick={() => navigateMonth('next')} style={styles.navButton}>
            Next →
          </button>
        </div>

        {/* View Type Selector */}
        <div style={styles.viewSelector}>
          {['Monthly', 'Quarterly', 'Yearly'].map((view) => (
            <button
              key={view}
              onClick={() => setCalendarView(view)}
              style={{
                ...styles.viewButton,
                ...(calendarView === view ? styles.viewButtonActive : {}),
              }}
            >
              {view}
            </button>
          ))}
        </div>

        {/* Calendar Grid */}
        <div style={styles.calendarGrid}>
          {dayNames.map((day) => (
            <div key={day} style={styles.calendarDayHeader}>
              <strong>{day}</strong>
            </div>
          ))}

          {Array.from({ length: startingDayOfWeek }).map((_, i) => (
            <div key={`empty-${i}`} style={styles.calendarDay}></div>
          ))}

          {Array.from({ length: daysInMonth }).map((_, i) => {
            const day = i + 1;
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayDate = new Date(year, month, day);
            dayDate.setHours(0, 0, 0, 0);
            const isToday = dayDate.getTime() === today.getTime();
            const icons = getHabitIcons(dateStr);

            return (
              <div
                key={day}
                style={{
                  ...styles.calendarDay,
                  ...(isToday ? styles.calendarDayToday : {}),
                }}
              >
                <div>{day}</div>
                {icons.length > 0 && <div style={styles.calendarIcons}>{icons.join(' ')}</div>}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderQuarterlyCalendar = () => {
    const year = calendarQuarter.getFullYear();
    const month = calendarQuarter.getMonth();
    const quarter = Math.floor(month / 3);
    const startMonth = quarter * 3;

    const navigateQuarter = (direction) => {
      const newQuarter = new Date(calendarQuarter);
      if (direction === 'prev') {
        newQuarter.setMonth(month - 3);
      } else {
        newQuarter.setMonth(month + 3);
      }
      setCalendarQuarter(newQuarter);
    };

    const quarterNames = { 0: 'Q1', 1: 'Q2', 2: 'Q3', 3: 'Q4' };

    return (
      <div style={styles.tabContent}>
        <h2 style={styles.tabTitle}>📅 Calendar View</h2>

        {/* Navigation */}
        <div style={styles.calendarNavigation}>
          <button onClick={() => navigateQuarter('prev')} style={styles.navButton}>
            ← Previous
          </button>
          <h3 style={styles.calendarTitle}>
            {quarterNames[quarter]} {year}
          </h3>
          <button onClick={() => navigateQuarter('next')} style={styles.navButton}>
            Next →
          </button>
        </div>

        {/* View Type Selector */}
        <div style={styles.viewSelector}>
          {['Monthly', 'Quarterly', 'Yearly'].map((view) => (
            <button
              key={view}
              onClick={() => setCalendarView(view)}
              style={{
                ...styles.viewButton,
                ...(calendarView === view ? styles.viewButtonActive : {}),
              }}
            >
              {view}
            </button>
          ))}
        </div>

        {/* Three months side by side */}
        <div style={styles.quarterlyMonths}>
          {[0, 1, 2].map((offset) => {
            const monthNum = startMonth + offset;
            const monthYear = monthNum >= 12 ? year + 1 : year;
            const actualMonth = monthNum >= 12 ? monthNum - 12 : monthNum;
            return (
              <div key={offset} style={styles.quarterlyMonth}>
                {renderSingleMonth(monthYear, actualMonth)}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderYearlyCalendar = () => {
    const navigateYear = (direction) => {
      if (direction === 'prev') {
        setCalendarYear(calendarYear - 1);
      } else {
        setCalendarYear(calendarYear + 1);
      }
    };

    return (
      <div style={styles.tabContent}>
        <h2 style={styles.tabTitle}>📅 Calendar View</h2>

        {/* Navigation */}
        <div style={styles.calendarNavigation}>
          <button onClick={() => navigateYear('prev')} style={styles.navButton}>
            ← Previous
          </button>
          <h3 style={styles.calendarTitle}>{calendarYear}</h3>
          <button onClick={() => navigateYear('next')} style={styles.navButton}>
            Next →
          </button>
        </div>

        {/* View Type Selector */}
        <div style={styles.viewSelector}>
          {['Monthly', 'Quarterly', 'Yearly'].map((view) => (
            <button
              key={view}
              onClick={() => setCalendarView(view)}
              style={{
                ...styles.viewButton,
                ...(calendarView === view ? styles.viewButtonActive : {}),
              }}
            >
              {view}
            </button>
          ))}
        </div>

        {/* All 12 months in a grid */}
        <div style={styles.yearlyMonths}>
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} style={styles.yearlyMonth}>
              {renderSingleMonth(calendarYear, i)}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderSingleMonth = (year, month) => {
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const monthName = firstDay.toLocaleDateString('en-US', { month: 'long' });
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const getHabitIcons = (dateStr) => {
      const habits = calendarData[dateStr] || [];
      const icons = [];
      for (const habitType of habits) {
        if (habitType.includes('exercise')) {
          icons.push('🤸');
        } else if (habitType.includes('mindfulness')) {
          icons.push('🧘');
        } else if (habitType.includes('music')) {
          icons.push('🎵');
        } else {
          icons.push('✓');
        }
      }
      return icons;
    };

    return (
      <div style={styles.singleMonth}>
        <h4 style={styles.monthHeader}>{monthName} {year}</h4>
        <div style={styles.miniCalendarGrid}>
          {dayNames.map((day) => (
            <div key={day} style={styles.miniDayHeader}>
              {day.substring(0, 1)}
            </div>
          ))}

          {Array.from({ length: startingDayOfWeek }).map((_, i) => (
            <div key={`empty-${i}`} style={styles.miniCalendarDay}></div>
          ))}

          {Array.from({ length: daysInMonth }).map((_, i) => {
            const day = i + 1;
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayDate = new Date(year, month, day);
            dayDate.setHours(0, 0, 0, 0);
            const isToday = dayDate.getTime() === today.getTime();
            const icons = getHabitIcons(dateStr);

            return (
              <div
                key={day}
                style={{
                  ...styles.miniCalendarDay,
                  ...(isToday ? styles.miniCalendarDayToday : {}),
                }}
              >
                <span>{day}</span>
                {icons.length > 0 && <span style={styles.miniIcons}>{icons.join('')}</span>}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderAnalyticsTab = () => {
    if (!analyticsData) {
      return (
        <div style={styles.tabContent}>
          <h2 style={styles.tabTitle}>📊 Habit Analytics</h2>
          <div>Loading analytics...</div>
        </div>
      );
    }

    const exerciseData = analyticsData.exercise || {};
    const mindfulnessData = analyticsData.mindfulness || {};
    const musicData = analyticsData.music || {};

    const avgExerciseMinutes =
      exerciseData.total_sessions > 0
        ? exerciseData.total_minutes / exerciseData.total_sessions
        : 0;
    const avgMindfulnessMinutes =
      mindfulnessData.total_sessions > 0
        ? mindfulnessData.total_minutes / mindfulnessData.total_sessions
        : 0;
    const avgMusicMinutes =
      musicData.total_sessions > 0 ? musicData.total_minutes / musicData.total_sessions : 0;

    return (
      <div style={styles.tabContent}>
        <h2 style={styles.tabTitle}>📊 Habit Analytics</h2>

        {/* Timeframe Selector */}
        <div style={styles.formSection}>
          <label style={styles.label}>Time Frame:</label>
          <select
            value={analyticsTimeframe}
            onChange={(e) => setAnalyticsTimeframe(e.target.value)}
            style={styles.select}
          >
            <option>This Month</option>
            <option>This Quarter</option>
            <option>This Year</option>
            <option>Last Month</option>
            <option>Last Quarter</option>
            <option>Last Year</option>
            <option>Custom</option>
          </select>
        </div>

        {analyticsTimeframe === 'Custom' && (
          <div style={styles.formSection}>
            <label style={styles.label}>Start Date:</label>
            <input
              type="date"
              value={analyticsStartDate || ''}
              onChange={(e) => setAnalyticsStartDate(e.target.value)}
              style={styles.dateInput}
            />
            <label style={styles.label}>End Date:</label>
            <input
              type="date"
              value={analyticsEndDate || ''}
              onChange={(e) => setAnalyticsEndDate(e.target.value)}
              style={styles.dateInput}
            />
          </div>
        )}

        {analyticsStartDate && analyticsEndDate && (
          <div style={styles.infoBox}>
            📅 Showing data from {new Date(analyticsStartDate).toLocaleDateString()} to{' '}
            {new Date(analyticsEndDate).toLocaleDateString()}
          </div>
        )}

        {/* Key Metrics */}
        <div style={styles.formSection}>
          <h3 style={styles.sectionTitle}>📈 Key Metrics</h3>
          <div style={styles.metricsGrid}>
            <div style={styles.metricCard}>
              <div style={styles.metricValue}>{analyticsData.total_days_with_habits || 0}</div>
              <div style={styles.metricLabel}>Days with Habits</div>
            </div>
            <div style={styles.metricCard}>
              <div style={styles.metricValue}>{exerciseData.total_sessions || 0}</div>
              <div style={styles.metricLabel}>Total Exercise Sessions</div>
            </div>
            <div style={styles.metricCard}>
              <div style={styles.metricValue}>{mindfulnessData.total_sessions || 0}</div>
              <div style={styles.metricLabel}>Total Mindfulness Sessions</div>
            </div>
            <div style={styles.metricCard}>
              <div style={styles.metricValue}>{musicData.total_sessions || 0}</div>
              <div style={styles.metricLabel}>Total Music Sessions</div>
            </div>
          </div>
        </div>

        {/* Exercise Analytics */}
        <div style={styles.formSection}>
          <h3 style={styles.sectionTitle}>🏋️ Exercise Analytics</h3>
          <div style={styles.metricsGrid}>
            <div style={styles.metricCard}>
              <div style={styles.metricValue}>{Math.round(exerciseData.total_minutes || 0)}</div>
              <div style={styles.metricLabel}>Total Minutes</div>
            </div>
            <div style={styles.metricCard}>
              <div style={styles.metricValue}>
                {(exerciseData.total_distance_miles || 0).toFixed(2)} mi
              </div>
              <div style={styles.metricLabel}>Total Distance</div>
            </div>
            <div style={styles.metricCard}>
              <div style={styles.metricValue}>{Math.round(exerciseData.total_elevation_feet || 0)} ft</div>
              <div style={styles.metricLabel}>Total Elevation</div>
            </div>
            <div style={styles.metricCard}>
              <div style={styles.metricValue}>{avgExerciseMinutes.toFixed(1)}</div>
              <div style={styles.metricLabel}>Avg Minutes/Session</div>
            </div>
          </div>

          {exerciseData.total_sessions > 0 && (
            <div style={styles.breakdownSection}>
              <h4 style={styles.subsectionTitle}>Exercise Breakdown</h4>
              <div style={styles.breakdownList}>
                {exerciseData.workout_sessions > 0 && (
                  <div>Workout: {exerciseData.workout_sessions} sessions</div>
                )}
                {exerciseData.yoga_sessions > 0 && (
                  <div>Yoga: {exerciseData.yoga_sessions} sessions</div>
                )}
                {exerciseData.running_sessions > 0 && (
                  <div>Running: {exerciseData.running_sessions} sessions</div>
                )}
                {exerciseData.biking_sessions > 0 && (
                  <div>Biking: {exerciseData.biking_sessions} sessions</div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Mindfulness Analytics */}
        <div style={styles.formSection}>
          <h3 style={styles.sectionTitle}>🧠 Mindfulness Analytics</h3>
          <div style={styles.metricsGrid}>
            <div style={styles.metricCard}>
              <div style={styles.metricValue}>{Math.round(mindfulnessData.total_minutes || 0)}</div>
              <div style={styles.metricLabel}>Total Minutes</div>
            </div>
            <div style={styles.metricCard}>
              <div style={styles.metricValue}>{avgMindfulnessMinutes.toFixed(1)}</div>
              <div style={styles.metricLabel}>Avg Minutes/Session</div>
            </div>
          </div>
        </div>

        {/* Music Analytics */}
        <div style={styles.formSection}>
          <h3 style={styles.sectionTitle}>🎵 Music Practice Analytics</h3>
          <div style={styles.metricsGrid}>
            <div style={styles.metricCard}>
              <div style={styles.metricValue}>{Math.round(musicData.total_minutes || 0)}</div>
              <div style={styles.metricLabel}>Total Minutes</div>
            </div>
            <div style={styles.metricCard}>
              <div style={styles.metricValue}>{avgMusicMinutes.toFixed(1)}</div>
              <div style={styles.metricLabel}>Avg Minutes/Session</div>
            </div>
            <div style={styles.metricCard}>
              <div style={styles.metricValue}>{musicData.guitar_sessions || 0}</div>
              <div style={styles.metricLabel}>Guitar Sessions</div>
            </div>
            <div style={styles.metricCard}>
              <div style={styles.metricValue}>{musicData.drums_sessions || 0}</div>
              <div style={styles.metricLabel}>Drums Sessions</div>
            </div>
          </div>

          {musicData.total_sessions > 0 && (
            <div style={styles.breakdownSection}>
              <h4 style={styles.subsectionTitle}>Music Practice Breakdown</h4>
              <div style={styles.breakdownList}>
                {musicData.guitar_sessions > 0 && (
                  <div>Guitar: {musicData.guitar_sessions} sessions</div>
                )}
                {musicData.drums_sessions > 0 && (
                  <div>Drums: {musicData.drums_sessions} sessions</div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Habit Type Distribution */}
        {analyticsData.habit_type_counts && Object.keys(analyticsData.habit_type_counts).length > 0 && (
          <div style={styles.formSection}>
            <h3 style={styles.sectionTitle}>📋 Habit Type Distribution</h3>
            <div style={styles.habitDistribution}>
              {Object.entries(analyticsData.habit_type_counts)
                .sort((a, b) => b[1] - a[1])
                .map(([habitType, count]) => {
                  const parts = habitType.split('_');
                  const category = parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
                  const activity = parts
                    .slice(1)
                    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(' ');
                  return (
                    <div key={habitType} style={styles.habitDistributionItem}>
                      <strong>{category}: {activity}</strong>: {count}
                    </div>
                  );
                })}
            </div>
          </div>
        )}
      </div>
    );
  };

  if (!user) {
    return (
      <div style={styles.container}>
        <div style={{ padding: '2rem', textAlign: 'center' }}>Loading...</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>📅 Habit Tracker</h1>
        <div style={styles.headerActions}>
          <button onClick={() => navigate('/')} style={styles.navLinkButton}>
            Home
          </button>
          <span style={styles.userInfo}>Welcome, {user?.username || 'User'}</span>
          <button onClick={logout} style={styles.logoutButton}>
            Logout
          </button>
        </div>
      </header>

      {error && (
        <div style={styles.errorBox}>
          {error}
          <button onClick={() => setError('')} style={styles.dismissButton}>
            ×
          </button>
        </div>
      )}

      {success && (
        <div style={styles.successBox}>
          {success}
          <button onClick={() => setSuccess('')} style={styles.dismissButton}>
            ×
          </button>
        </div>
      )}

      {/* Tabs */}
      <div style={styles.tabs}>
        <button
          onClick={() => setActiveTab('log')}
          style={{
            ...styles.tab,
            ...(activeTab === 'log' ? styles.tabActive : {}),
          }}
        >
          Log Habits
        </button>
        <button
          onClick={() => setActiveTab('calendar')}
          style={{
            ...styles.tab,
            ...(activeTab === 'calendar' ? styles.tabActive : {}),
          }}
        >
          Calendar
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          style={{
            ...styles.tab,
            ...(activeTab === 'analytics' ? styles.tabActive : {}),
          }}
        >
          Analytics
        </button>
      </div>

      {/* Tab Content */}
      {loading && activeTab !== 'calendar' && (
        <div style={styles.loadingBox}>Loading...</div>
      )}
      {activeTab === 'log' && renderLogHabitsTab()}
      {activeTab === 'calendar' && renderCalendarTab()}
      {activeTab === 'analytics' && renderAnalyticsTab()}
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
  navLinkButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  logoutButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  errorBox: {
    backgroundColor: '#f8d7da',
    color: '#721c24',
    padding: '1rem',
    margin: '1rem',
    borderRadius: '4px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  successBox: {
    backgroundColor: '#d4edda',
    color: '#155724',
    padding: '1rem',
    margin: '1rem',
    borderRadius: '4px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  dismissButton: {
    background: 'none',
    border: 'none',
    fontSize: '1.5rem',
    cursor: 'pointer',
    color: 'inherit',
  },
  tabs: {
    display: 'flex',
    backgroundColor: 'white',
    borderBottom: '2px solid #e0e0e0',
    padding: '0 1rem',
  },
  tab: {
    padding: '1rem 2rem',
    backgroundColor: 'transparent',
    border: 'none',
    borderBottom: '3px solid transparent',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '500',
    color: '#666',
    transition: 'all 0.2s',
  },
  tabActive: {
    color: '#007bff',
    borderBottomColor: '#007bff',
  },
  tabContent: {
    maxWidth: '1200px',
    margin: '2rem auto',
    padding: '0 1rem',
  },
  tabTitle: {
    marginTop: 0,
    marginBottom: '2rem',
    fontSize: '2rem',
    color: '#333',
  },
  formSection: {
    backgroundColor: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    marginBottom: '1.5rem',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  sectionTitle: {
    marginTop: 0,
    marginBottom: '1rem',
    fontSize: '1.3rem',
    color: '#333',
  },
  subsectionTitle: {
    marginTop: '1rem',
    marginBottom: '0.5rem',
    fontSize: '1.1rem',
    color: '#555',
  },
  label: {
    display: 'block',
    marginBottom: '0.5rem',
    fontWeight: '500',
    color: '#333',
  },
  dateInput: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
    width: '200px',
  },
  checkboxLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '0.5rem',
    cursor: 'pointer',
  },
  checkbox: {
    width: '18px',
    height: '18px',
    cursor: 'pointer',
  },
  numberInput: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
    width: '150px',
    marginLeft: '1rem',
  },
  unitLabel: {
    marginLeft: '0.5rem',
    color: '#666',
    fontSize: '0.9rem',
  },
  habitRow: {
    marginBottom: '1rem',
  },
  twoColumnInputs: {
    display: 'flex',
    gap: '1rem',
    marginLeft: '1rem',
    marginTop: '0.5rem',
  },
  buttonRow: {
    display: 'flex',
    gap: '1rem',
    justifyContent: 'flex-end',
    marginTop: '2rem',
  },
  primaryButton: {
    padding: '0.75rem 2rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '500',
  },
  secondaryButton: {
    padding: '0.75rem 2rem',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '500',
  },
  habitDetails: {
    marginBottom: '1rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    padding: '0.5rem',
  },
  habitSummary: {
    cursor: 'pointer',
    padding: '0.5rem',
    fontWeight: '500',
  },
  habitItem: {
    padding: '0.5rem',
    borderTop: '1px solid #eee',
  },
  habitItemContent: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  deleteButton: {
    padding: '0.25rem 0.5rem',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  deleteAllButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    marginTop: '1rem',
  },
  calendarNavigation: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  calendarTitle: {
    margin: 0,
    fontSize: '1.5rem',
  },
  navButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  viewSelector: {
    display: 'flex',
    gap: '0.5rem',
    marginBottom: '1.5rem',
  },
  viewButton: {
    padding: '0.5rem 1rem',
    backgroundColor: 'white',
    border: '1px solid #ddd',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  viewButtonActive: {
    backgroundColor: '#007bff',
    color: 'white',
    borderColor: '#007bff',
  },
  calendarGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(7, 1fr)',
    gap: '0.5rem',
    backgroundColor: 'white',
    padding: '1rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  calendarDayHeader: {
    textAlign: 'center',
    padding: '0.5rem',
    fontWeight: 'bold',
    color: '#666',
  },
  calendarDay: {
    minHeight: '80px',
    padding: '0.5rem',
    border: '1px solid #eee',
    borderRadius: '4px',
    backgroundColor: 'white',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
  },
  calendarDayToday: {
    backgroundColor: '#e3f2fd',
    borderColor: '#007bff',
    fontWeight: 'bold',
  },
  calendarIcons: {
    fontSize: '0.8rem',
    marginTop: '0.25rem',
  },
  quarterlyMonths: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '1rem',
  },
  quarterlyMonth: {
    backgroundColor: 'white',
    padding: '1rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  yearlyMonths: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '1rem',
  },
  yearlyMonth: {
    backgroundColor: 'white',
    padding: '1rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  singleMonth: {
    width: '100%',
  },
  monthHeader: {
    marginTop: 0,
    marginBottom: '0.5rem',
    fontSize: '1rem',
    textAlign: 'center',
  },
  miniCalendarGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(7, 1fr)',
    gap: '2px',
  },
  miniDayHeader: {
    textAlign: 'center',
    fontSize: '0.7rem',
    fontWeight: 'bold',
    color: '#666',
    padding: '0.25rem',
  },
  miniCalendarDay: {
    padding: '0.25rem',
    fontSize: '0.7rem',
    textAlign: 'center',
    border: '1px solid #eee',
    minHeight: '20px',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
  },
  miniCalendarDayToday: {
    backgroundColor: '#e3f2fd',
    fontWeight: 'bold',
  },
  miniIcons: {
    fontSize: '0.6rem',
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
    marginBottom: '1rem',
  },
  metricCard: {
    backgroundColor: '#f8f9fa',
    padding: '1.5rem',
    borderRadius: '8px',
    textAlign: 'center',
  },
  metricValue: {
    fontSize: '2rem',
    fontWeight: 'bold',
    color: '#007bff',
    marginBottom: '0.5rem',
  },
  metricLabel: {
    fontSize: '0.9rem',
    color: '#666',
  },
  breakdownSection: {
    marginTop: '1rem',
    padding: '1rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '4px',
  },
  breakdownList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  habitDistribution: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  habitDistributionItem: {
    padding: '0.5rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '4px',
  },
  select: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
    width: '200px',
  },
  infoBox: {
    backgroundColor: '#d1ecf1',
    color: '#0c5460',
    padding: '1rem',
    borderRadius: '4px',
    marginBottom: '1rem',
  },
  loadingBox: {
    textAlign: 'center',
    padding: '2rem',
    color: '#666',
  },
};
