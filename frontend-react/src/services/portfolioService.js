import api from './api';

export const portfolioService = {
  // Summary
  getSummary: async () => {
    const response = await api.get('/portfolio/summary');
    return response.data;
  },

  // Transactions
  getTransactions: async (params = {}) => {
    const response = await api.get('/portfolio/transactions', { params });
    return response.data;
  },

  getTransaction: async (id) => {
    const response = await api.get(`/portfolio/transactions/${id}`);
    return response.data;
  },

  createTransaction: async (transactionData) => {
    const response = await api.post('/portfolio/transactions', transactionData);
    return response.data;
  },

  updateTransaction: async (id, transactionData) => {
    const response = await api.put(`/portfolio/transactions/${id}`, transactionData);
    return response.data;
  },

  deleteTransaction: async (id) => {
    await api.delete(`/portfolio/transactions/${id}`);
  },

  deleteAllTransactions: async () => {
    const response = await api.delete('/portfolio/transactions');
    return response.data;
  },

  uploadTransactions: async (data) => {
    const response = await api.post('/portfolio/transactions/upload', data);
    return response.data;
  },

  // Holdings
  getHoldings: async () => {
    const response = await api.get('/portfolio/holdings');
    return response.data;
  },

  getTickerHolding: async (ticker) => {
    const response = await api.get(`/portfolio/holdings/${ticker}`);
    return response.data;
  },

  // Tickers
  getTickers: async () => {
    const response = await api.get('/portfolio/tickers');
    return response.data;
  },

  // Splits
  getTickerSplits: async (ticker) => {
    const response = await api.get(`/portfolio/splits/${ticker}`);
    return response.data;
  },

  // Allocation
  getAllocationSummary: async () => {
    const response = await api.get('/portfolio/allocation/summary');
    return response.data;
  },

  getAllocationTargets: async () => {
    const response = await api.get('/portfolio/allocation/targets');
    return response.data;
  },

  createAllocationTarget: async (targetData) => {
    const response = await api.post('/portfolio/allocation/targets', targetData);
    return response.data;
  },

  updateAllocationTarget: async (category, targetData) => {
    const response = await api.put(`/portfolio/allocation/targets/${category}`, targetData);
    return response.data;
  },

  // Ticker Categories
  getTickerCategories: async () => {
    const response = await api.get('/portfolio/allocation/ticker-categories');
    return response.data;
  },

  getTickerCategory: async (ticker) => {
    const response = await api.get(`/portfolio/allocation/ticker-categories/${ticker}`);
    return response.data;
  },

  updateTickerCategory: async (ticker, categoryData) => {
    const response = await api.put(`/portfolio/allocation/ticker-categories/${ticker}`, categoryData);
    return response.data;
  },

  recategorizeTicker: async (ticker) => {
    const response = await api.post(`/portfolio/allocation/ticker-categories/recategorize/${ticker}`);
    return response.data;
  },
};
