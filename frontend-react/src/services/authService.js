import api from './api';

export const authService = {
  login: async (username, password) => {
    // The FastAPI endpoint uses plain str parameters, which means FastAPI
    // will look for them in query params, form data, or JSON body
    // Since OAuth2PasswordBearer is used, let's try form data first
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    try {
      // Try form data (OAuth2 standard)
      const response = await api.post(
        '/auth/login',
        formData.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );
      
      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
      }
      
      return response.data;
    } catch (error) {
      // If form data fails with validation error, try JSON
      // FastAPI should accept JSON for plain str parameters
      if (error.response?.status === 422) {
        console.log('Form data failed, trying JSON...');
        const jsonResponse = await api.post('/auth/login', {
          username,
          password,
        });
        
        if (jsonResponse.data.access_token) {
          localStorage.setItem('token', jsonResponse.data.access_token);
        }
        
        return jsonResponse.data;
      }
      throw error;
    }
  },

  logout: async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
    }
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  },
};
