import api from './api';

export const movieDetailsService = {
  getDetails: async (title, year = null) => {
    try {
      const params = { title };
      if (year) {
        params.year = year;
      }
      const response = await api.get('/search/movies/details', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching movie details:', error);
      throw error;
    }
  },
};
