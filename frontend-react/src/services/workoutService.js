import api from './api';

export const workoutService = {
  // Exercise endpoints
  getExercises: async (params = {}) => {
    const response = await api.get('/workouts/exercises', { params });
    return response.data;
  },

  getExercise: async (id) => {
    const response = await api.get(`/workouts/exercises/${id}`);
    return response.data;
  },

  createExercise: async (exerciseData) => {
    const response = await api.post('/workouts/exercises', exerciseData);
    return response.data;
  },

  updateExercise: async (id, exerciseData) => {
    const response = await api.put(`/workouts/exercises/${id}`, exerciseData);
    return response.data;
  },

  deleteExercise: async (id) => {
    await api.delete(`/workouts/exercises/${id}`);
  },

  getExerciseProgress: async (id, params = {}) => {
    const response = await api.get(`/workouts/exercises/${id}/progress`, { params });
    return response.data;
  },

  // Workout template endpoints
  getWorkouts: async (params = {}) => {
    const response = await api.get('/workouts/templates', { params });
    return response.data;
  },

  getWorkout: async (id) => {
    const response = await api.get(`/workouts/templates/${id}`);
    return response.data;
  },

  createWorkout: async (workoutData) => {
    const response = await api.post('/workouts/templates', workoutData);
    return response.data;
  },

  updateWorkout: async (id, workoutData) => {
    const response = await api.put(`/workouts/templates/${id}`, workoutData);
    return response.data;
  },

  deleteWorkout: async (id) => {
    await api.delete(`/workouts/templates/${id}`);
  },

  // Workout record endpoints
  getWorkoutRecords: async (params = {}) => {
    const response = await api.get('/workouts/records', { params });
    return response.data;
  },

  getWorkoutRecord: async (id) => {
    const response = await api.get(`/workouts/records/${id}`);
    return response.data;
  },

  createWorkoutRecord: async (recordData) => {
    const response = await api.post('/workouts/records', recordData);
    return response.data;
  },

  updateWorkoutRecord: async (id, recordData) => {
    const response = await api.put(`/workouts/records/${id}`, recordData);
    return response.data;
  },

  deleteWorkoutRecord: async (id) => {
    await api.delete(`/workouts/records/${id}`);
  },

  getLastWorkoutRecord: async (workoutId) => {
    const response = await api.get(`/workouts/records/${workoutId}/last`);
    return response.data;
  },

  // Analytics endpoints
  getWorkoutAnalytics: async (params = {}) => {
    const response = await api.get('/workouts/analytics/summary', { params });
    return response.data;
  },

  getPersonalRecords: async () => {
    const response = await api.get('/workouts/analytics/personal-records');
    return response.data;
  },
};
