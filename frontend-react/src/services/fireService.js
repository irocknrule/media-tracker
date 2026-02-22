import api from './api';

export const fireService = {
  // Accounts
  getAccounts: async (params = {}) => {
    const response = await api.get('/fire/accounts', { params });
    return response.data;
  },

  createAccount: async (data) => {
    const response = await api.post('/fire/accounts', data);
    return response.data;
  },

  updateAccount: async (id, data) => {
    const response = await api.put(`/fire/accounts/${id}`, data);
    return response.data;
  },

  deleteAccount: async (id) => {
    await api.delete(`/fire/accounts/${id}`);
  },

  bulkImportAccounts: async (data) => {
    const response = await api.post('/fire/accounts/bulk', data);
    return response.data;
  },

  // Snapshots
  getSnapshots: async (accountId) => {
    const response = await api.get(`/fire/accounts/${accountId}/snapshots`);
    return response.data;
  },

  bulkCreateSnapshots: async (data) => {
    const response = await api.post('/fire/snapshots/bulk', data);
    return response.data;
  },

  updateSnapshot: async (id, data) => {
    const response = await api.put(`/fire/snapshots/${id}`, data);
    return response.data;
  },

  deleteSnapshot: async (id) => {
    await api.delete(`/fire/snapshots/${id}`);
  },

  // Aggregate portfolio snapshots
  getAggregateSnapshots: async () => {
    const response = await api.get('/fire/aggregate-snapshots');
    return response.data;
  },

  createAggregateSnapshot: async (data) => {
    const response = await api.post('/fire/aggregate-snapshots', data);
    return response.data;
  },

  updateAggregateSnapshot: async (id, data) => {
    const response = await api.put(`/fire/aggregate-snapshots/${id}`, data);
    return response.data;
  },

  deleteAggregateSnapshot: async (id) => {
    await api.delete(`/fire/aggregate-snapshots/${id}`);
  },

  // Dashboard & Income
  getDashboard: async () => {
    const response = await api.get('/fire/dashboard');
    return response.data;
  },

  getIncomeHistory: async (interval = 'quarterly', accountIds = null) => {
    const params = { interval };
    if (accountIds && accountIds.length > 0) {
      params.account_ids = accountIds.join(',');
    }
    const response = await api.get('/fire/income-history', { params });
    return response.data;
  },
};
