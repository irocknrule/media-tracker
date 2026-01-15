import api from './api';

export const searchService = {
  searchMovies: async (query) => {
    if (!query || query.length < 2) {
      return [];
    }
    
    try {
      const response = await api.get('/search/movies', {
        params: { query },
      });
      return response.data.results || [];
    } catch (error) {
      console.error('Search error:', error);
      return [];
    }
  },
};
