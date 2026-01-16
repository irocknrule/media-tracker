import api from './api';

export const habitService = {
  // Get all habits with optional date filters
  getAll: async (startDate = null, endDate = null) => {
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const response = await api.get('/habits/', { params });
    return response.data;
  },

  // Get habits for a specific date
  getByDate: async (date) => {
    const response = await api.get(`/habits/date/${date}`);
    return response.data;
  },

  // Get detailed habits for a specific date (includes IDs for deletion)
  getByDateDetailed: async (date) => {
    const response = await api.get(`/habits/date/${date}/detailed`);
    return response.data;
  },

  // Get calendar entries
  getCalendar: async (startDate = null, endDate = null) => {
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const response = await api.get('/habits/calendar', { params });
    return response.data;
  },

  // Create habit logs (batch)
  create: async (date, logs) => {
    const response = await api.post('/habits/', {
      date,
      logs,
    });
    return response.data;
  },

  // Delete all habits for a date
  deleteByDate: async (date) => {
    const response = await api.delete(`/habits/date/${date}`);
    return response.data;
  },

  // Delete a specific habit log by ID
  delete: async (habitId) => {
    const response = await api.delete(`/habits/${habitId}`);
    return response.data;
  },

  // Get analytics summary
  getAnalytics: async (startDate = null, endDate = null) => {
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const response = await api.get('/habits/analytics/summary', { params });
    return response.data;
  },
};
