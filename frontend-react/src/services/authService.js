import api from './api';

export const authService = {
  login: async (username, password) => {
    // FastAPI OAuth2PasswordBearer expects form data with username and password
    // Create form data properly
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    try {
      // Send as form data (OAuth2 standard for password flow)
      const response = await api.post(
        '/auth/login',
        formData.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );
      
      if (response.data && response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
      }
      
      return response.data;
    } catch (error) {
      // If form data fails, try JSON body (some FastAPI setups accept this)
      if (error.response?.status === 422 || error.response?.status === 400) {
        try {
          const jsonResponse = await api.post('/auth/login', {
            username,
            password,
          }, {
            headers: {
              'Content-Type': 'application/json',
            },
          });
          
          if (jsonResponse.data && jsonResponse.data.access_token) {
            localStorage.setItem('token', jsonResponse.data.access_token);
          }
          
          return jsonResponse.data;
        } catch (jsonError) {
          // If both fail, throw the original error
          throw error;
        }
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
