import api, { apiBaseUrl } from './api';

export const internetUsageService = {
  list: async (params = {}) => {
    const response = await api.get('/internet-usage', { params });
    return response.data;
  },

  upsertMonth: async (data) => {
    const response = await api.put('/internet-usage/month', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/internet-usage/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    await api.delete(`/internet-usage/${id}`);
  },

  /**
   * Upload an eero (or similar) screenshot; server runs OCR and returns suggested fields.
   */
  parseEeroScreenshot: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const token = localStorage.getItem('token');
    const res = await fetch(`${apiBaseUrl}/internet-usage/parse-eero-screenshot`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    const text = await res.text();
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      throw new Error(text || res.statusText);
    }
    if (!res.ok) {
      const detail = data.detail;
      const msg =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map((d) => d.msg || d).join('; ')
            : res.statusText;
      throw new Error(msg || 'Upload failed');
    }
    return data;
  },
};
