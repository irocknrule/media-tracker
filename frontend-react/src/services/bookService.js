import api from './api';

export const bookService = {
  getAll: async (params = {}) => {
    const response = await api.get('/books/', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/books/${id}`);
    return response.data;
  },

  create: async (bookData) => {
    const response = await api.post('/books/', bookData);
    return response.data;
  },

  update: async (id, bookData) => {
    const response = await api.put(`/books/${id}`, bookData);
    return response.data;
  },

  delete: async (id) => {
    await api.delete(`/books/${id}`);
  },
};
