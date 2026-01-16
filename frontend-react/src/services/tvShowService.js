import api from './api';

export const tvShowService = {
  getAll: async (params = {}) => {
    const response = await api.get('/tv-shows/', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/tv-shows/${id}`);
    return response.data;
  },

  create: async (showData) => {
    const response = await api.post('/tv-shows/', showData);
    return response.data;
  },

  update: async (id, showData) => {
    const response = await api.put(`/tv-shows/${id}`, showData);
    return response.data;
  },

  delete: async (id) => {
    await api.delete(`/tv-shows/${id}`);
  },

  // Season endpoints
  getSeasons: async (showId) => {
    const response = await api.get(`/tv-shows/${showId}/seasons`);
    return response.data;
  },

  getSeason: async (seasonId) => {
    const response = await api.get(`/tv-shows/seasons/${seasonId}`);
    return response.data;
  },

  createSeason: async (seasonData) => {
    const response = await api.post('/tv-shows/seasons', seasonData);
    return response.data;
  },

  updateSeason: async (seasonId, seasonData) => {
    const response = await api.put(`/tv-shows/seasons/${seasonId}`, seasonData);
    return response.data;
  },

  deleteSeason: async (seasonId) => {
    await api.delete(`/tv-shows/seasons/${seasonId}`);
  },

  // Legacy endpoint for backward compatibility
  createLegacy: async (showData) => {
    const response = await api.post('/tv-shows/legacy', showData);
    return response.data;
  },
};
