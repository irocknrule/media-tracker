import api from './api';

export const tvShowDetailsService = {
  search: async (query) => {
    try {
      const response = await api.get('/search/tv-shows', {
        params: { query },
      });
      return response.data.results || [];
    } catch (error) {
      console.error('TV show search error:', error);
      return [];
    }
  },

  getSeasons: async (tvmazeId) => {
    try {
      const response = await api.get(`/search/tv-shows/${tvmazeId}/seasons`);
      return response.data || [];
    } catch (error) {
      console.error('Error fetching TV show seasons:', error);
      return [];
    }
  },
};
