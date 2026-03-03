import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { portfolioService } from '../services/portfolioService';
import { getErrorMessage } from '../utils/errorHandler';
import { formatCurrency, formatCurrencyPrecise, formatPercent } from '../utils/formatters';
import ConfirmModal from '../components/ConfirmModal';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
  Treemap,
} from 'recharts';

export default function Portfolio() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'overview';
  const urlTicker = searchParams.get('ticker') || '';
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [confirmModal, setConfirmModal] = useState(null);

  const setActiveTab = (tab) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (tab === 'overview') {
        next.delete('tab');
      } else {
        next.set('tab', tab);
      }
      next.delete('ticker');
      return next;
    });
  };

  const navigateToTicker = (ticker) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('tab', 'holdings');
      if (ticker) {
        next.set('ticker', ticker);
      }
      return next;
    });
  };

  // Overview state
  const [summary, setSummary] = useState(null);
  const [showDeleteAll, setShowDeleteAll] = useState(false);
  const [confirmDeleteAll, setConfirmDeleteAll] = useState(false);
  const [transactionCount, setTransactionCount] = useState(0);

  // Transactions state
  const [transactions, setTransactions] = useState([]);
  const [tickerFilter, setTickerFilter] = useState('');
  const [assetTypeFilter, setAssetTypeFilter] = useState('All');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState(null);
  const [transactionFormData, setTransactionFormData] = useState({
    ticker: '',
    transaction_type: 'BUY',
    asset_type: 'STOCK',
    transaction_date: new Date().toISOString().split('T')[0],
    quantity: 0,
    price_per_unit: 0,
    total_amount: 0,
    fees: 0,
    notes: '',
  });

  // Upload state
  const [uploadMethod, setUploadMethod] = useState('file'); // 'file' or 'paste'
  const [uploadedFile, setUploadedFile] = useState(null);
  const [jsonInput, setJsonInput] = useState('');
  const [uploadResult, setUploadResult] = useState(null);

  // Individual Holdings state
  const [tickers, setTickers] = useState([]);
  const [selectedTicker, setSelectedTicker] = useState('');
  const [tickerHolding, setTickerHolding] = useState(null);
  const [tickerTransactions, setTickerTransactions] = useState([]);
  const [splits, setSplits] = useState({});
  const [selectedTransactions, setSelectedTransactions] = useState(new Set());
  const [editingTxnId, setEditingTxnId] = useState(null);
  const [confirmDeleteTicker, setConfirmDeleteTicker] = useState(false);
  const [quickAddFormData, setQuickAddFormData] = useState({
    ticker: '',
    transaction_type: 'BUY',
    asset_type: 'STOCK',
    transaction_date: new Date().toISOString().split('T')[0],
    quantity: 0,
    price_per_unit: 0,
    total_amount: 0,
    fees: 0,
    notes: '',
  });

  // Allocation state
  const [allocationSummary, setAllocationSummary] = useState(null);
  const [allocationTargets, setAllocationTargets] = useState([]);
  const [tickerCategories, setTickerCategories] = useState([]);
  const [allocationTab, setAllocationTab] = useState('summary'); // 'summary', 'settings', 'categories'

  // Yearly investments state
  const [yearlyInvestments, setYearlyInvestments] = useState([]);
  const [expandedYear, setExpandedYear] = useState(null);
  const [tickerSortKey, setTickerSortKey] = useState('total_amount');
  const [tickerSortDir, setTickerSortDir] = useState('desc');

  // Value history state (C4)
  const [valueHistory, setValueHistory] = useState(null);

  // Benchmark state (C3)
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [benchmarkTicker, setBenchmarkTicker] = useState('SPY');

  // Pagination state (D5)
  const [currentPage, setCurrentPage] = useState(1);
  const transactionsPerPage = 50;

  // Top Performers state
  const [performanceData, setPerformanceData] = useState(null);
  const [performanceTimeframe, setPerformanceTimeframe] = useState('all');
  const [perfSortKey, setPerfSortKey] = useState('period_return_pct');
  const [perfSortDir, setPerfSortDir] = useState('desc');
  const [returnMode, setReturnMode] = useState('market'); // 'market' or 'personal'

  const perfView = useMemo(() => {
    if (!performanceData) return null;
    const isPersonal = returnMode === 'personal';
    const tickers = performanceData.tickers.map((t) => ({
      ...t,
      activeReturnPct: isPersonal ? t.all_time_return_pct : t.period_return_pct,
      activeDollarChange: isPersonal ? t.all_time_dollar_change : t.period_dollar_change,
    }));
    tickers.sort((a, b) => (b.activeReturnPct ?? -9999) - (a.activeReturnPct ?? -9999));

    let portfolioReturnPct = performanceData.portfolio_period_return_pct;
    let portfolioDollarChange = performanceData.portfolio_period_dollar_change;
    if (isPersonal) {
      const totalInvested = performanceData.portfolio_total_invested;
      const totalCurrent = performanceData.portfolio_current_value;
      if (totalInvested > 0 && totalCurrent != null) {
        portfolioDollarChange = totalCurrent - totalInvested;
        portfolioReturnPct = (portfolioDollarChange / totalInvested) * 100;
      } else {
        portfolioReturnPct = null;
        portfolioDollarChange = null;
      }
    }

    return { tickers, portfolioReturnPct, portfolioDollarChange };
  }, [performanceData, returnMode]);

  useEffect(() => {
    if (activeTab === 'overview') {
      loadSummary();
    } else if (activeTab === 'transactions') {
      loadTransactions();
    } else if (activeTab === 'upload') {
      // Reset upload state
      setUploadResult(null);
    } else if (activeTab === 'holdings') {
      loadTickers();
    } else if (activeTab === 'allocation') {
      loadAllocationData();
    } else if (activeTab === 'yearly') {
      loadYearlyInvestments();
    } else if (activeTab === 'performers') {
      loadPerformance(performanceTimeframe);
    }
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === 'holdings' && selectedTicker) {
      loadTickerDetails();
    }
  }, [selectedTicker, activeTab]);

  useEffect(() => {
    if (urlTicker && urlTicker !== selectedTicker) {
      setSelectedTicker(urlTicker);
    }
  }, [urlTicker]);

  useEffect(() => {
    if (tickerHolding && selectedTicker) {
      setQuickAddFormData((prev) => ({
        ...prev,
        ticker: selectedTicker,
        asset_type: tickerHolding.asset_type,
      }));
    }
  }, [tickerHolding, selectedTicker]);

  const loadSummary = async () => {
    try {
      setLoading(true);
      setError('');
      const [data, txnData, histData] = await Promise.all([
        portfolioService.getSummary(),
        portfolioService.getTransactions(),
        portfolioService.getValueHistory().catch(() => ({ history: [] })),
      ]);
      setSummary(data);
      setTransactionCount(txnData.length || 0);
      setValueHistory(histData.history || []);
    } catch (err) {
      console.error('Error loading summary:', err);
      setError(getErrorMessage(err) || 'Failed to load portfolio summary');
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      const data = await portfolioService.exportTransactions();
      if (!data.rows || data.rows.length === 0) {
        setError('No transactions to export');
        return;
      }
      const headers = Object.keys(data.rows[0]);
      const csv = [
        headers.join(','),
        ...data.rows.map(row => headers.map(h => {
          const val = String(row[h] ?? '');
          return val.includes(',') || val.includes('"') ? `"${val.replace(/"/g, '""')}"` : val;
        }).join(',')),
      ].join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `portfolio_transactions_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to export transactions');
    }
  };

  const loadTransactions = async () => {
    setCurrentPage(1);
    try {
      setLoading(true);
      setError('');
      const params = {};
      if (tickerFilter) params.ticker = tickerFilter.toUpperCase();
      if (assetTypeFilter !== 'All') params.asset_type = assetTypeFilter;
      
      const data = await portfolioService.getTransactions(params);
      setTransactions(data || []);
    } catch (err) {
      console.error('Error loading transactions:', err);
      setError(getErrorMessage(err) || 'Failed to load transactions');
    } finally {
      setLoading(false);
    }
  };

  const loadTickers = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await portfolioService.getTickers();
      setTickers(data || []);
      if (data && data.length > 0 && !selectedTicker) {
        setSelectedTicker(data[0]);
      }
    } catch (err) {
      console.error('Error loading tickers:', err);
      setError(getErrorMessage(err) || 'Failed to load tickers');
    } finally {
      setLoading(false);
    }
  };

  const loadTickerDetails = async () => {
    if (!selectedTicker) return;
    
    try {
      setLoading(true);
      setError('');
      
      const [holding, txnData, splitsData] = await Promise.all([
        portfolioService.getTickerHolding(selectedTicker),
        portfolioService.getTransactions({ ticker: selectedTicker }),
        portfolioService.getTickerSplits(selectedTicker).catch(() => ({ splits: {} })),
      ]);
      
      setTickerHolding(holding);
      setTickerTransactions(txnData || []);
      setSplits(splitsData.splits || {});
    } catch (err) {
      console.error('Error loading ticker details:', err);
      setError(getErrorMessage(err) || 'Failed to load ticker details');
    } finally {
      setLoading(false);
    }
  };

  const loadAllocationData = async () => {
    try {
      setLoading(true);
      setError('');
      
      const [summaryData, targetsData, categoriesData] = await Promise.all([
        portfolioService.getAllocationSummary().catch(() => null),
        portfolioService.getAllocationTargets(),
        portfolioService.getTickerCategories(),
      ]);
      
      setAllocationSummary(summaryData);
      setAllocationTargets(targetsData || []);
      setTickerCategories(categoriesData || []);
    } catch (err) {
      console.error('Error loading allocation data:', err);
      // Don't set error for 404 on summary - it's expected if targets aren't set up
      if (err.response?.status !== 404) {
        setError(getErrorMessage(err) || 'Failed to load allocation data');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadYearlyInvestments = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await portfolioService.getYearlyInvestments();
      setYearlyInvestments(data || []);
    } catch (err) {
      console.error('Error loading yearly investments:', err);
      setError(getErrorMessage(err) || 'Failed to load yearly investments');
    } finally {
      setLoading(false);
    }
  };

  const loadPerformance = async (tf) => {
    try {
      setLoading(true);
      setError('');
      const [data, bench] = await Promise.all([
        portfolioService.getPerformance(tf),
        portfolioService.getBenchmark(benchmarkTicker, tf).catch(() => null),
      ]);
      setPerformanceData(data);
      setBenchmarkData(bench);
    } catch (err) {
      console.error('Error loading performance:', err);
      setError(getErrorMessage(err) || 'Failed to load performance data');
    } finally {
      setLoading(false);
    }
  };

  const handleTimeframeChange = (tf) => {
    setPerformanceTimeframe(tf);
    loadPerformance(tf);
  };

  const handleDeleteAllTransactions = async () => {
    if (!confirmDeleteAll) return;
    
    try {
      setLoading(true);
      setError('');
      const result = await portfolioService.deleteAllTransactions();
      setShowDeleteAll(false);
      setConfirmDeleteAll(false);
      loadSummary();
    } catch (err) {
      console.error('Error deleting all transactions:', err);
      setError(getErrorMessage(err) || 'Failed to delete all transactions');
    } finally {
      setLoading(false);
    }
  };

  const handleAddTransaction = async (e) => {
    e.preventDefault();
    
    if (!transactionFormData.ticker || !transactionFormData.quantity || 
        !transactionFormData.price_per_unit || !transactionFormData.total_amount) {
      setError('Please fill in all required fields');
      return;
    }
    
    try {
      setLoading(true);
      setError('');
      await portfolioService.createTransaction({
        ...transactionFormData,
        ticker: transactionFormData.ticker.toUpperCase(),
      });
      
      // Reset form
      setTransactionFormData({
        ticker: '',
        transaction_type: 'BUY',
        asset_type: 'STOCK',
        transaction_date: new Date().toISOString().split('T')[0],
        quantity: 0,
        price_per_unit: 0,
        total_amount: 0,
        fees: 0,
        notes: '',
      });
      setShowAddForm(false);
      
      // Reload data
      if (activeTab === 'transactions') {
        loadTransactions();
      } else if (activeTab === 'holdings' && selectedTicker) {
        loadTickerDetails();
      }
    } catch (err) {
      console.error('Error adding transaction:', err);
      setError(getErrorMessage(err) || 'Failed to add transaction');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateTransaction = async (id, updateData) => {
    try {
      setLoading(true);
      setError('');
      await portfolioService.updateTransaction(id, updateData);
      setEditingTxnId(null);
      
      // Reload data
      if (activeTab === 'transactions') {
        loadTransactions();
      } else if (activeTab === 'holdings' && selectedTicker) {
        loadTickerDetails();
      }
    } catch (err) {
      console.error('Error updating transaction:', err);
      setError(getErrorMessage(err) || 'Failed to update transaction');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTransaction = (id) => {
    setConfirmModal({
      title: 'Delete Transaction',
      message: 'Are you sure you want to delete this transaction?',
      danger: true,
      onConfirm: async () => {
        setConfirmModal(null);
        try {
          setLoading(true);
          setError('');
          await portfolioService.deleteTransaction(id);
          if (activeTab === 'transactions') {
            loadTransactions();
          } else if (activeTab === 'holdings' && selectedTicker) {
            loadTickerDetails();
          }
        } catch (err) {
          console.error('Error deleting transaction:', err);
          setError(getErrorMessage(err) || 'Failed to delete transaction');
        } finally {
          setLoading(false);
        }
      },
    });
  };

  const handleDeleteTickerTransactions = async () => {
    if (!confirmDeleteTicker || !selectedTicker) return;
    
    try {
      setLoading(true);
      setError('');
      
      const txns = await portfolioService.getTransactions({ ticker: selectedTicker });
      let deletedCount = 0;
      
      for (const txn of txns) {
        try {
          await portfolioService.deleteTransaction(txn.id);
          deletedCount++;
        } catch (err) {
          console.error(`Error deleting transaction ${txn.id}:`, err);
        }
      }
      
      setConfirmDeleteTicker(false);
      loadTickers();
      setSelectedTicker('');
    } catch (err) {
      console.error('Error deleting ticker transactions:', err);
      setError(getErrorMessage(err) || 'Failed to delete ticker transactions');
    } finally {
      setLoading(false);
    }
  };

  const handleBulkDeleteTransactions = () => {
    if (selectedTransactions.size === 0) return;
    setConfirmModal({
      title: 'Delete Selected Transactions',
      message: `Are you sure you want to delete ${selectedTransactions.size} selected transaction(s)?`,
      danger: true,
      onConfirm: async () => {
        setConfirmModal(null);
        try {
          setLoading(true);
          setError('');
          let deletedCount = 0;
          for (const id of selectedTransactions) {
            try {
              await portfolioService.deleteTransaction(id);
              deletedCount++;
            } catch (err) {
              console.error(`Error deleting transaction ${id}:`, err);
            }
          }
          setSelectedTransactions(new Set());
          setError('');
          loadTickerDetails();
        } catch (err) {
          console.error('Error bulk deleting transactions:', err);
          setError(getErrorMessage(err) || 'Failed to delete transactions');
        } finally {
          setLoading(false);
        }
      },
    });
  };

  const handleFileUpload = async () => {
    if (!uploadedFile) {
      setError('Please select a file first');
      return;
    }
    
    try {
      setLoading(true);
      setError('');
      const fileContent = await uploadedFile.text();
      const data = JSON.parse(fileContent);
      
      const result = await portfolioService.uploadTransactions(data);
      
      // API returns { transactions, created_count, duplicates_count }
      const createdCount = typeof result?.created_count === 'number' ? result.created_count : (Array.isArray(result) ? result.length : (result.created || []).length);
      const duplicatesCount = typeof result?.duplicates_count === 'number' ? result.duplicates_count : (Array.isArray(result) ? 0 : (result.duplicates || []).length);
      const total = (result?.transactions?.length ?? (Array.isArray(result) ? result.length : 0)) || (createdCount + duplicatesCount);
      
      setUploadResult({
        created: createdCount,
        duplicates: duplicatesCount,
        total: total || createdCount + duplicatesCount,
        details: result,
      });
      
      setUploadedFile(null);
      
      // Reload summary if on overview
      if (activeTab === 'overview') {
        loadSummary();
      }
    } catch (err) {
      console.error('Error uploading file:', err);
      if (err instanceof SyntaxError) {
        setError('Invalid JSON file: ' + err.message);
      } else {
        setError(getErrorMessage(err) || 'Failed to upload transactions');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleJsonUpload = async () => {
    if (!jsonInput.trim()) {
      setError('Please paste JSON data first');
      return;
    }
    
    try {
      setLoading(true);
      setError('');
      const data = JSON.parse(jsonInput);
      
      const result = await portfolioService.uploadTransactions(data);
      
      // API returns { transactions, created_count, duplicates_count }
      const createdCount = typeof result?.created_count === 'number' ? result.created_count : (Array.isArray(result) ? result.length : (result.created || []).length);
      const duplicatesCount = typeof result?.duplicates_count === 'number' ? result.duplicates_count : (Array.isArray(result) ? 0 : (result.duplicates || []).length);
      const total = (result?.transactions?.length ?? (Array.isArray(result) ? result.length : 0)) || (createdCount + duplicatesCount);
      
      setUploadResult({
        created: createdCount,
        duplicates: duplicatesCount,
        total: total || createdCount + duplicatesCount,
        details: result,
      });
      
      setJsonInput('');
      
      // Reload summary if on overview
      if (activeTab === 'overview') {
        loadSummary();
      }
    } catch (err) {
      console.error('Error uploading JSON:', err);
      if (err instanceof SyntaxError) {
        setError('Invalid JSON format: ' + err.message);
      } else {
        setError(getErrorMessage(err) || 'Failed to upload transactions');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateAllocationTarget = async (category, targetData) => {
    try {
      setLoading(true);
      setError('');
      await portfolioService.updateAllocationTarget(category, targetData);
      loadAllocationData();
    } catch (err) {
      console.error('Error updating allocation target:', err);
      setError(getErrorMessage(err) || 'Failed to update allocation target');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateTickerCategory = async (ticker, categoryData) => {
    try {
      setLoading(true);
      setError('');
      await portfolioService.updateTickerCategory(ticker, categoryData);
      loadAllocationData();
    } catch (err) {
      console.error('Error updating ticker category:', err);
      setError(getErrorMessage(err) || 'Failed to update ticker category');
    } finally {
      setLoading(false);
    }
  };

  const handleRecategorizeTicker = async (ticker) => {
    try {
      setLoading(true);
      setError('');
      await portfolioService.recategorizeTicker(ticker);
      loadAllocationData();
    } catch (err) {
      console.error('Error recategorizing ticker:', err);
      setError(getErrorMessage(err) || 'Failed to recategorize ticker');
    } finally {
      setLoading(false);
    }
  };

  // Calculate cumulative gain/loss timeline data
  const calculateCumulativeGainLoss = useMemo(() => {
    if (!tickerHolding || !tickerTransactions || tickerTransactions.length === 0) {
      return [];
    }

    const timelineData = [];
    const purchaseLots = []; // {quantity, price_per_unit, total_cost, date}

    // Get current market price
    let currentMarketPrice = tickerHolding.current_price;
    if (!currentMarketPrice && tickerTransactions.length > 0) {
      // Fallback to last transaction price
      const sortedTxns = [...tickerTransactions].sort(
        (a, b) => new Date(a.transaction_date) - new Date(b.transaction_date)
      );
      currentMarketPrice = sortedTxns[sortedTxns.length - 1].price_per_unit;
    }

    // Sort transactions by date
    const sortedTransactions = [...tickerTransactions].sort(
      (a, b) => new Date(a.transaction_date) - new Date(b.transaction_date)
    );

    // Apply split adjustments to historical transactions BEFORE calculating
    // This ensures we're comparing post-split prices with post-split current price
    const adjustedTransactions = sortedTransactions.map((txn) => {
      const txnDate = new Date(txn.transaction_date);
      let splitRatio = 1.0;

      // Calculate cumulative split ratio for splits that happened AFTER this transaction
      if (splits && Object.keys(splits).length > 0) {
        for (const [splitDateStr, ratio] of Object.entries(splits)) {
          try {
            const splitDate = new Date(splitDateStr);
            // If split happened AFTER this transaction, apply it
            if (splitDate > txnDate) {
              splitRatio *= ratio;
            }
          } catch (e) {
            // Skip invalid dates
            continue;
          }
        }
      }

      // Apply split adjustment: quantity increases, price decreases, total stays same
      if (splitRatio !== 1.0) {
        return {
          ...txn,
          quantity: txn.quantity * splitRatio,
          price_per_unit: txn.price_per_unit / splitRatio,
          // total_amount stays the same (quantity × price remains constant)
        };
      }

      return txn;
    });

    // Process each adjusted transaction
    for (const txn of adjustedTransactions) {
      const txnDate = txn.transaction_date;
      const txnType = txn.transaction_type;
      const quantity = txn.quantity;
      const price = txn.price_per_unit;
      const totalCost = txn.total_amount + (txn.fees || 0);

      if (txnType === 'BUY') {
        // Add this purchase lot
        purchaseLots.push({
          quantity,
          price_per_unit: price,
          total_cost: totalCost,
          date: txnDate,
        });
      } else if (txnType === 'SELL') {
        // Remove sold shares using FIFO
        let remainingToSell = quantity;

        while (remainingToSell > 0 && purchaseLots.length > 0) {
          const lot = purchaseLots[0];
          const lotQuantity = lot.quantity;

          if (lotQuantity <= remainingToSell) {
            // Sell entire lot
            remainingToSell -= lotQuantity;
            purchaseLots.shift();
          } else {
            // Sell partial lot
            const soldRatio = remainingToSell / lotQuantity;
            lot.quantity -= remainingToSell;
            lot.total_cost -= lot.total_cost * soldRatio;
            remainingToSell = 0;
          }
        }
      }

      // Calculate cumulative gain/loss: sum of each lot's contribution
      let cumulativeGainLoss = 0.0;
      let totalQuantity = 0.0;
      let totalCostBasis = 0.0;

      if (currentMarketPrice) {
        for (const lot of purchaseLots) {
          const lotCurrentValue = lot.quantity * currentMarketPrice;
          const lotGainLoss = lotCurrentValue - lot.total_cost;
          cumulativeGainLoss += lotGainLoss;
          totalQuantity += lot.quantity;
          totalCostBasis += lot.total_cost;
        }
      } else {
        totalQuantity = purchaseLots.reduce((sum, lot) => sum + lot.quantity, 0);
        totalCostBasis = purchaseLots.reduce((sum, lot) => sum + lot.total_cost, 0);
      }

      const avgCostBasis = totalQuantity > 0 ? totalCostBasis / totalQuantity : 0;

      timelineData.push({
        date: txnDate,
        quantity: totalQuantity,
        avgCost: avgCostBasis,
        invested: totalCostBasis,
        cumulativeGainLoss,
        transactionType: txnType,
        transactionQuantity: quantity,
        transactionPrice: price,
      });
    }

    // Add final data point with current price if available
    // The final cumulative should match the tickerHolding's profit_loss
    if (currentMarketPrice && timelineData.length > 0) {
      const lastEntry = timelineData[timelineData.length - 1];
      const finalDate = new Date().toISOString().split('T')[0];

      // Recalculate cumulative with current price
      let finalCumulative = 0.0;
      let finalQuantity = 0.0;
      let finalCostBasis = 0.0;
      
      for (const lot of purchaseLots) {
        const lotCurrentValue = lot.quantity * currentMarketPrice;
        const lotGainLoss = lotCurrentValue - lot.total_cost;
        finalCumulative += lotGainLoss;
        finalQuantity += lot.quantity;
        finalCostBasis += lot.total_cost;
      }

      // Use the backend's calculated profit_loss if available (it's more accurate)
      // Otherwise use our calculated value
      const finalGainLoss = tickerHolding.profit_loss !== null && tickerHolding.profit_loss !== undefined
        ? tickerHolding.profit_loss
        : finalCumulative;

      timelineData.push({
        date: finalDate,
        quantity: finalQuantity || lastEntry.quantity,
        avgCost: finalQuantity > 0 ? finalCostBasis / finalQuantity : lastEntry.avgCost,
        invested: finalCostBasis || lastEntry.invested,
        cumulativeGainLoss: finalGainLoss,
        transactionType: 'CURRENT',
        transactionQuantity: 0,
        transactionPrice: currentMarketPrice,
      });
    }

    return timelineData;
  }, [tickerHolding, tickerTransactions, splits]);

  return (
    <div style={styles.container}>
      {confirmModal && (
        <ConfirmModal
          title={confirmModal.title}
          message={confirmModal.message}
          danger={confirmModal.danger}
          confirmLabel={confirmModal.confirmLabel || 'Delete'}
          onConfirm={confirmModal.onConfirm}
          onCancel={() => setConfirmModal(null)}
        />
      )}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <button
            onClick={() => navigate('/')}
            style={styles.homeButton}
            title="Go to Home"
          >
            🏠
          </button>
          <h1 style={styles.title}>💼 Portfolio Tracker</h1>
        </div>
        <div style={styles.headerActions}>
          <span style={styles.userInfo}>Welcome, {user?.username || 'User'}</span>
          <button onClick={logout} style={styles.logoutButton}>
            Logout
          </button>
        </div>
      </header>

      <div style={styles.content}>
        {/* Tabs */}
        <div style={styles.tabs}>
          <button
            style={{
              ...styles.tab,
              ...(activeTab === 'overview' ? styles.tabActive : {}),
            }}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            style={{
              ...styles.tab,
              ...(activeTab === 'allocation' ? styles.tabActive : {}),
            }}
            onClick={() => setActiveTab('allocation')}
          >
            Asset Allocation
          </button>
          <button
            style={{
              ...styles.tab,
              ...(activeTab === 'transactions' ? styles.tabActive : {}),
            }}
            onClick={() => setActiveTab('transactions')}
          >
            Transactions
          </button>
          <button
            style={{
              ...styles.tab,
              ...(activeTab === 'upload' ? styles.tabActive : {}),
            }}
            onClick={() => setActiveTab('upload')}
          >
            Upload Data
          </button>
          <button
            style={{
              ...styles.tab,
              ...(activeTab === 'holdings' ? styles.tabActive : {}),
            }}
            onClick={() => setActiveTab('holdings')}
          >
            Individual Holdings
          </button>
          <button
            style={{
              ...styles.tab,
              ...(activeTab === 'yearly' ? styles.tabActive : {}),
            }}
            onClick={() => setActiveTab('yearly')}
          >
            Yearly Investments
          </button>
          <button
            style={{
              ...styles.tab,
              ...(activeTab === 'performers' ? styles.tabActive : {}),
            }}
            onClick={() => setActiveTab('performers')}
          >
            Top Performers
          </button>
        </div>

        {error && (
          <div style={styles.error}>
            {error}
            <button onClick={() => setError('')} style={styles.errorClose}>×</button>
          </div>
        )}

        {loading && <div style={styles.loading}>Loading...</div>}

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div style={styles.tabContent}>
            <h2 style={styles.sectionTitle}>📊 Portfolio Summary</h2>
            
            {summary && (
              <>
                <div style={styles.metricsGrid}>
                  <div style={styles.metricCard}>
                    <div style={styles.metricLabel}>Total Invested</div>
                    <div style={styles.metricValue}>
                      {formatCurrency(summary.total_invested)}
                    </div>
                  </div>
                  <div style={styles.metricCard}>
                    <div style={styles.metricLabel}>Current Value</div>
                    <div style={styles.metricValue}>
                      {summary.current_value !== null
                        ? formatCurrency(summary.current_value)
                        : 'N/A'}
                    </div>
                  </div>
                  <div style={styles.metricCard}>
                    <div style={styles.metricLabel}>Total P/L</div>
                    <div style={{
                      ...styles.metricValue,
                      color: summary.total_profit_loss >= 0 ? '#00cc88' : '#ff4444',
                    }}>
                      {summary.total_profit_loss !== null
                        ? `${formatCurrency(summary.total_profit_loss)} (${formatPercent(summary.total_profit_loss_percentage)})`
                        : 'N/A'}
                    </div>
                  </div>
                  <div style={styles.metricCard}>
                    <div style={styles.metricLabel}># Holdings</div>
                    <div style={styles.metricValue}>
                      {summary.holdings?.length || 0}
                    </div>
                  </div>
                </div>

                {valueHistory && valueHistory.length > 1 && (
                  <div style={styles.section}>
                    <h3 style={styles.subsectionTitle}>Portfolio Value Over Time</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={valueHistory}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.2)" />
                        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                        <YAxis tickFormatter={v => v >= 1000000 ? `$${(v / 1000000).toFixed(1)}M` : `$${(v / 1000).toFixed(0)}k`} />
                        <Tooltip formatter={(value) => [formatCurrency(value)]} />
                        <Area type="monotone" dataKey="total_invested" stroke="#6c757d" fill="#6c757d" fillOpacity={0.1} name="Total Invested" />
                        <Area type="monotone" dataKey="current_value" stroke="#007bff" fill="#007bff" fillOpacity={0.15} name="Current Value" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}

                <div style={styles.section}>
                  <div style={styles.sectionHeader}>
                    <h3 style={styles.subsectionTitle}>📈 Current Holdings</h3>
                    <button
                      style={{ ...styles.dangerButton, backgroundColor: '#6c757d' }}
                      onClick={handleExportCSV}
                    >
                      📥 Export CSV
                    </button>
                    <button
                      style={styles.dangerButton}
                      onClick={() => setShowDeleteAll(!showDeleteAll)}
                    >
                      🗑️ Delete All Transactions
                    </button>
                  </div>

                  {showDeleteAll && (
                    <div style={styles.dangerZone}>
                      <p style={styles.warning}>
                        ⚠️ <strong>Warning:</strong> This will permanently delete ALL portfolio
                        transactions and remove all holdings from your portfolio. This action
                        cannot be undone.
                      </p>
                      <p style={styles.info}>
                        📊 There are currently <strong>{transactionCount}</strong> transaction(s)
                        that will be deleted.
                      </p>
                      <label style={styles.checkboxLabel}>
                        <input
                          type="checkbox"
                          checked={confirmDeleteAll}
                          onChange={(e) => setConfirmDeleteAll(e.target.checked)}
                        />
                        I understand this will delete ALL portfolio data permanently
                      </label>
                      {confirmDeleteAll && (
                        <button
                          style={styles.dangerButton}
                          onClick={handleDeleteAllTransactions}
                          disabled={loading}
                        >
                          🗑️ DELETE ALL TRANSACTIONS
                        </button>
                      )}
                    </div>
                  )}

                  {summary.holdings && summary.holdings.length > 0 ? (
                    <div style={styles.tableContainer}>
                      <table style={styles.table}>
                        <thead>
                          <tr>
                            <th style={styles.th}>Ticker</th>
                            <th style={styles.th}>Type</th>
                            <th style={styles.th}>Quantity</th>
                            <th style={styles.th}>Avg Cost</th>
                            <th style={styles.th}>Invested</th>
                            <th style={styles.th}>Current Price</th>
                            <th style={styles.th}>Current Value</th>
                            <th style={styles.th}>P/L</th>
                            <th style={styles.th}>P/L %</th>
                          </tr>
                        </thead>
                        <tbody>
                          {summary.holdings.map((holding) => (
                            <tr
                              key={holding.ticker}
                              style={styles.tr}
                              onClick={() => {
                                navigateToTicker(holding.ticker);
                              }}
                            >
                              <td style={styles.td}>
                                <button style={styles.tickerButton}>
                                  {holding.ticker}
                                </button>
                              </td>
                              <td style={styles.td}>{holding.asset_type}</td>
                              <td style={styles.td}>{holding.total_quantity.toFixed(2)}</td>
                              <td style={styles.td}>
                                {formatCurrency(holding.average_cost)}
                              </td>
                              <td style={styles.td}>
                                {formatCurrency(holding.total_invested)}
                              </td>
                              <td style={styles.td}>
                                {holding.current_price
                                  ? formatCurrency(holding.current_price)
                                  : 'N/A'}
                              </td>
                              <td style={styles.td}>
                                {holding.current_value
                                  ? formatCurrency(holding.current_value)
                                  : 'N/A'}
                              </td>
                              <td style={{
                                ...styles.td,
                                color: holding.profit_loss >= 0 ? '#00cc88' : '#ff4444',
                              }}>
                                {holding.profit_loss !== null
                                  ? formatCurrency(holding.profit_loss)
                                  : 'N/A'}
                              </td>
                              <td style={{
                                ...styles.td,
                                color: holding.profit_loss_percentage >= 0 ? '#00cc88' : '#ff4444',
                              }}>
                                {holding.profit_loss_percentage !== null
                                  ? formatPercent(holding.profit_loss_percentage)
                                  : 'N/A'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p style={styles.info}>No holdings found. Add transactions to see your portfolio.</p>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {/* Transactions Tab */}
        {activeTab === 'transactions' && (
          <div style={styles.tabContent}>
            <h2 style={styles.sectionTitle}>📝 Transactions</h2>
            
            <div style={styles.tabs}>
              <button
                style={{
                  ...styles.subTab,
                  ...(!showAddForm ? styles.subTabActive : {}),
                }}
                onClick={() => setShowAddForm(false)}
              >
                View Transactions
              </button>
              <button
                style={{
                  ...styles.subTab,
                  ...(showAddForm ? styles.subTabActive : {}),
                }}
                onClick={() => setShowAddForm(true)}
              >
                Add Transaction
              </button>
            </div>

            {!showAddForm ? (
              <>
                <div style={styles.filters}>
                  <input
                    type="text"
                    placeholder="Filter by Ticker (optional)"
                    value={tickerFilter}
                    onChange={(e) => setTickerFilter(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') loadTransactions();
                    }}
                    style={styles.input}
                  />
                  <select
                    value={assetTypeFilter}
                    onChange={(e) => {
                      setAssetTypeFilter(e.target.value);
                      setTimeout(loadTransactions, 0);
                    }}
                    style={styles.select}
                  >
                    <option value="All">All Asset Types</option>
                    <option value="STOCK">STOCK</option>
                    <option value="ETF">ETF</option>
                    <option value="MUTUAL_FUND">MUTUAL_FUND</option>
                  </select>
                  <button onClick={loadTransactions} style={styles.button}>
                    Apply Filters
                  </button>
                </div>

                {transactions.length > 0 ? (
                  <div style={styles.transactionsList}>
                    {transactions.slice((currentPage - 1) * transactionsPerPage, currentPage * transactionsPerPage).map((txn) => (
                      <div key={txn.id} style={styles.transactionCard}>
                        <div style={styles.transactionHeader}>
                          <strong>
                            {txn.ticker} - {txn.transaction_type} - {txn.transaction_date} -{' '}
                            {formatCurrency(txn.total_amount)}
                          </strong>
                          <div>
                            <button
                              onClick={() => setEditingTransaction(editingTransaction === txn.id ? null : txn.id)}
                              style={styles.iconButton}
                            >
                              ✏️
                            </button>
                            <button
                              onClick={() => handleDeleteTransaction(txn.id)}
                              style={styles.iconButton}
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                        
                        {editingTransaction === txn.id ? (
                          <TransactionEditForm
                            transaction={txn}
                            onSave={(data) => {
                              handleUpdateTransaction(txn.id, data);
                              setEditingTransaction(null);
                            }}
                            onCancel={() => setEditingTransaction(null)}
                          />
                        ) : (
                          <div style={styles.transactionDetails}>
                            <div style={styles.transactionGrid}>
                              <div>
                                <strong>Ticker:</strong> {txn.ticker}
                              </div>
                              <div>
                                <strong>Type:</strong> {txn.transaction_type}
                              </div>
                              <div>
                                <strong>Asset Type:</strong> {txn.asset_type}
                              </div>
                              <div>
                                <strong>Date:</strong> {txn.transaction_date}
                              </div>
                              <div>
                                <strong>Quantity:</strong> {txn.quantity.toFixed(2)}
                              </div>
                              <div>
                                <strong>Price/Unit:</strong> {formatCurrency(txn.price_per_unit)}
                              </div>
                              <div>
                                <strong>Total:</strong> {formatCurrency(txn.total_amount)}
                              </div>
                              <div>
                                <strong>Fees:</strong> {formatCurrency(txn.fees)}
                              </div>
                            </div>
                            {txn.notes && (
                              <div style={styles.notes}>
                                <strong>Notes:</strong> {txn.notes}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={styles.info}>No transactions found.</p>
                )}
                {transactions.length > transactionsPerPage && (
                  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem', marginTop: '1rem', padding: '1rem 0' }}>
                    <button
                      style={{ padding: '0.4rem 0.8rem', border: '1px solid #ddd', borderRadius: '4px', backgroundColor: currentPage === 1 ? '#f5f5f5' : 'white', cursor: currentPage === 1 ? 'default' : 'pointer', color: currentPage === 1 ? '#ccc' : '#333' }}
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                    >
                      Previous
                    </button>
                    <span style={{ fontSize: '0.9rem', color: '#666' }}>
                      Page {currentPage} of {Math.ceil(transactions.length / transactionsPerPage)} ({transactions.length} total)
                    </span>
                    <button
                      style={{ padding: '0.4rem 0.8rem', border: '1px solid #ddd', borderRadius: '4px', backgroundColor: currentPage >= Math.ceil(transactions.length / transactionsPerPage) ? '#f5f5f5' : 'white', cursor: currentPage >= Math.ceil(transactions.length / transactionsPerPage) ? 'default' : 'pointer', color: currentPage >= Math.ceil(transactions.length / transactionsPerPage) ? '#ccc' : '#333' }}
                      onClick={() => setCurrentPage(p => Math.min(Math.ceil(transactions.length / transactionsPerPage), p + 1))}
                      disabled={currentPage >= Math.ceil(transactions.length / transactionsPerPage)}
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            ) : (
              <TransactionForm
                formData={transactionFormData}
                setFormData={setTransactionFormData}
                onSubmit={handleAddTransaction}
                onCancel={() => setShowAddForm(false)}
              />
            )}
          </div>
        )}

        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <div style={styles.tabContent}>
            <h2 style={styles.sectionTitle}>📤 Upload Transaction Data</h2>
            
            <div style={styles.infoBox}>
              <h3>Upload Historical Transactions</h3>
              <p>
                Upload your transaction history from a JSON file or paste JSON directly.
              </p>
              <p>
                <strong>Supported Formats:</strong>
              </p>
              <ul>
                <li>
                  <strong>Schwab Brokerage Format</strong> - Direct export from Schwab
                  (automatically detected)
                </li>
                <li>
                  <strong>Standard Format</strong> - Our simple transaction format
                </li>
              </ul>
            </div>

            <div style={styles.tabs}>
              <button
                style={{
                  ...styles.subTab,
                  ...(uploadMethod === 'file' ? styles.subTabActive : {}),
                }}
                onClick={() => setUploadMethod('file')}
              >
                📁 Upload File
              </button>
              <button
                style={{
                  ...styles.subTab,
                  ...(uploadMethod === 'paste' ? styles.subTabActive : {}),
                }}
                onClick={() => setUploadMethod('paste')}
              >
                📋 Paste JSON
              </button>
            </div>

            {uploadMethod === 'file' ? (
              <div>
                <input
                  type="file"
                  accept=".json"
                  onChange={(e) => setUploadedFile(e.target.files[0])}
                  style={styles.fileInput}
                />
                {uploadedFile && (
                  <div style={styles.fileInfo}>
                    Selected: {uploadedFile.name}
                  </div>
                )}
                <button
                  onClick={handleFileUpload}
                  disabled={!uploadedFile || loading}
                  style={styles.button}
                >
                  Process and Upload
                </button>
              </div>
            ) : (
              <div>
                <textarea
                  value={jsonInput}
                  onChange={(e) => setJsonInput(e.target.value)}
                  placeholder='{"transactions": [...]} or Schwab format'
                  style={styles.textarea}
                  rows={15}
                />
                <button
                  onClick={handleJsonUpload}
                  disabled={!jsonInput.trim() || loading}
                  style={styles.button}
                >
                  Process and Upload
                </button>
              </div>
            )}

            {uploadResult && (
              <div style={styles.uploadResult}>
                <h3>Upload Results</h3>
                {uploadResult.duplicates > 0 ? (
                  <p style={styles.warning}>
                    ⚠️ Uploaded {uploadResult.created} new transaction(s),{' '}
                    {uploadResult.duplicates} duplicate(s) skipped
                  </p>
                ) : (
                  <p style={styles.success}>
                    ✅ Successfully uploaded {uploadResult.created} transaction(s)!
                  </p>
                )}
                <p>
                  <strong>Total Processed:</strong> {uploadResult.total}
                </p>
                <p>
                  <strong>New Transactions:</strong> {uploadResult.created}
                </p>
                <p>
                  <strong>Duplicates Skipped:</strong> {uploadResult.duplicates}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Holdings Tab */}
        {activeTab === 'holdings' && (
          <div style={styles.tabContent}>
            <h2 style={styles.sectionTitle}>📊 Individual Holdings Breakdown</h2>
            
            {tickers.length > 0 ? (
              <>
                <div style={styles.selectContainer}>
                  <label style={styles.label}>
                    Select Ticker to View Details:
                  </label>
                  <select
                    value={selectedTicker}
                    onChange={(e) => {
                      setSelectedTicker(e.target.value);
                      setSearchParams((prev) => {
                        const next = new URLSearchParams(prev);
                        next.set('ticker', e.target.value);
                        return next;
                      }, { replace: true });
                    }}
                    style={styles.select}
                  >
                    {tickers.map((ticker) => (
                      <option key={ticker} value={ticker}>
                        {ticker}
                      </option>
                    ))}
                  </select>
                </div>

                {tickerHolding && (
                  <>
                    <div style={styles.metricsGrid}>
                      <div style={styles.metricCard}>
                        <div style={styles.metricLabel}>Asset Type</div>
                        <div style={styles.metricValue}>
                          {tickerHolding.asset_type}
                        </div>
                      </div>
                      <div style={styles.metricCard}>
                        <div style={styles.metricLabel}>Quantity</div>
                        <div style={styles.metricValue}>
                          {tickerHolding.total_quantity.toFixed(2)}
                        </div>
                      </div>
                      <div style={styles.metricCard}>
                        <div style={styles.metricLabel}>Avg Cost</div>
                        <div style={styles.metricValue}>
                          {formatCurrency(tickerHolding.average_cost)}
                        </div>
                      </div>
                      <div style={styles.metricCard}>
                        <div style={styles.metricLabel}>Invested</div>
                        <div style={styles.metricValue}>
                          {formatCurrency(tickerHolding.total_invested)}
                        </div>
                      </div>
                      <div style={styles.metricCard}>
                        <div style={styles.metricLabel}>P/L</div>
                        <div style={{
                          ...styles.metricValue,
                          color: tickerHolding.profit_loss >= 0 ? '#00cc88' : '#ff4444',
                        }}>
                          {tickerHolding.profit_loss !== null
                            ? `${formatCurrency(tickerHolding.profit_loss)} (${formatPercent(tickerHolding.profit_loss_percentage)})`
                            : 'N/A'}
                        </div>
                      </div>
                      <div style={styles.metricCard}>
                        <div style={styles.metricLabel}>Current Value</div>
                        <div style={styles.metricValue}>
                          {tickerHolding.current_value != null
                            ? formatCurrency(tickerHolding.current_value)
                            : 'N/A'}
                        </div>
                      </div>
                    </div>

                    <div style={styles.dangerZone}>
                      <button
                        style={styles.dangerButton}
                        onClick={() => setConfirmDeleteTicker(!confirmDeleteTicker)}
                      >
                        🗑️ Delete Ticker (Remove All Transactions)
                      </button>
                      
                      {confirmDeleteTicker && (
                        <div style={styles.dangerZone}>
                          <p style={styles.warning}>
                            ⚠️ <strong>Warning:</strong> This will permanently delete ALL
                            transactions for <strong>{selectedTicker}</strong> and remove it
                            from your portfolio.
                          </p>
                          <label style={styles.checkboxLabel}>
                            <input
                              type="checkbox"
                              checked={confirmDeleteTicker}
                              onChange={(e) => setConfirmDeleteTicker(e.target.checked)}
                            />
                            I understand this will delete all {selectedTicker} data permanently
                          </label>
                          {confirmDeleteTicker && (
                            <button
                              style={styles.dangerButton}
                              onClick={handleDeleteTickerTransactions}
                              disabled={loading}
                            >
                              🗑️ DELETE ALL {selectedTicker} TRANSACTIONS
                            </button>
                          )}
                        </div>
                      )}
                    </div>

                    {Object.keys(splits).length > 0 && (
                      <div style={styles.infoBox}>
                        <p>
                          📊 <strong>Stock Splits Detected:</strong> {Object.keys(splits).length}{' '}
                          split(s) applied to historical data. All quantities and prices are
                          adjusted for accurate tracking.
                        </p>
                      </div>
                    )}

                    {/* Cumulative Gain/Loss Chart */}
                    {calculateCumulativeGainLoss.length > 0 && (
                      <div style={styles.section}>
                        <h3 style={styles.subsectionTitle}>📈 Cumulative Gain/Loss Over Time</h3>
                        <CumulativeGainLossChart
                          data={calculateCumulativeGainLoss}
                          ticker={selectedTicker}
                          holding={tickerHolding}
                        />
                      </div>
                    )}

                    <div style={styles.section}>
                      <details style={styles.details}>
                        <summary style={styles.summary}>➕ Quick Add Transaction</summary>
                        <TransactionForm
                          formData={quickAddFormData}
                          setFormData={setQuickAddFormData}
                          onSubmit={async (e) => {
                            e.preventDefault();
                            if (!quickAddFormData.quantity || !quickAddFormData.price_per_unit || !quickAddFormData.total_amount) {
                              setError('Please fill in all required fields');
                              return;
                            }
                            try {
                              setLoading(true);
                              setError('');
                              await portfolioService.createTransaction({
                                ...quickAddFormData,
                                ticker: selectedTicker.toUpperCase(),
                              });
                              setQuickAddFormData({
                                ticker: selectedTicker,
                                transaction_type: 'BUY',
                                asset_type: tickerHolding.asset_type,
                                transaction_date: new Date().toISOString().split('T')[0],
                                quantity: 0,
                                price_per_unit: 0,
                                total_amount: 0,
                                fees: 0,
                                notes: '',
                              });
                              loadTickerDetails();
                            } catch (err) {
                              console.error('Error adding transaction:', err);
                              setError(getErrorMessage(err) || 'Failed to add transaction');
                            } finally {
                              setLoading(false);
                            }
                          }}
                          onCancel={() => {}}
                        />
                      </details>
                    </div>

                    {tickerTransactions.length > 0 && (
                      <div style={styles.section}>
                        <h3 style={styles.subsectionTitle}>Transaction History</h3>
                        <div style={styles.transactionsList}>
                          {tickerTransactions
                            .sort((a, b) => new Date(b.transaction_date) - new Date(a.transaction_date))
                            .map((txn) => (
                              <div key={txn.id} style={styles.transactionCard}>
                                <div style={styles.transactionHeader}>
                                  <strong>
                                    {txn.transaction_type === 'BUY' ? '🟢' : '🔴'} {txn.transaction_date} -{' '}
                                    {txn.transaction_type}
                                  </strong>
                                  <div>
                                    <button
                                      onClick={() => setEditingTxnId(editingTxnId === txn.id ? null : txn.id)}
                                      style={styles.iconButton}
                                    >
                                      ✏️
                                    </button>
                                    <button
                                      onClick={() => handleDeleteTransaction(txn.id)}
                                      style={styles.iconButton}
                                    >
                                      🗑️
                                    </button>
                                  </div>
                                </div>
                                
                                {editingTxnId === txn.id ? (
                                  <TransactionEditForm
                                    transaction={txn}
                                    onSave={(data) => {
                                      handleUpdateTransaction(txn.id, data);
                                      setEditingTxnId(null);
                                    }}
                                    onCancel={() => setEditingTxnId(null)}
                                  />
                                ) : (
                                  <div style={styles.transactionDetails}>
                                    <div style={styles.transactionGrid}>
                                      <div>Qty: {txn.quantity.toFixed(2)}</div>
                                      <div>Price: {formatCurrency(txn.price_per_unit)}</div>
                                      <div>Total: {formatCurrency(txn.total_amount)}</div>
                                      <div>Fees: {formatCurrency(txn.fees)}</div>
                                    </div>
                                    {txn.notes && (
                                      <div style={styles.notes}>
                                        📝 {txn.notes}
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </>
            ) : (
              <p style={styles.info}>No holdings found. Add transactions first.</p>
            )}
          </div>
        )}

        {/* Allocation Tab */}
        {activeTab === 'allocation' && (
          <div style={styles.tabContent}>
            <h2 style={styles.sectionTitle}>📊 Asset Allocation</h2>
            
            {allocationSummary ? (
              <>
                <div style={styles.metricCard}>
                  <div style={styles.metricLabel}>Total Portfolio Value</div>
                  <div style={styles.metricValue}>
                    {formatCurrency(allocationSummary.total_portfolio_value)}
                  </div>
                </div>

                <div style={styles.tabs}>
                  <button
                    style={{
                      ...styles.subTab,
                      ...(allocationTab === 'summary' ? styles.subTabActive : {}),
                    }}
                    onClick={() => setAllocationTab('summary')}
                  >
                    📊 Allocation Summary
                  </button>
                  <button
                    style={{
                      ...styles.subTab,
                      ...(allocationTab === 'settings' ? styles.subTabActive : {}),
                    }}
                    onClick={() => setAllocationTab('settings')}
                  >
                    ⚙️ Settings
                  </button>
                  <button
                    style={{
                      ...styles.subTab,
                      ...(allocationTab === 'categories' ? styles.subTabActive : {}),
                    }}
                    onClick={() => setAllocationTab('categories')}
                  >
                    🏷️ Ticker Categories
                  </button>
                </div>

                {allocationTab === 'summary' && (
                  <div>
                    <h3 style={styles.subsectionTitle}>Asset Allocation Comparison</h3>
                    {allocationSummary.categories && allocationSummary.categories.length > 0 ? (
                      <div style={styles.tableContainer}>
                        <table style={styles.table}>
                          <thead>
                            <tr>
                              <th style={styles.th}>Category</th>
                              <th style={styles.th}>Target %</th>
                              <th style={styles.th}>Actual %</th>
                              <th style={styles.th}>Difference</th>
                              <th style={styles.th}>Threshold</th>
                              <th style={styles.th}>Value</th>
                              <th style={styles.th}>Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {allocationSummary.categories.map((cat) => (
                              <tr
                                key={cat.category}
                                style={{
                                  ...styles.tr,
                                  backgroundColor: cat.needs_rebalancing ? '#fff3cd' : 'transparent',
                                }}
                              >
                                <td style={styles.td}>{cat.category}</td>
                                <td style={styles.td}>{cat.target_percentage.toFixed(1)}%</td>
                                <td style={styles.td}>{cat.actual_percentage.toFixed(1)}%</td>
                                <td style={styles.td}>
                                  {cat.difference > 0 ? '+' : ''}
                                  {cat.difference.toFixed(2)}%
                                </td>
                                <td style={styles.td}>{cat.threshold.toFixed(1)}%</td>
                                <td style={styles.td}>{formatCurrency(cat.current_value)}</td>
                                <td style={styles.td}>
                                  {cat.needs_rebalancing ? '⚠️ Rebalance' : '✅ On Track'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p style={styles.info}>
                        No allocation data available. Make sure you have holdings and targets set up.
                      </p>
                    )}
                  </div>
                )}

                {allocationTab === 'settings' && (
                  <div>
                    <h3 style={styles.subsectionTitle}>⚙️ Allocation Targets</h3>
                    <p>Set your target allocation percentages and acceptable deviation thresholds.</p>
                    
                    {allocationTargets.map((target) => (
                      <AllocationTargetForm
                        key={target.category}
                        target={target}
                        onUpdate={(data) => handleUpdateAllocationTarget(target.category, data)}
                      />
                    ))}
                    
                    {allocationTargets.length > 0 && (
                      <div style={styles.infoBox}>
                        <p>
                          Total Targets:{' '}
                          {allocationTargets.reduce((sum, t) => sum + t.target_percentage, 0).toFixed(1)}%
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {allocationTab === 'categories' && (
                  <div>
                    <h3 style={styles.subsectionTitle}>🏷️ Ticker Categorization</h3>
                    <p>
                      View and adjust how your tickers are categorized. Tickers are automatically
                      categorized using market data.
                    </p>
                    
                    {tickerCategories.length > 0 ? (
                      <div>
                        {['US Stocks', 'International Stocks', 'Bonds', 'Cash'].map((category) => {
                          const tickersInCategory = tickerCategories.filter(
                            (tc) => tc.category === category
                          );
                          if (tickersInCategory.length === 0) return null;
                          
                          return (
                            <div key={category} style={styles.categoryGroup}>
                              <h4>
                                {category} ({tickersInCategory.length} tickers)
                              </h4>
                              {tickersInCategory.map((tc) => (
                                <TickerCategoryForm
                                  key={tc.ticker}
                                  tickerCategory={tc}
                                  onUpdate={(data) => handleUpdateTickerCategory(tc.ticker, data)}
                                  onRecategorize={() => handleRecategorizeTicker(tc.ticker)}
                                />
                              ))}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <p style={styles.info}>
                        No ticker categories found. Add transactions to see your tickers here.
                      </p>
                    )}
                  </div>
                )}
              </>
            ) : (
              <div style={styles.infoBox}>
                <p>
                  ⚠️ Allocation targets not set up yet. Please run the migration script:
                  <code>python scripts/migrate_add_asset_allocation.py</code>
                </p>
              </div>
            )}
          </div>
        )}

        {/* Yearly Investments Tab */}
        {activeTab === 'yearly' && (
          <div style={styles.tabContent}>
            <h2 style={styles.sectionTitle}>📅 Yearly Investment Summary</h2>
            <p style={styles.info}>
              Total cost basis of all BUY transactions per year across all tickers.
              Gain/loss is computed on the portion of that year&apos;s purchases still held (FIFO, split-adjusted).
            </p>

            {yearlyInvestments.length > 0 ? (
              <>
                {/* Summary metrics */}
                <div style={styles.metricsGrid}>
                  <div style={styles.metricCard}>
                    <div style={styles.metricLabel}>All-Time Invested</div>
                    <div style={styles.metricValue}>
                      {formatCurrency(yearlyInvestments.reduce((sum, y) => sum + y.total_invested, 0))}
                    </div>
                  </div>
                  <div style={styles.metricCard}>
                    <div style={styles.metricLabel}>Years Active</div>
                    <div style={styles.metricValue}>{yearlyInvestments.length}</div>
                  </div>
                  <div style={styles.metricCard}>
                    <div style={styles.metricLabel}>Avg / Year</div>
                    <div style={styles.metricValue}>
                      {formatCurrency(
                        yearlyInvestments.reduce((sum, y) => sum + y.total_invested, 0) /
                          yearlyInvestments.length
                      )}
                    </div>
                  </div>
                  <div style={styles.metricCard}>
                    <div style={styles.metricLabel}>Total Transactions</div>
                    <div style={styles.metricValue}>
                      {yearlyInvestments.reduce((sum, y) => sum + y.transaction_count, 0)}
                    </div>
                  </div>
                </div>

                {/* Bar chart */}
                <div style={styles.section}>
                  <h3 style={styles.subsectionTitle}>Investment by Year</h3>
                  <div style={{ marginTop: '1rem' }}>
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart
                        data={yearlyInvestments.map((y) => ({
                          year: y.year.toString(),
                          invested: y.total_invested,
                          fees: y.total_fees,
                        }))}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(128, 128, 128, 0.2)" />
                        <XAxis dataKey="year" stroke="#666" tick={{ fill: '#666', fontSize: 13 }} />
                        <YAxis
                          stroke="#666"
                          tick={{ fill: '#666', fontSize: 12 }}
                          tickFormatter={(v) =>
                            `$${v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v.toFixed(0)}`
                          }
                        />
                        <Tooltip
                          formatter={(value) => [formatCurrency(value)]}
                          labelFormatter={(label) => `Year: ${label}`}
                          contentStyle={{
                            backgroundColor: 'rgba(255,255,255,0.95)',
                            border: '1px solid #ccc',
                            borderRadius: '4px',
                          }}
                        />
                        <Bar
                          dataKey="invested"
                          name="Total Invested"
                          fill="#007bff"
                          radius={[4, 4, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Year-by-year table */}
                <div style={styles.section}>
                  <h3 style={styles.subsectionTitle}>Breakdown by Year</h3>
                  <div style={styles.tableContainer}>
                    <table style={styles.table}>
                      <thead>
                        <tr>
                          <th style={styles.th}>Year</th>
                          <th style={styles.th}>Total Invested</th>
                          <th style={styles.th}>Cost Basis Held</th>
                          <th style={styles.th}>Current Value</th>
                          <th style={styles.th}>Gain/Loss</th>
                          <th style={styles.th}>Txns</th>
                          <th style={styles.th}>Tickers</th>
                          <th style={styles.th}></th>
                        </tr>
                      </thead>
                      <tbody>
                        {[...yearlyInvestments].reverse().map((yearData) => (
                          <React.Fragment key={yearData.year}>
                            <tr
                              style={{ ...styles.tr, cursor: 'pointer' }}
                              onClick={() => {
                                setExpandedYear(expandedYear === yearData.year ? null : yearData.year);
                                setTickerSortKey('total_amount');
                                setTickerSortDir('desc');
                              }}
                            >
                              <td style={{ ...styles.td, fontWeight: 'bold' }}>{yearData.year}</td>
                              <td style={styles.td}>{formatCurrency(yearData.total_invested)}</td>
                              <td style={styles.td}>
                                {yearData.cost_basis_remaining != null
                                  ? formatCurrency(yearData.cost_basis_remaining)
                                  : '—'}
                              </td>
                              <td style={styles.td}>
                                {yearData.current_value_remaining != null
                                  ? formatCurrency(yearData.current_value_remaining)
                                  : '—'}
                              </td>
                              <td
                                style={{
                                  ...styles.td,
                                  color:
                                    yearData.gain_loss != null
                                      ? yearData.gain_loss >= 0
                                        ? '#00cc88'
                                        : '#ff4444'
                                      : undefined,
                                }}
                              >
                                {yearData.gain_loss != null ? (
                                  <>
                                    {formatCurrency(yearData.gain_loss)}
                                    {yearData.gain_loss_percentage != null &&
                                      ` (${yearData.gain_loss_percentage >= 0 ? '+' : ''}${yearData.gain_loss_percentage.toFixed(1)}%)`}
                                  </>
                                ) : (
                                  '—'
                                )}
                              </td>
                              <td style={styles.td}>{yearData.transaction_count}</td>
                              <td style={styles.td}>{yearData.tickers.length}</td>
                              <td style={styles.td}>
                                {expandedYear === yearData.year ? '▼' : '▶'}
                              </td>
                            </tr>
                            {expandedYear === yearData.year && (
                              <tr>
                                <td colSpan={8} style={{ padding: 0 }}>
                                  <div style={yearlyStyles.tickerBreakdown}>
                                    <table style={{ ...styles.table, marginBottom: 0 }}>
                                      <thead>
                                        <tr>
                                          {[
                                            { key: 'ticker', label: 'Ticker' },
                                            { key: 'asset_type', label: 'Type' },
                                            { key: 'total_amount', label: 'Invested' },
                                            { key: 'cost_basis_remaining', label: 'Cost Basis Held' },
                                            { key: 'current_value', label: 'Current Value' },
                                            { key: 'gain_loss', label: 'Gain/Loss' },
                                            { key: 'gain_loss_pct', label: 'G/L %' },
                                            { key: 'transaction_count', label: 'Txns' },
                                          ].map((col) => (
                                            <th
                                              key={col.key}
                                              style={{
                                                ...yearlyStyles.subTh,
                                                cursor: 'pointer',
                                                userSelect: 'none',
                                              }}
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                if (tickerSortKey === col.key) {
                                                  setTickerSortDir(tickerSortDir === 'asc' ? 'desc' : 'asc');
                                                } else {
                                                  setTickerSortKey(col.key);
                                                  setTickerSortDir(
                                                    col.key === 'ticker' || col.key === 'asset_type' ? 'asc' : 'desc'
                                                  );
                                                }
                                              }}
                                            >
                                              {col.label}
                                              {tickerSortKey === col.key && (
                                                <span style={{ marginLeft: '4px', fontSize: '0.7rem' }}>
                                                  {tickerSortDir === 'asc' ? '▲' : '▼'}
                                                </span>
                                              )}
                                            </th>
                                          ))}
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {[...yearData.tickers]
                                          .map((t) => ({
                                            ...t,
                                            gain_loss_pct:
                                              t.gain_loss != null && t.cost_basis_remaining > 0
                                                ? (t.gain_loss / t.cost_basis_remaining) * 100
                                                : null,
                                          }))
                                          .sort((a, b) => {
                                            const va = a[tickerSortKey] ?? -Infinity;
                                            const vb = b[tickerSortKey] ?? -Infinity;
                                            if (typeof va === 'string') {
                                              return tickerSortDir === 'asc'
                                                ? va.localeCompare(vb)
                                                : vb.localeCompare(va);
                                            }
                                            return tickerSortDir === 'asc' ? va - vb : vb - va;
                                          })
                                          .map((t) => (
                                          <tr key={t.ticker}>
                                            <td style={yearlyStyles.subTd}>
                                              <button
                                                style={styles.tickerButton}
                                                onClick={(e) => {
                                                  e.stopPropagation();
                                                  navigateToTicker(t.ticker);
                                                }}
                                              >
                                                {t.ticker}
                                              </button>
                                            </td>
                                            <td style={yearlyStyles.subTd}>{t.asset_type}</td>
                                            <td style={yearlyStyles.subTd}>
                                              {formatCurrency(t.total_amount)}
                                            </td>
                                            <td style={yearlyStyles.subTd}>
                                              {t.cost_basis_remaining != null
                                                ? formatCurrency(t.cost_basis_remaining)
                                                : '—'}
                                            </td>
                                            <td style={yearlyStyles.subTd}>
                                              {t.current_value != null
                                                ? formatCurrency(t.current_value)
                                                : '—'}
                                            </td>
                                            <td
                                              style={{
                                                ...yearlyStyles.subTd,
                                                color:
                                                  t.gain_loss != null
                                                    ? t.gain_loss >= 0
                                                      ? '#00cc88'
                                                      : '#ff4444'
                                                    : undefined,
                                              }}
                                            >
                                              {t.gain_loss != null
                                                ? formatCurrency(t.gain_loss)
                                                : '—'}
                                            </td>
                                            <td
                                              style={{
                                                ...yearlyStyles.subTd,
                                                color:
                                                  t.gain_loss_pct != null
                                                    ? t.gain_loss_pct >= 0
                                                      ? '#00cc88'
                                                      : '#ff4444'
                                                    : undefined,
                                              }}
                                            >
                                              {t.gain_loss_pct != null
                                                ? `${t.gain_loss_pct >= 0 ? '+' : ''}${t.gain_loss_pct.toFixed(1)}%`
                                                : '—'}
                                            </td>
                                            <td style={yearlyStyles.subTd}>{t.transaction_count}</td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            ) : (
              <p style={styles.info}>No buy transactions found. Add transactions to see yearly investment data.</p>
            )}
          </div>
        )}

        {/* Top Performers Tab */}
        {activeTab === 'performers' && (
          <div style={styles.tabContent}>
            <h2 style={styles.sectionTitle}>🏆 Top Performers</h2>

            {/* Controls row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
              {/* Timeframe selector */}
              <div style={{ ...perfStyles.timeframeBar, marginBottom: 0 }}>
                {[
                  { key: '1m', label: '1M' },
                  { key: '3m', label: '3M' },
                  { key: '6m', label: '6M' },
                  { key: 'ytd', label: 'YTD' },
                  { key: '1y', label: '1Y' },
                  { key: '3y', label: '3Y' },
                  { key: '5y', label: '5Y' },
                  { key: 'all', label: 'All Time' },
                ].map((tf) => (
                  <button
                    key={tf.key}
                    style={{
                      ...perfStyles.timeframeButton,
                      ...(performanceTimeframe === tf.key ? perfStyles.timeframeButtonActive : {}),
                    }}
                    onClick={() => handleTimeframeChange(tf.key)}
                  >
                    {tf.label}
                  </button>
                ))}
              </div>

              {/* Market / My Return toggle */}
              <div style={perfStyles.toggleContainer}>
                <button
                  style={{
                    ...perfStyles.toggleButton,
                    ...(returnMode === 'market' ? perfStyles.toggleButtonActive : {}),
                    borderRadius: '20px 0 0 20px',
                  }}
                  onClick={() => setReturnMode('market')}
                >
                  Market Return
                </button>
                <button
                  style={{
                    ...perfStyles.toggleButton,
                    ...(returnMode === 'personal' ? perfStyles.toggleButtonActive : {}),
                    borderRadius: '0 20px 20px 0',
                  }}
                  onClick={() => setReturnMode('personal')}
                >
                  My Return
                </button>
              </div>
            </div>

            {perfView && perfView.tickers.length > 0 ? (
              <>
                {/* Summary cards */}
                <div style={styles.metricsGrid}>
                  <div style={styles.metricCard}>
                    <div style={styles.metricLabel}>Portfolio Return</div>
                    <div style={{
                      ...styles.metricValue,
                      color: perfView.portfolioReturnPct != null
                        ? perfView.portfolioReturnPct >= 0 ? '#00cc88' : '#ff4444'
                        : '#333',
                    }}>
                      {perfView.portfolioReturnPct != null
                        ? `${perfView.portfolioReturnPct >= 0 ? '+' : ''}${perfView.portfolioReturnPct.toFixed(2)}%`
                        : 'N/A'}
                    </div>
                  </div>
                  <div style={styles.metricCard}>
                    <div style={styles.metricLabel}>Portfolio P/L</div>
                    <div style={{
                      ...styles.metricValue,
                      color: perfView.portfolioDollarChange != null
                        ? perfView.portfolioDollarChange >= 0 ? '#00cc88' : '#ff4444'
                        : '#333',
                    }}>
                      {perfView.portfolioDollarChange != null
                        ? formatCurrency(perfView.portfolioDollarChange)
                        : 'N/A'}
                    </div>
                  </div>
                  {(() => {
                    const best = perfView.tickers.find((t) => t.activeReturnPct != null);
                    return (
                      <div style={{ ...styles.metricCard, borderLeft: '4px solid #00cc88' }}>
                        <div style={styles.metricLabel}>Best Performer</div>
                        <div style={{ ...styles.metricValue, color: '#00cc88' }}>
                          {best ? `${best.ticker} (${best.activeReturnPct >= 0 ? '+' : ''}${best.activeReturnPct.toFixed(1)}%)` : 'N/A'}
                        </div>
                      </div>
                    );
                  })()}
                  {(() => {
                    const withReturns = perfView.tickers.filter((t) => t.activeReturnPct != null);
                    const worst = withReturns.length > 0 ? withReturns[withReturns.length - 1] : null;
                    return (
                      <div style={{ ...styles.metricCard, borderLeft: '4px solid #ff4444' }}>
                        <div style={styles.metricLabel}>Worst Performer</div>
                        <div style={{ ...styles.metricValue, color: '#ff4444' }}>
                          {worst ? `${worst.ticker} (${worst.activeReturnPct >= 0 ? '+' : ''}${worst.activeReturnPct.toFixed(1)}%)` : 'N/A'}
                        </div>
                      </div>
                    );
                  })()}
                  {benchmarkData && (
                    <div style={{ ...styles.metricCard, borderLeft: '4px solid #17a2b8' }}>
                      <div style={styles.metricLabel}>Benchmark ({benchmarkData.ticker})</div>
                      <div style={{
                        ...styles.metricValue,
                        color: benchmarkData.return_pct != null
                          ? benchmarkData.return_pct >= 0 ? '#00cc88' : '#ff4444'
                          : '#333',
                      }}>
                        {benchmarkData.return_pct != null
                          ? `${benchmarkData.return_pct >= 0 ? '+' : ''}${benchmarkData.return_pct.toFixed(2)}%`
                          : 'N/A'}
                      </div>
                    </div>
                  )}
                </div>

                {/* Performance bar chart - % returns */}
                <div style={styles.section}>
                  <h3 style={styles.subsectionTitle}>
                    {returnMode === 'personal' ? 'My Return by Ticker (%)' : 'Market Return by Ticker (%)'}
                  </h3>
                  <div style={{ marginTop: '1rem' }}>
                    <ResponsiveContainer width="100%" height={Math.max(300, perfView.tickers.filter((t) => t.activeReturnPct != null).length * 40)}>
                      <BarChart
                        data={perfView.tickers
                          .filter((t) => t.activeReturnPct != null)
                          .map((t) => ({
                            ticker: t.ticker,
                            return_pct: parseFloat(t.activeReturnPct.toFixed(2)),
                          }))}
                        layout="vertical"
                        margin={{ top: 5, right: 40, left: 60, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.2)" horizontal={false} />
                        <XAxis
                          type="number"
                          stroke="#666"
                          tick={{ fill: '#666', fontSize: 12 }}
                          tickFormatter={(v) => `${v}%`}
                        />
                        <YAxis
                          type="category"
                          dataKey="ticker"
                          stroke="#666"
                          tick={{ fill: '#333', fontSize: 13, fontWeight: 500 }}
                          width={55}
                        />
                        <Tooltip
                          formatter={(value) => [`${value >= 0 ? '+' : ''}${value.toFixed(2)}%`, 'Return']}
                          contentStyle={{ backgroundColor: 'rgba(255,255,255,0.95)', border: '1px solid #ccc', borderRadius: '4px' }}
                        />
                        <ReferenceLine x={0} stroke="#999" strokeDasharray="3 3" />
                        <Bar dataKey="return_pct" name="Return %" radius={[0, 4, 4, 0]}>
                          {perfView.tickers
                            .filter((t) => t.activeReturnPct != null)
                            .map((t, i) => (
                              <Cell key={i} fill={t.activeReturnPct >= 0 ? '#00cc88' : '#ff4444'} />
                            ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Dollar gain/loss bar chart */}
                <div style={styles.section}>
                  <h3 style={styles.subsectionTitle}>Dollar Gain/Loss by Ticker</h3>
                  <div style={{ marginTop: '1rem' }}>
                    {(() => {
                      const sorted = perfView.tickers
                        .filter((t) => t.activeDollarChange != null)
                        .sort((a, b) => b.activeDollarChange - a.activeDollarChange);
                      return (
                        <ResponsiveContainer width="100%" height={Math.max(300, sorted.length * 40)}>
                          <BarChart
                            data={sorted.map((t) => ({
                              ticker: t.ticker,
                              dollar_change: parseFloat(t.activeDollarChange.toFixed(2)),
                            }))}
                            layout="vertical"
                            margin={{ top: 5, right: 40, left: 60, bottom: 5 }}
                          >
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.2)" horizontal={false} />
                            <XAxis
                              type="number"
                              stroke="#666"
                              tick={{ fill: '#666', fontSize: 12 }}
                              tickFormatter={(v) => `$${v >= 1000 || v <= -1000 ? `${(v / 1000).toFixed(1)}k` : v.toFixed(0)}`}
                            />
                            <YAxis
                              type="category"
                              dataKey="ticker"
                              stroke="#666"
                              tick={{ fill: '#333', fontSize: 13, fontWeight: 500 }}
                              width={55}
                            />
                            <Tooltip
                              formatter={(value) => [formatCurrency(value), 'Gain/Loss']}
                              contentStyle={{ backgroundColor: 'rgba(255,255,255,0.95)', border: '1px solid #ccc', borderRadius: '4px' }}
                            />
                            <ReferenceLine x={0} stroke="#999" strokeDasharray="3 3" />
                            <Bar dataKey="dollar_change" name="Gain/Loss" radius={[0, 4, 4, 0]}>
                              {sorted.map((t, i) => (
                                <Cell key={i} fill={t.activeDollarChange >= 0 ? '#00cc88' : '#ff4444'} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      );
                    })()}
                  </div>
                </div>

                {/* Investment treemap */}
                {(() => {
                  const treemapData = perfView.tickers
                    .filter((t) => t.current_value != null && t.current_value > 0)
                    .map((t) => ({
                      name: t.ticker,
                      size: t.current_value,
                      returnPct: t.activeReturnPct,
                    }));
                  if (treemapData.length === 0) return null;

                  const TREEMAP_COLORS = [
                    '#004d00', '#006600', '#008800', '#00aa00', '#00cc88',
                    '#88ddaa', '#cccccc',
                    '#ffaaaa', '#ff7777', '#ff4444', '#cc0000', '#990000',
                  ];

                  const getTreemapColor = (pct) => {
                    if (pct == null) return '#cccccc';
                    if (pct >= 50) return TREEMAP_COLORS[0];
                    if (pct >= 30) return TREEMAP_COLORS[1];
                    if (pct >= 20) return TREEMAP_COLORS[2];
                    if (pct >= 10) return TREEMAP_COLORS[3];
                    if (pct >= 5) return TREEMAP_COLORS[4];
                    if (pct >= 0) return TREEMAP_COLORS[5];
                    if (pct >= -5) return TREEMAP_COLORS[7];
                    if (pct >= -10) return TREEMAP_COLORS[8];
                    if (pct >= -20) return TREEMAP_COLORS[9];
                    if (pct >= -30) return TREEMAP_COLORS[10];
                    return TREEMAP_COLORS[11];
                  };

                  const TreemapContent = ({ x, y, width, height, name, returnPct, size }) => {
                    if (width < 30 || height < 25) return null;
                    const showValue = width > 60 && height > 45;
                    return (
                      <g>
                        <rect x={x} y={y} width={width} height={height} rx={4} ry={4}
                          style={{ fill: getTreemapColor(returnPct), stroke: '#fff', strokeWidth: 2 }}
                        />
                        <text x={x + width / 2} y={y + height / 2 - (showValue ? 8 : 0)} textAnchor="middle" dominantBaseline="central"
                          style={{ fontSize: Math.min(14, width / 5), fill: '#fff', fontWeight: 'bold' }}
                        >
                          {name}
                        </text>
                        {showValue && (
                          <text x={x + width / 2} y={y + height / 2 + 12} textAnchor="middle" dominantBaseline="central"
                            style={{ fontSize: Math.min(11, width / 6), fill: 'rgba(255,255,255,0.85)' }}
                          >
                            {returnPct != null ? `${returnPct >= 0 ? '+' : ''}${returnPct.toFixed(1)}%` : ''}
                          </text>
                        )}
                      </g>
                    );
                  };

                  return (
                    <div style={styles.section}>
                      <h3 style={styles.subsectionTitle}>Portfolio Heatmap (size = value, color = return)</h3>
                      <div style={{ marginTop: '1rem' }}>
                        <ResponsiveContainer width="100%" height={400}>
                          <Treemap
                            data={treemapData}
                            dataKey="size"
                            nameKey="name"
                            content={<TreemapContent />}
                          >
                            <Tooltip
                              content={({ payload }) => {
                                if (!payload || !payload.length) return null;
                                const d = payload[0].payload;
                                return (
                                  <div style={{ backgroundColor: 'rgba(255,255,255,0.95)', border: '1px solid #ccc', borderRadius: '4px', padding: '0.5rem' }}>
                                    <p style={{ margin: '0 0 0.25rem', fontWeight: 'bold' }}>{d.name}</p>
                                    <p style={{ margin: '0 0 0.15rem', fontSize: '0.9rem' }}>Value: {formatCurrency(d.size)}</p>
                                    <p style={{ margin: 0, fontSize: '0.9rem', color: d.returnPct >= 0 ? '#00cc88' : '#ff4444' }}>
                                      Return: {d.returnPct != null ? `${d.returnPct >= 0 ? '+' : ''}${d.returnPct.toFixed(2)}%` : 'N/A'}
                                    </p>
                                  </div>
                                );
                              }}
                            />
                          </Treemap>
                        </ResponsiveContainer>
                        <div style={perfStyles.legendBar}>
                          <span style={{ fontSize: '0.8rem', color: '#666' }}>◄ Loss</span>
                          <div style={perfStyles.legendGradient} />
                          <span style={{ fontSize: '0.8rem', color: '#666' }}>Gain ►</span>
                        </div>
                      </div>
                    </div>
                  );
                })()}

                {/* Invested vs Current Value comparison */}
                <div style={styles.section}>
                  <h3 style={styles.subsectionTitle}>Invested vs Current Value</h3>
                  <div style={{ marginTop: '1rem' }}>
                    <ResponsiveContainer width="100%" height={Math.max(300, perfView.tickers.filter((t) => t.current_value != null).length * 45)}>
                      <BarChart
                        data={perfView.tickers
                          .filter((t) => t.current_value != null)
                          .sort((a, b) => b.current_value - a.current_value)
                          .map((t) => ({
                            ticker: t.ticker,
                            invested: parseFloat(t.total_invested.toFixed(2)),
                            current: parseFloat(t.current_value.toFixed(2)),
                          }))}
                        layout="vertical"
                        margin={{ top: 5, right: 40, left: 60, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.2)" horizontal={false} />
                        <XAxis
                          type="number"
                          stroke="#666"
                          tick={{ fill: '#666', fontSize: 12 }}
                          tickFormatter={(v) => `$${v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v.toFixed(0)}`}
                        />
                        <YAxis
                          type="category"
                          dataKey="ticker"
                          stroke="#666"
                          tick={{ fill: '#333', fontSize: 13, fontWeight: 500 }}
                          width={55}
                        />
                        <Tooltip
                          formatter={(value) => [formatCurrency(value)]}
                          contentStyle={{ backgroundColor: 'rgba(255,255,255,0.95)', border: '1px solid #ccc', borderRadius: '4px' }}
                        />
                        <Bar dataKey="invested" name="Invested" fill="#6c757d" radius={[0, 4, 4, 0]} />
                        <Bar dataKey="current" name="Current Value" fill="#007bff" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Detailed table */}
                <div style={styles.section}>
                  <h3 style={styles.subsectionTitle}>Detailed Breakdown</h3>
                  <div style={styles.tableContainer}>
                    <table style={styles.table}>
                      <thead>
                        <tr>
                          {[
                            { key: 'ticker', label: 'Ticker' },
                            { key: 'current_value', label: 'Current Value' },
                            { key: 'total_invested', label: 'Invested' },
                            { key: 'period_return_pct', label: 'Market Return' },
                            { key: 'period_dollar_change', label: 'Market P/L' },
                            { key: 'all_time_return_pct', label: 'My Return' },
                            { key: 'all_time_dollar_change', label: 'My P/L' },
                            { key: 'current_price', label: 'Price' },
                            { key: 'quantity', label: 'Shares' },
                          ].map((col) => {
                            const isActiveMode =
                              (returnMode === 'market' && (col.key === 'period_return_pct' || col.key === 'period_dollar_change')) ||
                              (returnMode === 'personal' && (col.key === 'all_time_return_pct' || col.key === 'all_time_dollar_change'));
                            return (
                              <th
                                key={col.key}
                                style={{
                                  ...styles.th,
                                  cursor: 'pointer',
                                  userSelect: 'none',
                                  backgroundColor: isActiveMode ? '#eef4ff' : undefined,
                                }}
                                onClick={() => {
                                  if (perfSortKey === col.key) {
                                    setPerfSortDir(perfSortDir === 'asc' ? 'desc' : 'asc');
                                  } else {
                                    setPerfSortKey(col.key);
                                    setPerfSortDir(col.key === 'ticker' ? 'asc' : 'desc');
                                  }
                                }}
                              >
                                {col.label}
                                {perfSortKey === col.key && (
                                  <span style={{ marginLeft: '4px', fontSize: '0.7rem' }}>
                                    {perfSortDir === 'asc' ? '▲' : '▼'}
                                  </span>
                                )}
                              </th>
                            );
                          })}
                        </tr>
                      </thead>
                      <tbody>
                        {[...perfView.tickers]
                          .sort((a, b) => {
                            const va = a[perfSortKey] ?? -Infinity;
                            const vb = b[perfSortKey] ?? -Infinity;
                            if (typeof va === 'string') {
                              return perfSortDir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
                            }
                            return perfSortDir === 'asc' ? va - vb : vb - va;
                          })
                          .map((t) => {
                            const mktActive = returnMode === 'market';
                            const myActive = returnMode === 'personal';
                            return (
                              <tr key={t.ticker} style={styles.tr}>
                                <td style={styles.td}>
                                  <button style={styles.tickerButton} onClick={() => navigateToTicker(t.ticker)}>
                                    {t.ticker}
                                  </button>
                                </td>
                                <td style={styles.td}>
                                  {t.current_value != null ? formatCurrency(t.current_value) : 'N/A'}
                                </td>
                                <td style={styles.td}>{formatCurrency(t.total_invested)}</td>
                                <td style={{
                                  ...styles.td,
                                  fontWeight: mktActive ? 'bold' : 'normal',
                                  backgroundColor: mktActive ? '#f6f9ff' : undefined,
                                  color: t.period_return_pct != null
                                    ? t.period_return_pct >= 0 ? '#00cc88' : '#ff4444'
                                    : undefined,
                                }}>
                                  {t.period_return_pct != null
                                    ? `${t.period_return_pct >= 0 ? '+' : ''}${t.period_return_pct.toFixed(2)}%`
                                    : '—'}
                                </td>
                                <td style={{
                                  ...styles.td,
                                  backgroundColor: mktActive ? '#f6f9ff' : undefined,
                                  color: t.period_dollar_change != null
                                    ? t.period_dollar_change >= 0 ? '#00cc88' : '#ff4444'
                                    : undefined,
                                }}>
                                  {t.period_dollar_change != null ? formatCurrency(t.period_dollar_change) : '—'}
                                </td>
                                <td style={{
                                  ...styles.td,
                                  fontWeight: myActive ? 'bold' : 'normal',
                                  backgroundColor: myActive ? '#f6f9ff' : undefined,
                                  color: t.all_time_return_pct != null
                                    ? t.all_time_return_pct >= 0 ? '#00cc88' : '#ff4444'
                                    : undefined,
                                }}>
                                  {t.all_time_return_pct != null
                                    ? `${t.all_time_return_pct >= 0 ? '+' : ''}${t.all_time_return_pct.toFixed(2)}%`
                                    : '—'}
                                </td>
                                <td style={{
                                  ...styles.td,
                                  backgroundColor: myActive ? '#f6f9ff' : undefined,
                                  color: t.all_time_dollar_change != null
                                    ? t.all_time_dollar_change >= 0 ? '#00cc88' : '#ff4444'
                                    : undefined,
                                }}>
                                  {t.all_time_dollar_change != null ? formatCurrency(t.all_time_dollar_change) : '—'}
                                </td>
                                <td style={styles.td}>
                                  {t.current_price != null ? `$${t.current_price.toFixed(2)}` : 'N/A'}
                                </td>
                                <td style={styles.td}>{t.quantity.toFixed(4)}</td>
                              </tr>
                            );
                          })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            ) : !loading ? (
              <p style={styles.info}>No holdings found. Add transactions to see performance data.</p>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}

// Helper Components
function CumulativeGainLossChart({ data, ticker, holding }) {
  if (!data || data.length === 0) return null;

  // Format data for chart (convert dates to proper format)
  const chartData = data.map((item) => ({
    ...item,
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    dateValue: new Date(item.date).getTime(),
  }));

  // Determine line color based on final gain/loss
  const finalGainLoss = data[data.length - 1]?.cumulativeGainLoss || 0;
  const lineColor = finalGainLoss >= 0 ? '#00cc88' : '#ff4444';
  const fillColor = finalGainLoss >= 0 ? 'rgba(0, 204, 136, 0.15)' : 'rgba(255, 68, 68, 0.15)';

  // Format currency for tooltip
  const formatCurrencyTooltip = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={chartStyles.tooltip}>
          <p style={chartStyles.tooltipLabel}>{data.date}</p>
          <p style={chartStyles.tooltipValue}>
            Cumulative Gain/Loss: {formatCurrencyTooltip(data.cumulativeGainLoss)}
          </p>
          {data.transactionType && data.transactionType !== 'CURRENT' && (
            <p style={chartStyles.tooltipDetail}>
              {data.transactionType}: {data.transactionQuantity.toFixed(2)} @{' '}
              {formatCurrencyTooltip(data.transactionPrice)}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  // Calculate Y-axis range with padding
  const yValues = data.map((d) => d.cumulativeGainLoss);
  const minY = Math.min(...yValues);
  const maxY = Math.max(...yValues);
  const padding = Math.abs(maxY - minY) * 0.1 || 100;
  const yDomain = [minY - padding, maxY + padding];

  return (
    <div style={chartStyles.chartContainer}>
      <ResponsiveContainer width="100%" height={500}>
        <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <defs>
            <linearGradient id="colorGainLoss" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={lineColor} stopOpacity={0.3} />
              <stop offset="95%" stopColor={lineColor} stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(128, 128, 128, 0.2)" />
          <XAxis
            dataKey="date"
            stroke="#666"
            tick={{ fill: '#666', fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            stroke="#666"
            tick={{ fill: '#666', fontSize: 12 }}
            domain={yDomain}
            tickFormatter={(value) => `$${value.toLocaleString('en-US', { maximumFractionDigits: 0 })}`}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={0} stroke="rgba(128, 128, 128, 0.5)" strokeDasharray="5 5" />
          <Area
            type="monotone"
            dataKey="cumulativeGainLoss"
            stroke={lineColor}
            strokeWidth={3}
            fill="url(#colorGainLoss)"
            dot={{ fill: lineColor, r: 6 }}
            activeDot={{ r: 8 }}
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Current Position Summary */}
      {holding && (
        <div style={chartStyles.positionSummary}>
          {holding.current_price ? (
            <div style={chartStyles.successBox}>
              <strong>Current Position:</strong> {holding.total_quantity.toFixed(2)} shares @{' '}
              {formatCurrencyTooltip(holding.current_price)} = {formatCurrencyTooltip(holding.current_value)}{' '}
              {holding.profit_loss >= 0 ? '📈 +' : '📉 '}
              {formatCurrencyTooltip(Math.abs(holding.profit_loss))} /{' '}
              {holding.profit_loss_percentage.toFixed(2)}%
            </div>
          ) : (
            <div style={chartStyles.infoBox}>
              <strong>Current Position:</strong> {holding.total_quantity.toFixed(2)} shares (Cost Basis:{' '}
              {formatCurrencyTooltip(holding.average_cost)}/share, Total Invested:{' '}
              {formatCurrencyTooltip(holding.total_invested)})
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function TransactionForm({ formData, setFormData, onSubmit, onCancel }) {
  return (
    <form onSubmit={onSubmit} style={styles.form}>
      <div style={styles.formGrid}>
        <div>
          <label style={styles.label}>
            Ticker Symbol* <input
              type="text"
              value={formData.ticker}
              onChange={(e) => setFormData({ ...formData, ticker: e.target.value.toUpperCase() })}
              placeholder="e.g., AAPL"
              required
              style={styles.input}
            />
          </label>
        </div>
        <div>
          <label style={styles.label}>
            Transaction Type* <select
              value={formData.transaction_type}
              onChange={(e) => setFormData({ ...formData, transaction_type: e.target.value })}
              required
              style={styles.select}
            >
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
              <option value="DIVIDEND">DIVIDEND</option>
            </select>
          </label>
        </div>
        <div>
          <label style={styles.label}>
            Asset Type* <select
              value={formData.asset_type}
              onChange={(e) => setFormData({ ...formData, asset_type: e.target.value })}
              required
              style={styles.select}
            >
              <option value="STOCK">STOCK</option>
              <option value="ETF">ETF</option>
              <option value="MUTUAL_FUND">MUTUAL_FUND</option>
            </select>
          </label>
        </div>
        <div>
          <label style={styles.label}>
            Transaction Date* <input
              type="date"
              value={formData.transaction_date}
              onChange={(e) => setFormData({ ...formData, transaction_date: e.target.value })}
              required
              style={styles.input}
            />
          </label>
        </div>
        <div>
          <label style={styles.label}>
            Quantity (shares)* <input
              type="number"
              value={formData.quantity}
              onChange={(e) => {
                const qty = parseFloat(e.target.value) || 0;
                const price = formData.price_per_unit || 0;
                setFormData({
                  ...formData,
                  quantity: qty,
                  total_amount: qty * price,
                });
              }}
              min="0"
              step="0.01"
              required
              style={styles.input}
            />
          </label>
        </div>
        <div>
          <label style={styles.label}>
            Price per Unit* <input
              type="number"
              value={formData.price_per_unit}
              onChange={(e) => {
                const price = parseFloat(e.target.value) || 0;
                const qty = formData.quantity || 0;
                setFormData({
                  ...formData,
                  price_per_unit: price,
                  total_amount: qty * price,
                });
              }}
              min="0"
              step="0.01"
              required
              style={styles.input}
            />
          </label>
        </div>
        <div>
          <label style={styles.label}>
            Fees <input
              type="number"
              value={formData.fees}
              onChange={(e) => setFormData({ ...formData, fees: parseFloat(e.target.value) || 0 })}
              min="0"
              step="0.01"
              style={styles.input}
            />
          </label>
        </div>
        <div>
          <label style={styles.label}>
            Total Amount* <input
              type="number"
              value={formData.total_amount}
              onChange={(e) => setFormData({ ...formData, total_amount: parseFloat(e.target.value) || 0 })}
              min="0"
              step="0.01"
              required
              style={styles.input}
            />
          </label>
        </div>
      </div>
      <div>
        <label style={styles.label}>
          Notes (optional) <textarea
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            style={styles.textarea}
            rows={3}
          />
        </label>
      </div>
      <div style={styles.formActions}>
        <button type="submit" style={styles.button}>
          Add Transaction
        </button>
        <button type="button" onClick={onCancel} style={styles.secondaryButton}>
          Cancel
        </button>
      </div>
    </form>
  );
}

function TransactionEditForm({ transaction, onSave, onCancel }) {
  const [editData, setEditData] = useState({
    transaction_type: transaction.transaction_type,
    transaction_date: transaction.transaction_date,
    quantity: transaction.quantity,
    price_per_unit: transaction.price_per_unit,
    total_amount: transaction.total_amount,
    fees: transaction.fees || 0,
    notes: transaction.notes || '',
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(editData);
  };

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <div style={styles.formGrid}>
        <div>
          <label style={styles.label}>
            Type <select
              value={editData.transaction_type}
              onChange={(e) => setEditData({ ...editData, transaction_type: e.target.value })}
              style={styles.select}
            >
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
              <option value="DIVIDEND">DIVIDEND</option>
            </select>
          </label>
        </div>
        <div>
          <label style={styles.label}>
            Date <input
              type="date"
              value={editData.transaction_date}
              onChange={(e) => setEditData({ ...editData, transaction_date: e.target.value })}
              style={styles.input}
            />
          </label>
        </div>
        <div>
          <label style={styles.label}>
            Quantity <input
              type="number"
              value={editData.quantity}
              onChange={(e) => {
                const qty = parseFloat(e.target.value) || 0;
                const price = editData.price_per_unit || 0;
                setEditData({
                  ...editData,
                  quantity: qty,
                  total_amount: qty * price,
                });
              }}
              min="0"
              step="0.01"
              style={styles.input}
            />
          </label>
        </div>
        <div>
          <label style={styles.label}>
            Price/Unit <input
              type="number"
              value={editData.price_per_unit}
              onChange={(e) => {
                const price = parseFloat(e.target.value) || 0;
                const qty = editData.quantity || 0;
                setEditData({
                  ...editData,
                  price_per_unit: price,
                  total_amount: qty * price,
                });
              }}
              min="0"
              step="0.01"
              style={styles.input}
            />
          </label>
        </div>
        <div>
          <label style={styles.label}>
            Fees <input
              type="number"
              value={editData.fees}
              onChange={(e) => setEditData({ ...editData, fees: parseFloat(e.target.value) || 0 })}
              min="0"
              step="0.01"
              style={styles.input}
            />
          </label>
        </div>
        <div>
          <label style={styles.label}>
            Total <input
              type="number"
              value={editData.total_amount}
              onChange={(e) => setEditData({ ...editData, total_amount: parseFloat(e.target.value) || 0 })}
              min="0"
              step="0.01"
              style={styles.input}
            />
          </label>
        </div>
      </div>
      <div>
        <label style={styles.label}>
          Notes <textarea
            value={editData.notes}
            onChange={(e) => setEditData({ ...editData, notes: e.target.value })}
            style={styles.textarea}
            rows={3}
          />
        </label>
      </div>
      <div style={styles.formActions}>
        <button type="submit" style={styles.button}>
          💾 Save Changes
        </button>
        <button type="button" onClick={onCancel} style={styles.secondaryButton}>
          ❌ Cancel
        </button>
      </div>
    </form>
  );
}

function AllocationTargetForm({ target, onUpdate }) {
  const [targetPct, setTargetPct] = useState(target.target_percentage);
  const [thresholdPct, setThresholdPct] = useState(target.threshold_percentage);

  const handleUpdate = () => {
    onUpdate({
      target_percentage: targetPct,
      threshold_percentage: thresholdPct,
    });
  };

  return (
    <div style={styles.allocationTargetCard}>
      <h4>{target.category}</h4>
      <div style={styles.formGrid}>
        <div>
          <label style={styles.label}>
            Target % <input
              type="number"
              value={targetPct}
              onChange={(e) => setTargetPct(parseFloat(e.target.value) || 0)}
              min="0"
              max="100"
              step="1"
              style={styles.input}
            />
          </label>
        </div>
        <div>
          <label style={styles.label}>
            Threshold % <input
              type="number"
              value={thresholdPct}
              onChange={(e) => setThresholdPct(parseFloat(e.target.value) || 0)}
              min="0"
              max="100"
              step="0.5"
              style={styles.input}
            />
          </label>
        </div>
      </div>
      <button onClick={handleUpdate} style={styles.button}>
        Update {target.category}
      </button>
    </div>
  );
}

function TickerCategoryForm({ tickerCategory, onUpdate, onRecategorize }) {
  const [newCategory, setNewCategory] = useState(tickerCategory.category);

  const handleUpdate = () => {
    if (newCategory !== tickerCategory.category) {
      onUpdate({
        category: newCategory,
        is_auto_categorized: false,
      });
    }
  };

  return (
    <div style={styles.tickerCategoryCard}>
      <div style={styles.tickerCategoryHeader}>
        <div>
          <strong>{tickerCategory.ticker}</strong>
          {tickerCategory.ticker_name && (
            <div style={styles.tickerName}>{tickerCategory.ticker_name}</div>
          )}
        </div>
        <div>
          {tickerCategory.is_auto_categorized ? '🤖 Auto' : '✋ Manual'}
        </div>
      </div>
      <div style={styles.tickerCategoryActions}>
        <select
          value={newCategory}
          onChange={(e) => setNewCategory(e.target.value)}
          style={styles.select}
        >
          <option value="US Stocks">US Stocks</option>
          <option value="International Stocks">International Stocks</option>
          <option value="Bonds">Bonds</option>
          <option value="Cash">Cash</option>
        </select>
        {newCategory !== tickerCategory.category ? (
          <button onClick={handleUpdate} style={styles.button}>
            Update
          </button>
        ) : (
          tickerCategory.is_auto_categorized && (
            <button onClick={onRecategorize} style={styles.secondaryButton}>
              Re-scan
            </button>
          )
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    width: '100%',
    boxSizing: 'border-box',
  },
  header: {
    backgroundColor: 'white',
    padding: 'clamp(0.75rem, 2vw, 1rem) clamp(1rem, 4vw, 2rem)',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    boxSizing: 'border-box',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  homeButton: {
    padding: '0.5rem',
    backgroundColor: 'transparent',
    border: 'none',
    fontSize: '1.5rem',
    cursor: 'pointer',
    borderRadius: '4px',
    transition: 'background-color 0.2s',
  },
  title: {
    margin: 0,
    fontSize: '1.5rem',
    color: '#333',
  },
  headerActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  userInfo: {
    color: '#666',
  },
  logoutButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  content: {
    width: '100%',
    maxWidth: '1400px',
    margin: '0 auto',
    padding: 'clamp(1rem, 3vw, 2rem)',
    boxSizing: 'border-box',
  },
  tabs: {
    display: 'flex',
    gap: '0.5rem',
    marginBottom: '2rem',
    borderBottom: '2px solid #ddd',
    flexWrap: 'wrap',
  },
  tab: {
    padding: '0.75rem 1.5rem',
    backgroundColor: 'transparent',
    border: 'none',
    borderBottom: '3px solid transparent',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '500',
    color: '#666',
    transition: 'all 0.2s',
  },
  tabActive: {
    color: '#007bff',
    borderBottomColor: '#007bff',
  },
  tabContent: {
    backgroundColor: 'white',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  sectionTitle: {
    marginTop: 0,
    marginBottom: '1.5rem',
    fontSize: '1.5rem',
    color: '#333',
  },
  subsectionTitle: {
    marginTop: 0,
    marginBottom: '1rem',
    fontSize: '1.2rem',
    color: '#333',
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1.5rem',
    marginBottom: '2rem',
  },
  metricCard: {
    backgroundColor: '#f8f9fa',
    padding: '1.5rem',
    borderRadius: '8px',
    textAlign: 'center',
  },
  metricLabel: {
    fontSize: '0.9rem',
    color: '#666',
    marginBottom: '0.5rem',
  },
  metricValue: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    color: '#333',
  },
  section: {
    marginTop: '2rem',
  },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  dangerZone: {
    backgroundColor: '#fff3cd',
    border: '1px solid #ffc107',
    borderRadius: '8px',
    padding: '1.5rem',
    marginBottom: '1.5rem',
  },
  warning: {
    color: '#856404',
    marginBottom: '1rem',
  },
  info: {
    color: '#666',
    marginBottom: '1rem',
  },
  checkboxLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '1rem',
    cursor: 'pointer',
  },
  dangerButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  tableContainer: {
    overflowX: 'auto',
    marginTop: '1rem',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    padding: '0.75rem',
    textAlign: 'left',
    borderBottom: '2px solid #ddd',
    fontWeight: '600',
    color: '#333',
  },
  tr: {
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  'tr:hover': {
    backgroundColor: '#f8f9fa',
  },
  td: {
    padding: '0.75rem',
    borderBottom: '1px solid #eee',
  },
  tickerButton: {
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    padding: '0.25rem 0.75rem',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  error: {
    backgroundColor: '#f8d7da',
    color: '#721c24',
    padding: '1rem',
    borderRadius: '4px',
    marginBottom: '1rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  errorClose: {
    backgroundColor: 'transparent',
    border: 'none',
    fontSize: '1.5rem',
    cursor: 'pointer',
    color: '#721c24',
  },
  loading: {
    textAlign: 'center',
    padding: '2rem',
    color: '#666',
  },
  subTab: {
    padding: '0.5rem 1rem',
    backgroundColor: 'transparent',
    border: 'none',
    borderBottom: '2px solid transparent',
    cursor: 'pointer',
    fontSize: '0.9rem',
    color: '#666',
    transition: 'all 0.2s',
  },
  subTabActive: {
    color: '#007bff',
    borderBottomColor: '#007bff',
  },
  filters: {
    display: 'flex',
    gap: '1rem',
    marginBottom: '1.5rem',
    flexWrap: 'wrap',
  },
  input: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
    width: '100%',
    boxSizing: 'border-box',
  },
  select: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
    backgroundColor: 'white',
    cursor: 'pointer',
  },
  button: {
    padding: '0.5rem 1rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    fontWeight: '500',
  },
  secondaryButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    fontWeight: '500',
  },
  iconButton: {
    padding: '0.25rem 0.5rem',
    backgroundColor: 'transparent',
    border: 'none',
    cursor: 'pointer',
    fontSize: '1rem',
    marginLeft: '0.5rem',
  },
  transactionsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
    marginTop: '1.5rem',
  },
  transactionCard: {
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '1rem',
    backgroundColor: '#f8f9fa',
  },
  transactionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.5rem',
  },
  transactionDetails: {
    marginTop: '0.5rem',
  },
  transactionGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '0.5rem',
    marginBottom: '0.5rem',
  },
  notes: {
    marginTop: '0.5rem',
    color: '#666',
    fontSize: '0.9rem',
  },
  form: {
    marginTop: '1.5rem',
  },
  formGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
    marginBottom: '1rem',
  },
  formActions: {
    display: 'flex',
    gap: '1rem',
    marginTop: '1rem',
  },
  label: {
    display: 'block',
    marginBottom: '0.5rem',
    fontWeight: '500',
    color: '#333',
  },
  textarea: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
    width: '100%',
    fontFamily: 'inherit',
    boxSizing: 'border-box',
  },
  fileInput: {
    marginBottom: '1rem',
  },
  fileInfo: {
    marginBottom: '1rem',
    color: '#666',
  },
  uploadResult: {
    marginTop: '1.5rem',
    padding: '1rem',
    backgroundColor: '#d4edda',
    border: '1px solid #c3e6cb',
    borderRadius: '8px',
  },
  success: {
    color: '#155724',
    fontWeight: '500',
  },
  infoBox: {
    backgroundColor: '#d1ecf1',
    border: '1px solid #bee5eb',
    borderRadius: '8px',
    padding: '1rem',
    marginBottom: '1.5rem',
  },
  selectContainer: {
    marginBottom: '1.5rem',
  },
  allocationTargetCard: {
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '1.5rem',
    marginBottom: '1rem',
    backgroundColor: '#f8f9fa',
  },
  tickerCategoryCard: {
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '1rem',
    marginBottom: '0.5rem',
    backgroundColor: '#f8f9fa',
  },
  tickerCategoryHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.5rem',
  },
  tickerName: {
    fontSize: '0.85rem',
    color: '#666',
    marginTop: '0.25rem',
  },
  tickerCategoryActions: {
    display: 'flex',
    gap: '0.5rem',
    alignItems: 'center',
  },
  categoryGroup: {
    marginBottom: '2rem',
  },
  details: {
    marginTop: '1rem',
    padding: '1rem',
    border: '1px solid #ddd',
    borderRadius: '8px',
    backgroundColor: '#f8f9fa',
  },
  summary: {
    cursor: 'pointer',
    fontWeight: '500',
    fontSize: '1rem',
    padding: '0.5rem',
    userSelect: 'none',
  },
};

const chartStyles = {
  chartContainer: {
    marginTop: '1.5rem',
    marginBottom: '1.5rem',
  },
  tooltip: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    border: '1px solid #ccc',
    borderRadius: '4px',
    padding: '0.5rem',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  tooltipLabel: {
    margin: '0 0 0.25rem 0',
    fontWeight: 'bold',
    color: '#333',
  },
  tooltipValue: {
    margin: '0 0 0.25rem 0',
    color: '#333',
  },
  tooltipDetail: {
    margin: 0,
    fontSize: '0.85rem',
    color: '#666',
  },
  positionSummary: {
    marginTop: '1rem',
    padding: '1rem',
    borderRadius: '8px',
  },
  successBox: {
    backgroundColor: '#d4edda',
    border: '1px solid #c3e6cb',
    color: '#155724',
    padding: '1rem',
    borderRadius: '8px',
  },
  infoBox: {
    backgroundColor: '#d1ecf1',
    border: '1px solid #bee5eb',
    color: '#0c5460',
    padding: '1rem',
    borderRadius: '8px',
  },
};

const yearlyStyles = {
  tickerBreakdown: {
    backgroundColor: '#f0f4f8',
    padding: '0.75rem 1rem',
    borderTop: '1px solid #ddd',
  },
  subTh: {
    padding: '0.5rem 0.75rem',
    textAlign: 'left',
    borderBottom: '1px solid #ccc',
    fontWeight: '600',
    color: '#555',
    fontSize: '0.85rem',
  },
  subTd: {
    padding: '0.5rem 0.75rem',
    borderBottom: '1px solid #e8e8e8',
    fontSize: '0.9rem',
  },
};

const perfStyles = {
  timeframeBar: {
    display: 'flex',
    gap: '0.5rem',
    marginBottom: '1.5rem',
    flexWrap: 'wrap',
  },
  timeframeButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#f0f0f0',
    border: '1px solid #ddd',
    borderRadius: '20px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    fontWeight: '500',
    color: '#555',
    transition: 'all 0.2s',
  },
  timeframeButtonActive: {
    backgroundColor: '#007bff',
    color: '#fff',
    borderColor: '#007bff',
  },
  toggleContainer: {
    display: 'flex',
    flexShrink: 0,
  },
  toggleButton: {
    padding: '0.5rem 1.1rem',
    backgroundColor: '#f0f0f0',
    border: '1px solid #ddd',
    cursor: 'pointer',
    fontSize: '0.85rem',
    fontWeight: '500',
    color: '#555',
    transition: 'all 0.2s',
  },
  toggleButtonActive: {
    backgroundColor: '#007bff',
    color: '#fff',
    borderColor: '#007bff',
  },
  legendBar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    marginTop: '0.5rem',
  },
  legendGradient: {
    width: '200px',
    height: '12px',
    borderRadius: '6px',
    background: 'linear-gradient(to right, #990000, #ff4444, #cccccc, #00cc88, #004d00)',
  },
};
