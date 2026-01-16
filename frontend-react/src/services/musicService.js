import api from './api';

export const musicService = {
  getAll: async (params = {}) => {
    const response = await api.get('/music/', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/music/${id}`);
    return response.data;
  },

  create: async (musicData) => {
    const response = await api.post('/music/', musicData);
    return response.data;
  },

  update: async (id, musicData) => {
    const response = await api.put(`/music/${id}`, musicData);
    return response.data;
  },

  delete: async (id) => {
    await api.delete(`/music/${id}`);
  },
};
