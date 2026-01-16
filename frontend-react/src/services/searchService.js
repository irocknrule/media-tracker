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

  searchTVShows: async (query) => {
    if (!query || query.length < 2) {
      return [];
    }
    
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

  searchBooks: async (query) => {
    if (!query || query.length < 2) {
      return [];
    }
    
    try {
      const response = await api.get('/search/books', {
        params: { query },
      });
      return response.data.results || [];
    } catch (error) {
      console.error('Book search error:', error);
      return [];
    }
  },

  searchMusic: async (query) => {
    if (!query || query.length < 2) {
      return [];
    }
    
    try {
      const response = await api.get('/search/music', {
        params: { query },
      });
      return response.data.results || [];
    } catch (error) {
      console.error('Music search error:', error);
      return [];
    }
  },
};
