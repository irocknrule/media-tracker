import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { fireService } from '../services/fireService';
import { portfolioService } from '../services/portfolioService';
import { getErrorMessage } from '../utils/errorHandler';
import { formatCurrency, formatCurrencyPrecise, formatPercent } from '../utils/formatters';
import ConfirmModal from '../components/ConfirmModal';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
  BarChart,
  Bar,
  ComposedChart,
  Line,
} from 'recharts';

const ACCOUNT_TYPES = ['401K', 'IRA', 'ROTH_IRA', 'HSA', 'BROKERAGE', 'STOCK_PLAN', 'OTHER'];
const ACCOUNT_TYPE_LABELS = {
  '401K': '401(k)',
  'IRA': 'IRA',
  'ROTH_IRA': 'Roth IRA',
  'HSA': 'HSA',
  'BROKERAGE': 'Brokerage',
  'STOCK_PLAN': 'Stock Plan',
  'OTHER': 'Other',
};

export default function Fire() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'accounts';
  const setActiveTab = (tab) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (tab === 'accounts') {
        next.delete('tab');
      } else {
        next.set('tab', tab);
      }
      return next;
    });
  };
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Accounts state
  const [accounts, setAccounts] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showBulkImport, setShowBulkImport] = useState(false);
  const [bulkText, setBulkText] = useState('');
  const [bulkSnapshotDate, setBulkSnapshotDate] = useState(new Date().toISOString().split('T')[0]);
  const [bulkImportResult, setBulkImportResult] = useState(null);
  const [editingAccount, setEditingAccount] = useState(null);
  const [expandedAccountId, setExpandedAccountId] = useState(null);
  const [accountSnapshots, setAccountSnapshots] = useState([]);
  const [showSnapshotModal, setShowSnapshotModal] = useState(false);
  const [snapshotBalances, setSnapshotBalances] = useState({});
  const [snapshotContributions, setSnapshotContributions] = useState({});
  const [snapshotDate, setSnapshotDate] = useState(new Date().toISOString().split('T')[0]);
  const [accountForm, setAccountForm] = useState({
    name: '',
    account_type: 'BROKERAGE',
    owner: '',
    institution: '',
    last_four: '',
    balance: '',
  });

  // Aggregate snapshots state
  const [aggSnapshots, setAggSnapshots] = useState([]);
  const [showAggForm, setShowAggForm] = useState(false);
  const [aggForm, setAggForm] = useState({
    snapshot_date: new Date().toISOString().split('T')[0],
    total_value: '',
    contributions_since_last: '',
    notes: '',
  });

  // Income state
  const [incomeHistory, setIncomeHistory] = useState(null);
  const [incomeInterval, setIncomeInterval] = useState('quarterly');
  const [selectedAccountIds, setSelectedAccountIds] = useState(null);
  const [showAccountFilter, setShowAccountFilter] = useState(false);
  const filterRef = useRef(null);

  // Projections state
  const [projParams, setProjParams] = useState({
    currentValue: 0,
    annualContribution: 50000,
    growthRate: 7,
    annualExpenses: 100000,
    swr: 4,
    currentAge: 35,
    targetAge: 65,
    inflationRate: 3,
  });
  const [scenarios, setScenarios] = useState([
    { id: 1, growthRate: 6, swr: 4, annualExpenses: 80000 },
    { id: 2, growthRate: 7, swr: 4, annualExpenses: 100000 },
    { id: 3, growthRate: 8, swr: 3.5, annualExpenses: 120000 },
  ]);

  // Data loading
  const loadAccounts = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fireService.getAccounts();
      setAccounts(data);
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to load accounts');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadDashboard = useCallback(async () => {
    try {
      const data = await fireService.getDashboard();
      setDashboard(data);
      if (data.total_portfolio_value) {
        setProjParams(prev => ({ ...prev, currentValue: data.total_portfolio_value }));
      }
    } catch (err) {
      console.error('Error loading dashboard:', err);
    }
  }, []);

  const loadAggSnapshots = useCallback(async () => {
    try {
      const data = await fireService.getAggregateSnapshots();
      setAggSnapshots(data);
    } catch (err) {
      console.error('Error loading aggregate snapshots:', err);
    }
  }, []);

  const loadIncomeHistory = useCallback(async () => {
    try {
      setLoading(true);
      const allIds = accounts.map(a => a.id);
      const isFiltered = selectedAccountIds !== null &&
        selectedAccountIds.length !== allIds.length;
      const ids = isFiltered ? selectedAccountIds : null;
      const data = await fireService.getIncomeHistory(incomeInterval, ids);
      setIncomeHistory(data);
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to load income history');
    } finally {
      setLoading(false);
    }
  }, [incomeInterval, selectedAccountIds, accounts]);

  useEffect(() => {
    loadAccounts();
    loadDashboard();
    loadAggSnapshots();
  }, [loadAccounts, loadDashboard, loadAggSnapshots]);

  useEffect(() => {
    if (activeTab === 'income') {
      loadIncomeHistory();
    }
  }, [activeTab, loadIncomeHistory]);

  useEffect(() => {
    if (!showAccountFilter) return;
    const handleClickOutside = (e) => {
      if (filterRef.current && !filterRef.current.contains(e.target)) {
        setShowAccountFilter(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showAccountFilter]);

  // Handlers
  const handleCreateAccount = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');
      await fireService.createAccount({
        ...accountForm,
        balance: accountForm.balance ? parseFloat(accountForm.balance) : null,
        snapshot_date: new Date().toISOString().split('T')[0],
      });
      setAccountForm({ name: '', account_type: 'BROKERAGE', owner: '', institution: '', last_four: '', balance: '' });
      setShowAddForm(false);
      loadAccounts();
      loadDashboard();
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to create account');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateAccount = async (e) => {
    e.preventDefault();
    if (!editingAccount) return;
    try {
      setLoading(true);
      setError('');
      await fireService.updateAccount(editingAccount.id, {
        name: editingAccount.name,
        account_type: editingAccount.account_type,
        owner: editingAccount.owner,
        institution: editingAccount.institution,
        last_four: editingAccount.last_four,
        is_active: editingAccount.is_active,
      });
      setEditingAccount(null);
      loadAccounts();
      loadDashboard();
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to update account');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = (id) => {
    setConfirmModal({
      title: 'Delete Account',
      message: 'Delete this account and all its snapshots? This cannot be undone.',
      danger: true,
      onConfirm: async () => {
        setConfirmModal(null);
        try {
          setLoading(true);
          await fireService.deleteAccount(id);
          if (expandedAccountId === id) {
            setExpandedAccountId(null);
            setAccountSnapshots([]);
          }
          loadAccounts();
          loadDashboard();
        } catch (err) {
          setError(getErrorMessage(err) || 'Failed to delete account');
        } finally {
          setLoading(false);
        }
      },
    });
  };

  const toggleSnapshots = async (accountId) => {
    if (expandedAccountId === accountId) {
      setExpandedAccountId(null);
      setAccountSnapshots([]);
      return;
    }
    try {
      const snaps = await fireService.getSnapshots(accountId);
      setAccountSnapshots(snaps);
      setExpandedAccountId(accountId);
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to load snapshots');
    }
  };

  const handleDeleteSnapshot = (snapshotId, accountId) => {
    setConfirmModal({
      title: 'Delete Snapshot',
      message: 'Delete this snapshot?',
      danger: true,
      onConfirm: async () => {
        setConfirmModal(null);
        try {
          await fireService.deleteSnapshot(snapshotId);
          const snaps = await fireService.getSnapshots(accountId);
          setAccountSnapshots(snaps);
          loadAccounts();
          loadDashboard();
        } catch (err) {
          setError(getErrorMessage(err) || 'Failed to delete snapshot');
        }
      },
    });
  };

  const handleBulkImport = async () => {
    if (!bulkText.trim()) {
      setError('Please paste Monarch text data');
      return;
    }
    try {
      setLoading(true);
      setError('');
      const result = await fireService.bulkImportAccounts({
        text: bulkText,
        snapshot_date: bulkSnapshotDate,
      });
      setBulkImportResult(result);
      setBulkText('');
      loadAccounts();
      loadDashboard();
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to import accounts');
    } finally {
      setLoading(false);
    }
  };

  const handleTakeSnapshot = async () => {
    const entries = accounts
      .filter(a => snapshotBalances[a.id] !== undefined && snapshotBalances[a.id] !== '')
      .map(a => ({
        account_id: a.id,
        balance: parseFloat(snapshotBalances[a.id]),
        contributions_since_last: parseFloat(snapshotContributions[a.id] || 0),
      }));

    if (entries.length === 0) {
      setError('Please enter at least one account balance');
      return;
    }

    try {
      setLoading(true);
      setError('');
      await fireService.bulkCreateSnapshots({
        snapshot_date: snapshotDate,
        entries,
      });
      setShowSnapshotModal(false);
      setSnapshotBalances({});
      setSnapshotContributions({});
      loadAccounts();
      loadDashboard();
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to create snapshots');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAggSnapshot = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');
      await fireService.createAggregateSnapshot({
        snapshot_date: aggForm.snapshot_date,
        total_value: parseFloat(aggForm.total_value),
        contributions_since_last: aggForm.contributions_since_last ? parseFloat(aggForm.contributions_since_last) : 0,
        notes: aggForm.notes || null,
      });
      setAggForm({ snapshot_date: new Date().toISOString().split('T')[0], total_value: '', contributions_since_last: '', notes: '' });
      setShowAggForm(false);
      loadAggSnapshots();
      loadDashboard();
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to create aggregate snapshot');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAggSnapshot = (id) => {
    setConfirmModal({
      title: 'Delete Snapshot',
      message: 'Delete this aggregate snapshot?',
      danger: true,
      onConfirm: async () => {
        setConfirmModal(null);
        try {
          await fireService.deleteAggregateSnapshot(id);
          loadAggSnapshots();
          loadDashboard();
        } catch (err) {
          setError(getErrorMessage(err) || 'Failed to delete aggregate snapshot');
        }
      },
    });
  };

  const openSnapshotModal = () => {
    const balances = {};
    accounts.forEach(a => {
      balances[a.id] = a.latest_balance !== null ? String(a.latest_balance) : '';
    });
    setSnapshotBalances(balances);
    setSnapshotContributions({});
    setSnapshotDate(new Date().toISOString().split('T')[0]);
    setShowSnapshotModal(true);
  };

  const addScenario = () => {
    const maxId = scenarios.reduce((max, s) => Math.max(max, s.id), 0);
    setScenarios([...scenarios, { id: maxId + 1, growthRate: 7, swr: 4, annualExpenses: 100000 }]);
  };

  const removeScenario = (id) => {
    if (scenarios.length <= 1) return;
    setScenarios(scenarios.filter(s => s.id !== id));
  };

  const updateScenario = (id, field, value) => {
    setScenarios(scenarios.map(s => s.id === id ? { ...s, [field]: parseFloat(value) || 0 } : s));
  };

  // Confirm modal state
  const [confirmModal, setConfirmModal] = useState(null);

  // Snapshot editing state
  const [editingSnapshot, setEditingSnapshot] = useState(null);

  const handleEditSnapshot = async (snap) => {
    if (!editingSnapshot) {
      setEditingSnapshot({ ...snap });
      return;
    }
    try {
      await fireService.updateSnapshot(editingSnapshot.id, {
        balance: parseFloat(editingSnapshot.balance),
        contributions_since_last: parseFloat(editingSnapshot.contributions_since_last || 0),
        notes: editingSnapshot.notes || null,
      });
      const snaps = await fireService.getSnapshots(editingSnapshot.account_id);
      setAccountSnapshots(snaps);
      setEditingSnapshot(null);
      loadAccounts();
      loadDashboard();
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to update snapshot');
    }
  };

  // Sync current value from portfolio
  const handleSyncFromPortfolio = async () => {
    try {
      setLoading(true);
      const summary = await portfolioService.getSummary();
      if (summary.current_value != null) {
        setProjParams(prev => ({ ...prev, currentValue: summary.current_value }));
      } else if (summary.total_invested) {
        setProjParams(prev => ({ ...prev, currentValue: summary.total_invested }));
      }
    } catch (err) {
      setError('Could not fetch portfolio value. Make sure you have portfolio data.');
    } finally {
      setLoading(false);
    }
  };

  // Projection calculations
  const projectionData = useMemo(() => {
    const { currentValue, annualContribution, growthRate, inflationRate } = projParams;
    const r = growthRate / 100;
    const inf = (inflationRate || 0) / 100;
    const years = 50;
    const data = [];
    let portfolio = currentValue;
    let portfolioReal = currentValue;

    for (let y = 0; y <= years; y++) {
      const investmentIncome = y === 0 ? 0 : portfolio * r;
      const realGrowth = y === 0 ? 0 : portfolioReal * ((1 + r) / (1 + inf) - 1);
      if (y > 0) {
        portfolio = portfolio + investmentIncome + annualContribution;
        portfolioReal = portfolioReal + realGrowth + annualContribution / Math.pow(1 + inf, y);
      }
      data.push({
        year: y,
        age: projParams.currentAge + y,
        portfolio: Math.round(portfolio),
        portfolioReal: Math.round(portfolioReal),
        investmentIncome: Math.round(investmentIncome),
        withdrawalCapacity4: Math.round(portfolio * 0.04),
        withdrawalCapacity3_5: Math.round(portfolio * 0.035),
        withdrawalCapacity3: Math.round(portfolio * 0.03),
      });
    }
    return data;
  }, [projParams]);

  const fireMetrics = useMemo(() => {
    const { currentValue, annualContribution, growthRate, annualExpenses, swr } = projParams;
    const fireNumber = annualExpenses / (swr / 100);
    const gap = fireNumber - currentValue;
    const r = growthRate / 100;
    const progressPct = fireNumber > 0 ? Math.min(100, (currentValue / fireNumber) * 100) : 0;

    // Coast FIRE: portfolio that grows to FIRE number by targetAge without contributions
    const yearsToTarget = Math.max(0, projParams.targetAge - projParams.currentAge);
    const coastFireNumber = r > 0 ? fireNumber / Math.pow(1 + r, yearsToTarget) : fireNumber;
    const coastFireReached = currentValue >= coastFireNumber;

    // Barista FIRE: covers half expenses from portfolio, work for the rest
    const baristaFireNumber = (annualExpenses * 0.5) / (swr / 100);

    let yearsToFire = null;
    if (currentValue >= fireNumber) {
      yearsToFire = 0;
    } else if (r > 0) {
      let portfolio = currentValue;
      for (let y = 1; y <= 100; y++) {
        portfolio = portfolio * (1 + r) + annualContribution;
        if (portfolio >= fireNumber) {
          yearsToFire = y;
          break;
        }
      }
    }

    const monthlyIncomeAtFire = fireNumber * (swr / 100) / 12;
    const currentAnnualIncome = currentValue * (growthRate / 100);

    return {
      fireNumber, gap, yearsToFire, monthlyIncomeAtFire, currentAnnualIncome,
      progressPct, coastFireNumber, coastFireReached, baristaFireNumber,
    };
  }, [projParams]);

  // Monte Carlo simulation
  const monteCarloResults = useMemo(() => {
    const { currentValue, annualContribution, growthRate, annualExpenses, swr } = projParams;
    const fireNumber = annualExpenses / (swr / 100);
    const meanReturn = growthRate / 100;
    const stdDev = 0.16; // historical S&P 500 annual std dev
    const simulations = 1000;
    const years = 30;
    const results = [];

    const boxMuller = () => {
      let u = 0, v = 0;
      while (u === 0) u = Math.random();
      while (v === 0) v = Math.random();
      return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
    };

    for (let s = 0; s < simulations; s++) {
      let portfolio = currentValue;
      let reachedFire = false;
      const path = [portfolio];
      for (let y = 1; y <= years; y++) {
        const annualReturn = meanReturn + stdDev * boxMuller();
        portfolio = portfolio * (1 + annualReturn) + annualContribution;
        if (portfolio < 0) portfolio = 0;
        path.push(Math.round(portfolio));
        if (portfolio >= fireNumber) reachedFire = true;
      }
      results.push({ path, reachedFire, finalValue: portfolio });
    }

    const successCount = results.filter(r => r.reachedFire).length;
    const successRate = (successCount / simulations) * 100;

    const percentiles = [10, 25, 50, 75, 90];
    const percentileData = [];
    for (let y = 0; y <= years; y++) {
      const yearValues = results.map(r => r.path[y]).sort((a, b) => a - b);
      const entry = { year: y, age: projParams.currentAge + y };
      percentiles.forEach(p => {
        const idx = Math.floor((p / 100) * yearValues.length);
        entry[`p${p}`] = yearValues[Math.min(idx, yearValues.length - 1)];
      });
      percentileData.push(entry);
    }

    return { successRate, percentileData, simulations };
  }, [projParams]);

  const scenarioResults = useMemo(() => {
    return scenarios.map(s => {
      const fireNumber = s.annualExpenses / (s.swr / 100);
      const gap = fireNumber - projParams.currentValue;
      const r = s.growthRate / 100;

      let yearsToFire = null;
      if (projParams.currentValue >= fireNumber) {
        yearsToFire = 0;
      } else if (r > 0) {
        let portfolio = projParams.currentValue;
        for (let y = 1; y <= 100; y++) {
          portfolio = portfolio * (1 + r) + projParams.annualContribution;
          if (portfolio >= fireNumber) {
            yearsToFire = y;
            break;
          }
        }
      }

      return {
        ...s,
        fireNumber,
        gap,
        yearsToFire,
        fireAge: yearsToFire !== null ? projParams.currentAge + yearsToFire : null,
      };
    });
  }, [scenarios, projParams]);

  // Group accounts by owner for display
  const accountsByOwner = useMemo(() => {
    const grouped = {};
    accounts.forEach(a => {
      if (!grouped[a.owner]) grouped[a.owner] = [];
      grouped[a.owner].push(a);
    });
    return grouped;
  }, [accounts]);

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
          <button onClick={() => navigate('/')} style={styles.homeButton} title="Go to Home">
            🏠
          </button>
          <h1 style={styles.title}>FIRE Journey Tracker</h1>
        </div>
        <div style={styles.headerActions}>
          <span style={styles.userInfo}>Welcome, {user?.username || 'User'}</span>
          <button onClick={logout} style={styles.logoutButton}>Logout</button>
        </div>
      </header>

      <div style={styles.content}>
        {/* Tabs */}
        <div style={styles.tabs}>
          {['accounts', 'income', 'projections', 'docs'].map(tab => (
            <button
              key={tab}
              style={{ ...styles.tab, ...(activeTab === tab ? styles.tabActive : {}) }}
              onClick={() => setActiveTab(tab)}
            >
              {{ accounts: 'Accounts & Balances', income: 'Investment Income', projections: 'FIRE Projections', docs: 'Documentation' }[tab]}
            </button>
          ))}
        </div>

        {error && <div style={styles.errorBox}>{error}<button onClick={() => setError('')} style={styles.dismissBtn}>x</button></div>}

        <div style={styles.tabContent}>
          {/* ============ TAB 1: ACCOUNTS & BALANCES ============ */}
          {activeTab === 'accounts' && (
            <div>
              <h2 style={styles.sectionTitle}>Accounts & Balances</h2>

              {/* Dashboard Summary Cards */}
              {dashboard && (
                <div style={styles.metricsGrid}>
                  <div style={styles.metricCard}>
                    <div style={styles.metricLabel}>Total Portfolio</div>
                    <div style={styles.metricValue}>{formatCurrency(dashboard.total_portfolio_value)}</div>
                  </div>
                  {dashboard.by_owner?.map(o => (
                    <div key={o.owner} style={styles.metricCard}>
                      <div style={styles.metricLabel}>{o.owner}</div>
                      <div style={styles.metricValue}>{formatCurrency(o.total_value)}</div>
                      <div style={styles.metricSub}>{o.account_count} account{o.account_count !== 1 ? 's' : ''}</div>
                    </div>
                  ))}
                  {dashboard.month_over_month_change !== null && dashboard.month_over_month_change !== undefined && (
                    <div style={styles.metricCard}>
                      <div style={styles.metricLabel}>Last Period Change</div>
                      <div style={{
                        ...styles.metricValue,
                        color: dashboard.month_over_month_change >= 0 ? '#28a745' : '#dc3545',
                      }}>
                        {formatCurrency(dashboard.month_over_month_change)}
                      </div>
                      {dashboard.month_over_month_change_pct !== null && (
                        <div style={styles.metricSub}>{formatPercent(dashboard.month_over_month_change_pct)}</div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div style={styles.actionBar}>
                <button style={styles.primaryButton} onClick={() => { setShowAddForm(!showAddForm); setShowBulkImport(false); }}>
                  {showAddForm ? 'Cancel' : '+ Add Account'}
                </button>
                <button style={styles.secondaryButton} onClick={() => { setShowBulkImport(!showBulkImport); setShowAddForm(false); }}>
                  {showBulkImport ? 'Cancel' : 'Bulk Import'}
                </button>
                {accounts.length > 0 && (
                  <button style={styles.secondaryButton} onClick={openSnapshotModal}>
                    Take New Snapshot
                  </button>
                )}
              </div>

              {/* Add Account Form */}
              {showAddForm && (
                <div style={styles.formCard}>
                  <h3 style={styles.subsectionTitle}>Add New Account</h3>
                  <form onSubmit={handleCreateAccount}>
                    <div style={styles.formGrid}>
                      <div>
                        <label style={styles.label}>Account Name</label>
                        <input
                          style={styles.input}
                          value={accountForm.name}
                          onChange={e => setAccountForm({ ...accountForm, name: e.target.value })}
                          placeholder="e.g. Individual - TOD (..3467)"
                          required
                        />
                      </div>
                      <div>
                        <label style={styles.label}>Account Type</label>
                        <select
                          style={styles.input}
                          value={accountForm.account_type}
                          onChange={e => setAccountForm({ ...accountForm, account_type: e.target.value })}
                        >
                          {ACCOUNT_TYPES.map(t => (
                            <option key={t} value={t}>{ACCOUNT_TYPE_LABELS[t]}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label style={styles.label}>Owner</label>
                        <input
                          style={styles.input}
                          value={accountForm.owner}
                          onChange={e => setAccountForm({ ...accountForm, owner: e.target.value })}
                          placeholder="e.g. Mohammad"
                          required
                        />
                      </div>
                      <div>
                        <label style={styles.label}>Institution</label>
                        <input
                          style={styles.input}
                          value={accountForm.institution}
                          onChange={e => setAccountForm({ ...accountForm, institution: e.target.value })}
                          placeholder="e.g. Charles Schwab"
                        />
                      </div>
                      <div>
                        <label style={styles.label}>Last 4 Digits</label>
                        <input
                          style={styles.input}
                          value={accountForm.last_four}
                          onChange={e => setAccountForm({ ...accountForm, last_four: e.target.value })}
                          placeholder="e.g. 3467"
                          maxLength={4}
                        />
                      </div>
                      <div>
                        <label style={styles.label}>Current Balance ($)</label>
                        <input
                          style={styles.input}
                          type="number"
                          step="0.01"
                          value={accountForm.balance}
                          onChange={e => setAccountForm({ ...accountForm, balance: e.target.value })}
                          placeholder="0.00"
                        />
                      </div>
                    </div>
                    <div style={styles.formActions}>
                      <button type="submit" style={styles.primaryButton} disabled={loading}>
                        {loading ? 'Saving...' : 'Save Account'}
                      </button>
                      <button type="button" style={styles.secondaryButton} onClick={() => setShowAddForm(false)}>
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {/* Bulk Import */}
              {showBulkImport && (
                <div style={styles.formCard}>
                  <h3 style={styles.subsectionTitle}>Bulk Import from Monarch</h3>
                  <p style={styles.helpText}>
                    Copy and paste the text from your Monarch Money investments view. The parser will extract
                    account names, types, owners, and balances automatically. Set the snapshot date to when
                    these balances were recorded.
                  </p>
                  <div style={{ marginBottom: '1rem' }}>
                    <label style={styles.label}>Snapshot Date</label>
                    <input
                      style={{ ...styles.input, maxWidth: '220px' }}
                      type="date"
                      value={bulkSnapshotDate}
                      onChange={e => setBulkSnapshotDate(e.target.value)}
                    />
                  </div>
                  <textarea
                    style={{ ...styles.textarea, minHeight: '200px' }}
                    value={bulkText}
                    onChange={e => setBulkText(e.target.value)}
                    placeholder={"Robo Investment ..274 (..Robo Investment ..274)\nBrokerage (Taxable)   Mohammad\n$34,619.09\n19 hours ago\n..."}
                  />
                  <div style={styles.formActions}>
                    <button style={styles.primaryButton} onClick={handleBulkImport} disabled={loading}>
                      {loading ? 'Importing...' : 'Import'}
                    </button>
                    <button style={styles.secondaryButton} onClick={() => setShowBulkImport(false)}>Cancel</button>
                  </div>
                  {bulkImportResult && (
                    <div style={styles.successBox}>
                      <strong>Import Complete:</strong> {bulkImportResult.accounts_created} created,{' '}
                      {bulkImportResult.accounts_updated} updated, {bulkImportResult.snapshots_created} snapshots recorded.
                    </div>
                  )}
                </div>
              )}

              {/* Snapshot Modal */}
              {showSnapshotModal && (
                <div style={styles.modalOverlay}>
                  <div style={styles.modal}>
                    <h3 style={styles.subsectionTitle}>Record New Snapshot</h3>
                    <div style={{ marginBottom: '1rem' }}>
                      <label style={styles.label}>Snapshot Date</label>
                      <input
                        style={styles.input}
                        type="date"
                        value={snapshotDate}
                        onChange={e => setSnapshotDate(e.target.value)}
                      />
                    </div>
                    <div style={styles.snapshotTable}>
                      <div style={styles.snapshotHeader}>
                        <span style={{ flex: 2 }}>Account</span>
                        <span style={{ flex: 1 }}>Balance ($)</span>
                        <span style={{ flex: 1 }}>Contributions ($)</span>
                      </div>
                      {accounts.map(a => (
                        <div key={a.id} style={styles.snapshotRow}>
                          <span style={{ flex: 2 }}>
                            <strong>{a.name}</strong>
                            <br />
                            <small style={{ color: '#666' }}>{a.owner} - {ACCOUNT_TYPE_LABELS[a.account_type] || a.account_type}</small>
                          </span>
                          <span style={{ flex: 1 }}>
                            <input
                              style={styles.inputSmall}
                              type="number"
                              step="0.01"
                              value={snapshotBalances[a.id] || ''}
                              onChange={e => setSnapshotBalances({ ...snapshotBalances, [a.id]: e.target.value })}
                              placeholder={a.latest_balance !== null ? String(a.latest_balance) : '0.00'}
                            />
                          </span>
                          <span style={{ flex: 1 }}>
                            <input
                              style={styles.inputSmall}
                              type="number"
                              step="0.01"
                              value={snapshotContributions[a.id] || ''}
                              onChange={e => setSnapshotContributions({ ...snapshotContributions, [a.id]: e.target.value })}
                              placeholder="0.00"
                            />
                          </span>
                        </div>
                      ))}
                    </div>
                    <div style={styles.formActions}>
                      <button style={styles.primaryButton} onClick={handleTakeSnapshot} disabled={loading}>
                        {loading ? 'Saving...' : 'Save Snapshot'}
                      </button>
                      <button style={styles.secondaryButton} onClick={() => setShowSnapshotModal(false)}>Cancel</button>
                    </div>
                  </div>
                </div>
              )}

              {/* Edit Account Inline */}
              {editingAccount && (
                <div style={styles.formCard}>
                  <h3 style={styles.subsectionTitle}>Edit Account</h3>
                  <form onSubmit={handleUpdateAccount}>
                    <div style={styles.formGrid}>
                      <div>
                        <label style={styles.label}>Account Name</label>
                        <input
                          style={styles.input}
                          value={editingAccount.name}
                          onChange={e => setEditingAccount({ ...editingAccount, name: e.target.value })}
                        />
                      </div>
                      <div>
                        <label style={styles.label}>Account Type</label>
                        <select
                          style={styles.input}
                          value={editingAccount.account_type}
                          onChange={e => setEditingAccount({ ...editingAccount, account_type: e.target.value })}
                        >
                          {ACCOUNT_TYPES.map(t => (
                            <option key={t} value={t}>{ACCOUNT_TYPE_LABELS[t]}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label style={styles.label}>Owner</label>
                        <input
                          style={styles.input}
                          value={editingAccount.owner}
                          onChange={e => setEditingAccount({ ...editingAccount, owner: e.target.value })}
                        />
                      </div>
                      <div>
                        <label style={styles.label}>Institution</label>
                        <input
                          style={styles.input}
                          value={editingAccount.institution || ''}
                          onChange={e => setEditingAccount({ ...editingAccount, institution: e.target.value })}
                        />
                      </div>
                      <div>
                        <label style={styles.label}>Active</label>
                        <select
                          style={styles.input}
                          value={editingAccount.is_active ? 'true' : 'false'}
                          onChange={e => setEditingAccount({ ...editingAccount, is_active: e.target.value === 'true' })}
                        >
                          <option value="true">Active</option>
                          <option value="false">Inactive</option>
                        </select>
                      </div>
                    </div>
                    <div style={styles.formActions}>
                      <button type="submit" style={styles.primaryButton} disabled={loading}>Save</button>
                      <button type="button" style={styles.secondaryButton} onClick={() => setEditingAccount(null)}>Cancel</button>
                    </div>
                  </form>
                </div>
              )}

              {/* Aggregate Portfolio Snapshots */}
              <div style={{ marginTop: '1.5rem', borderTop: '1px solid #ddd', paddingTop: '1.5rem' }}>
                <div style={styles.sectionHeader}>
                  <h3 style={styles.subsectionTitle}>Historical Portfolio Totals</h3>
                  <button style={styles.primaryButton} onClick={() => setShowAggForm(!showAggForm)}>
                    {showAggForm ? 'Cancel' : '+ Add Historical Snapshot'}
                  </button>
                </div>
                <p style={styles.helpText}>
                  Record total portfolio values from past dates (e.g. from Monarch's change headers)
                  when you don't have per-account breakdowns. These are used alongside per-account
                  snapshots to calculate investment income over time.
                </p>

                {showAggForm && (
                  <div style={styles.formCard}>
                    <form onSubmit={handleCreateAggSnapshot}>
                      <div style={styles.formGrid}>
                        <div>
                          <label style={styles.label}>Snapshot Date</label>
                          <input
                            style={styles.input}
                            type="date"
                            value={aggForm.snapshot_date}
                            onChange={e => setAggForm({ ...aggForm, snapshot_date: e.target.value })}
                            required
                          />
                        </div>
                        <div>
                          <label style={styles.label}>Total Portfolio Value ($)</label>
                          <input
                            style={styles.input}
                            type="number"
                            step="0.01"
                            value={aggForm.total_value}
                            onChange={e => setAggForm({ ...aggForm, total_value: e.target.value })}
                            placeholder="e.g. 3458173.61"
                            required
                          />
                        </div>
                        <div>
                          <label style={styles.label}>Contributions Since Prior ($)</label>
                          <input
                            style={styles.input}
                            type="number"
                            step="0.01"
                            value={aggForm.contributions_since_last}
                            onChange={e => setAggForm({ ...aggForm, contributions_since_last: e.target.value })}
                            placeholder="0.00"
                          />
                        </div>
                        <div>
                          <label style={styles.label}>Notes</label>
                          <input
                            style={styles.input}
                            value={aggForm.notes}
                            onChange={e => setAggForm({ ...aggForm, notes: e.target.value })}
                            placeholder="e.g. From Monarch 1-year header"
                          />
                        </div>
                      </div>
                      <div style={styles.formActions}>
                        <button type="submit" style={styles.primaryButton} disabled={loading}>
                          {loading ? 'Saving...' : 'Save Snapshot'}
                        </button>
                        <button type="button" style={styles.secondaryButton} onClick={() => setShowAggForm(false)}>
                          Cancel
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                {aggSnapshots.length > 0 && (
                  <div style={styles.tableContainer}>
                    <table style={styles.table}>
                      <thead>
                        <tr>
                          <th style={styles.th}>Date</th>
                          <th style={{ ...styles.th, textAlign: 'right' }}>Total Value</th>
                          <th style={{ ...styles.th, textAlign: 'right' }}>Contributions</th>
                          <th style={styles.th}>Notes</th>
                          <th style={styles.th}></th>
                        </tr>
                      </thead>
                      <tbody>
                        {aggSnapshots.map(s => (
                          <tr key={s.id}>
                            <td style={styles.td}>{s.snapshot_date}</td>
                            <td style={{ ...styles.td, textAlign: 'right', fontWeight: 'bold' }}>{formatCurrencyPrecise(s.total_value)}</td>
                            <td style={{ ...styles.td, textAlign: 'right' }}>{s.contributions_since_last ? formatCurrencyPrecise(s.contributions_since_last) : '-'}</td>
                            <td style={styles.td}>{s.notes || '-'}</td>
                            <td style={styles.td}>
                              <button style={styles.iconBtn} onClick={() => handleDeleteAggSnapshot(s.id)} title="Delete">
                                🗑️
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Accounts Table Grouped by Owner */}
              {loading && accounts.length === 0 ? (
                <p>Loading accounts...</p>
              ) : accounts.length === 0 ? (
                <div style={styles.emptyState}>
                  <p>No investment accounts yet. Add accounts manually or use bulk import from Monarch.</p>
                </div>
              ) : (
                Object.entries(accountsByOwner).map(([owner, ownerAccounts]) => (
                  <div key={owner} style={styles.ownerGroup}>
                    <h3 style={styles.ownerTitle}>
                      {owner}
                      <span style={styles.ownerTotal}>
                        {formatCurrency(ownerAccounts.reduce((sum, a) => sum + (a.latest_balance || 0), 0))}
                      </span>
                    </h3>
                    <div style={styles.tableContainer}>
                      <table style={styles.table}>
                        <thead>
                          <tr>
                            <th style={styles.th}>Account</th>
                            <th style={styles.th}>Type</th>
                            <th style={styles.th}>Institution</th>
                            <th style={{ ...styles.th, textAlign: 'right' }}>Balance</th>
                            <th style={styles.th}>Last Updated</th>
                            <th style={styles.th}>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {ownerAccounts.map(a => (
                            <React.Fragment key={a.id}>
                              <tr>
                                <td style={styles.td}>
                                  <strong>{a.name}</strong>
                                  {a.last_four && <span style={{ color: '#999', marginLeft: '4px' }}>({a.last_four})</span>}
                                </td>
                                <td style={styles.td}>
                                  <span style={styles.badge}>{ACCOUNT_TYPE_LABELS[a.account_type] || a.account_type}</span>
                                </td>
                                <td style={styles.td}>{a.institution || '-'}</td>
                                <td style={{ ...styles.td, textAlign: 'right', fontWeight: 'bold' }}>
                                  {a.latest_balance !== null ? formatCurrencyPrecise(a.latest_balance) : '-'}
                                </td>
                                <td style={styles.td}>{a.latest_snapshot_date || '-'}</td>
                                <td style={styles.td}>
                                  <button
                                    style={styles.iconBtn}
                                    onClick={() => toggleSnapshots(a.id)}
                                    title={expandedAccountId === a.id ? 'Hide snapshots' : 'Show snapshots'}
                                  >
                                    {expandedAccountId === a.id ? '📋' : '📊'}
                                  </button>
                                  <button style={styles.iconBtn} onClick={() => setEditingAccount({ ...a })} title="Edit">
                                    ✏️
                                  </button>
                                  <button style={styles.iconBtn} onClick={() => handleDeleteAccount(a.id)} title="Delete">
                                    🗑️
                                  </button>
                                </td>
                              </tr>
                              {expandedAccountId === a.id && (
                                <tr>
                                  <td colSpan={6} style={{ padding: 0 }}>
                                    <div style={styles.snapshotsPanel}>
                                      <div style={styles.snapshotsPanelHeader}>
                                        <strong>Snapshots for {a.name}</strong>
                                        <span style={{ color: '#666', fontSize: '0.85rem' }}>{accountSnapshots.length} snapshot{accountSnapshots.length !== 1 ? 's' : ''}</span>
                                      </div>
                                      {accountSnapshots.length === 0 ? (
                                        <p style={{ color: '#666', padding: '0.5rem 0' }}>No snapshots recorded.</p>
                                      ) : (
                                        <table style={{ ...styles.table, fontSize: '0.85rem' }}>
                                          <thead>
                                            <tr>
                                              <th style={styles.thSm}>Date</th>
                                              <th style={{ ...styles.thSm, textAlign: 'right' }}>Balance</th>
                                              <th style={{ ...styles.thSm, textAlign: 'right' }}>Contributions</th>
                                              <th style={styles.thSm}>Notes</th>
                                              <th style={styles.thSm}></th>
                                            </tr>
                                          </thead>
                                          <tbody>
                                            {accountSnapshots.map(snap => (
                                              <tr key={snap.id}>
                                                <td style={styles.tdSm}>{snap.snapshot_date}</td>
                                                <td style={{ ...styles.tdSm, textAlign: 'right' }}>
                                                  {editingSnapshot?.id === snap.id ? (
                                                    <input style={styles.inputSmall} type="number" step="0.01" value={editingSnapshot.balance}
                                                      onChange={e => setEditingSnapshot({ ...editingSnapshot, balance: e.target.value })} />
                                                  ) : formatCurrencyPrecise(snap.balance)}
                                                </td>
                                                <td style={{ ...styles.tdSm, textAlign: 'right' }}>
                                                  {editingSnapshot?.id === snap.id ? (
                                                    <input style={styles.inputSmall} type="number" step="0.01" value={editingSnapshot.contributions_since_last || ''}
                                                      onChange={e => setEditingSnapshot({ ...editingSnapshot, contributions_since_last: e.target.value })} />
                                                  ) : snap.contributions_since_last ? formatCurrencyPrecise(snap.contributions_since_last) : '-'}
                                                </td>
                                                <td style={styles.tdSm}>
                                                  {editingSnapshot?.id === snap.id ? (
                                                    <input style={styles.inputSmall} value={editingSnapshot.notes || ''}
                                                      onChange={e => setEditingSnapshot({ ...editingSnapshot, notes: e.target.value })} />
                                                  ) : snap.notes || '-'}
                                                </td>
                                                <td style={styles.tdSm}>
                                                  {editingSnapshot?.id === snap.id ? (
                                                    <>
                                                      <button style={styles.iconBtn} onClick={() => handleEditSnapshot(snap)} title="Save">
                                                        💾
                                                      </button>
                                                      <button style={styles.iconBtn} onClick={() => setEditingSnapshot(null)} title="Cancel">
                                                        ✖️
                                                      </button>
                                                    </>
                                                  ) : (
                                                    <>
                                                      <button style={styles.iconBtn} onClick={() => setEditingSnapshot({ ...snap })} title="Edit snapshot">
                                                        ✏️
                                                      </button>
                                                      <button
                                                        style={styles.iconBtn}
                                                        onClick={() => handleDeleteSnapshot(snap.id, a.id)}
                                                        title="Delete snapshot"
                                                      >
                                                        🗑️
                                                      </button>
                                                    </>
                                                  )}
                                                </td>
                                              </tr>
                                            ))}
                                          </tbody>
                                        </table>
                                      )}
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
                ))
              )}

              {/* Account Type Breakdown */}
              {dashboard && dashboard.by_account_type?.length > 0 && (
                <div style={{ marginTop: '2rem' }}>
                  <h3 style={styles.subsectionTitle}>By Account Type</h3>
                  <div style={styles.metricsGrid}>
                    {dashboard.by_account_type.map(t => (
                      <div key={t.account_type} style={styles.metricCard}>
                        <div style={styles.metricLabel}>{ACCOUNT_TYPE_LABELS[t.account_type] || t.account_type}</div>
                        <div style={styles.metricValue}>{formatCurrency(t.total_value)}</div>
                        <div style={styles.metricSub}>{t.account_count} account{t.account_count !== 1 ? 's' : ''}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ============ TAB 2: INVESTMENT INCOME ============ */}
          {activeTab === 'income' && (
            <div>
              <div style={styles.sectionHeader}>
                <h2 style={styles.sectionTitle}>Investment Income</h2>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={styles.intervalToggle}>
                    {['monthly', 'quarterly', 'yearly'].map(iv => (
                      <button
                        key={iv}
                        style={{
                          ...styles.intervalBtn,
                          ...(incomeInterval === iv ? styles.intervalBtnActive : {}),
                        }}
                        onClick={() => setIncomeInterval(iv)}
                      >
                        {iv.charAt(0).toUpperCase() + iv.slice(1)}
                      </button>
                    ))}
                  </div>
                  {accounts.length > 0 && (
                    <div ref={filterRef} style={styles.filterContainer}>
                      <button
                        style={{
                          ...styles.filterBtn,
                          ...(selectedAccountIds !== null && selectedAccountIds.length !== accounts.length
                            ? styles.filterBtnActive : {}),
                        }}
                        onClick={() => setShowAccountFilter(f => !f)}
                      >
                        <span>&#9776;</span>
                        {selectedAccountIds !== null && selectedAccountIds.length !== accounts.length
                          ? `${selectedAccountIds.length} of ${accounts.length} accounts`
                          : 'All Accounts'}
                      </button>
                      {showAccountFilter && (
                        <div style={styles.filterDropdown}>
                          <div style={styles.filterHeader}>
                            <span style={styles.filterHeaderLabel}>Filter Accounts</span>
                            <div style={styles.filterActions}>
                              <button
                                style={styles.filterActionBtn}
                                onClick={() => setSelectedAccountIds(accounts.map(a => a.id))}
                              >
                                Select All
                              </button>
                              <button
                                style={styles.filterActionBtn}
                                onClick={() => setSelectedAccountIds([])}
                              >
                                Deselect All
                              </button>
                            </div>
                          </div>
                          <div style={styles.filterList}>
                            {accounts.map(acct => {
                              const ids = selectedAccountIds ?? accounts.map(a => a.id);
                              const checked = ids.includes(acct.id);
                              return (
                                <label
                                  key={acct.id}
                                  style={styles.filterItem}
                                  onMouseEnter={e => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                                  onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
                                >
                                  <input
                                    type="checkbox"
                                    style={styles.filterCheckbox}
                                    checked={checked}
                                    onChange={() => {
                                      const current = selectedAccountIds ?? accounts.map(a => a.id);
                                      setSelectedAccountIds(
                                        checked
                                          ? current.filter(id => id !== acct.id)
                                          : [...current, acct.id]
                                      );
                                    }}
                                  />
                                  <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                    {acct.name}
                                  </span>
                                  {acct.latest_balance != null && (
                                    <span style={{ color: '#888', fontSize: '0.78rem', flexShrink: 0 }}>
                                      {formatCurrency(acct.latest_balance)}
                                    </span>
                                  )}
                                </label>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {!incomeHistory || incomeHistory.entries.length === 0 ? (
                <div style={styles.emptyState}>
                  <p>
                    No income history yet. You need at least two snapshots to calculate investment income.
                    Go to the Accounts tab to record snapshots over time.
                  </p>
                </div>
              ) : (
                <>
                  {/* Summary Metrics */}
                  <div style={styles.metricsGrid}>
                    <div style={styles.metricCard}>
                      <div style={styles.metricLabel}>Total Investment Income</div>
                      <div style={{
                        ...styles.metricValue,
                        color: incomeHistory.total_investment_income >= 0 ? '#28a745' : '#dc3545',
                      }}>
                        {formatCurrency(incomeHistory.total_investment_income)}
                      </div>
                    </div>
                    {incomeHistory.entries.length > 0 && (
                      <div style={styles.metricCard}>
                        <div style={styles.metricLabel}>Last Period Income</div>
                        <div style={{
                          ...styles.metricValue,
                          color: incomeHistory.entries[incomeHistory.entries.length - 1].investment_income >= 0 ? '#28a745' : '#dc3545',
                        }}>
                          {formatCurrency(incomeHistory.entries[incomeHistory.entries.length - 1].investment_income)}
                        </div>
                        <div style={styles.metricSub}>
                          {formatPercent(incomeHistory.entries[incomeHistory.entries.length - 1].growth_rate_pct)}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Income Chart */}
                  <div style={{ marginBottom: '2rem' }}>
                    <h3 style={styles.subsectionTitle}>Portfolio Growth Over Time</h3>
                    <ResponsiveContainer width="100%" height={400}>
                      <ComposedChart data={incomeHistory.entries}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="period_end" />
                        <YAxis
                          yAxisId="left"
                          tickFormatter={v => v >= 1000000 ? `$${(v / 1000000).toFixed(1)}M` : `$${(v / 1000).toFixed(0)}k`}
                        />
                        <YAxis
                          yAxisId="right"
                          orientation="right"
                          tickFormatter={v => v >= 1000000 ? `$${(v / 1000000).toFixed(1)}M` : `$${(v / 1000).toFixed(0)}k`}
                          stroke="#999"
                        />
                        <Tooltip
                          formatter={(value, name) => [formatCurrency(value), name]}
                          labelFormatter={l => `Period ending: ${l}`}
                        />
                        <Legend />
                        <Bar yAxisId="left" dataKey="investment_income" fill="#28a745" name="Investment Income" />
                        <Line yAxisId="right" type="monotone" dataKey="ending_balance" stroke="#999" name="Ending Balance" dot={false} strokeWidth={2} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Income Breakdown Table */}
                  <h3 style={styles.subsectionTitle}>Period-by-Period Breakdown</h3>
                  <div style={styles.tableContainer}>
                    <table style={styles.table}>
                      <thead>
                        <tr>
                          <th style={styles.th}>Period</th>
                          <th style={{ ...styles.th, textAlign: 'right' }}>Starting Balance</th>
                          <th style={{ ...styles.th, textAlign: 'right' }}>Ending Balance</th>
                          <th style={{ ...styles.th, textAlign: 'right' }}>Investment Income</th>
                          <th style={{ ...styles.th, textAlign: 'right' }}>Growth Rate</th>
                        </tr>
                      </thead>
                      <tbody>
                        {[...incomeHistory.entries].reverse().map((entry, idx) => (
                          <tr key={idx}>
                            <td style={styles.td}>{entry.period_start} to {entry.period_end}</td>
                            <td style={{ ...styles.td, textAlign: 'right' }}>{formatCurrency(entry.starting_balance)}</td>
                            <td style={{ ...styles.td, textAlign: 'right' }}>{formatCurrency(entry.ending_balance)}</td>
                            <td style={{
                              ...styles.td,
                              textAlign: 'right',
                              fontWeight: 'bold',
                              color: entry.investment_income >= 0 ? '#28a745' : '#dc3545',
                            }}>
                              {formatCurrency(entry.investment_income)}
                            </td>
                            <td style={{
                              ...styles.td,
                              textAlign: 'right',
                              color: entry.growth_rate_pct >= 0 ? '#28a745' : '#dc3545',
                            }}>
                              {formatPercent(entry.growth_rate_pct)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </div>
          )}

          {/* ============ TAB 3: FIRE PROJECTIONS ============ */}
          {activeTab === 'projections' && (
            <div>
              <h2 style={styles.sectionTitle}>FIRE Projections</h2>

              {/* Input Parameters */}
              <div style={styles.formCard}>
                <div style={styles.sectionHeader}>
                  <h3 style={styles.subsectionTitle}>Parameters</h3>
                  <button style={styles.secondaryButton} onClick={handleSyncFromPortfolio} disabled={loading}>
                    {loading ? 'Syncing...' : 'Sync Value from Portfolio'}
                  </button>
                </div>
                <div style={styles.formGrid}>
                  <div>
                    <label style={styles.label}>Current Portfolio Value ($)</label>
                    <input
                      style={styles.input}
                      type="number"
                      value={projParams.currentValue}
                      onChange={e => setProjParams({ ...projParams, currentValue: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                  <div>
                    <label style={styles.label}>Annual Contributions ($)</label>
                    <input
                      style={styles.input}
                      type="number"
                      value={projParams.annualContribution}
                      onChange={e => setProjParams({ ...projParams, annualContribution: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                  <div>
                    <label style={styles.label}>Expected Annual Return (%)</label>
                    <input
                      style={styles.input}
                      type="number"
                      step="0.1"
                      min="0"
                      max="30"
                      value={projParams.growthRate}
                      onChange={e => setProjParams({ ...projParams, growthRate: parseFloat(e.target.value) || 0 })}
                    />
                    <input
                      type="range" min="0" max="15" step="0.5"
                      value={projParams.growthRate}
                      onChange={e => setProjParams({ ...projParams, growthRate: parseFloat(e.target.value) })}
                      style={{ width: '100%', marginTop: '0.25rem' }}
                    />
                  </div>
                  <div>
                    <label style={styles.label}>Inflation Rate (%)</label>
                    <input
                      style={styles.input}
                      type="number"
                      step="0.1"
                      min="0"
                      max="15"
                      value={projParams.inflationRate}
                      onChange={e => setProjParams({ ...projParams, inflationRate: parseFloat(e.target.value) || 0 })}
                    />
                    <input
                      type="range" min="0" max="8" step="0.5"
                      value={projParams.inflationRate}
                      onChange={e => setProjParams({ ...projParams, inflationRate: parseFloat(e.target.value) })}
                      style={{ width: '100%', marginTop: '0.25rem' }}
                    />
                  </div>
                  <div>
                    <label style={styles.label}>Annual Expenses in Retirement ($)</label>
                    <input
                      style={styles.input}
                      type="number"
                      value={projParams.annualExpenses}
                      onChange={e => setProjParams({ ...projParams, annualExpenses: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                  <div>
                    <label style={styles.label}>Safe Withdrawal Rate (%)</label>
                    <input
                      style={styles.input}
                      type="number"
                      step="0.1"
                      min="1"
                      max="10"
                      value={projParams.swr}
                      onChange={e => setProjParams({ ...projParams, swr: parseFloat(e.target.value) || 4 })}
                    />
                    <input
                      type="range" min="2" max="6" step="0.25"
                      value={projParams.swr}
                      onChange={e => setProjParams({ ...projParams, swr: parseFloat(e.target.value) })}
                      style={{ width: '100%', marginTop: '0.25rem' }}
                    />
                  </div>
                  <div>
                    <label style={styles.label}>Current Age</label>
                    <input
                      style={styles.input}
                      type="number"
                      value={projParams.currentAge}
                      onChange={e => setProjParams({ ...projParams, currentAge: parseInt(e.target.value) || 30 })}
                    />
                  </div>
                  <div>
                    <label style={styles.label}>Target Retirement Age</label>
                    <input
                      style={styles.input}
                      type="number"
                      value={projParams.targetAge}
                      onChange={e => setProjParams({ ...projParams, targetAge: parseInt(e.target.value) || 65 })}
                    />
                  </div>
                </div>
              </div>

              {/* FIRE Progress Bar (C5) */}
              <div style={{ marginBottom: '1.5rem', backgroundColor: '#f8f9fa', borderRadius: '8px', padding: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontWeight: '600', color: '#333' }}>Progress to FIRE</span>
                  <span style={{ fontWeight: '700', color: fireMetrics.progressPct >= 100 ? '#28a745' : '#007bff' }}>
                    {fireMetrics.progressPct.toFixed(1)}%
                  </span>
                </div>
                <div style={{ backgroundColor: '#e9ecef', borderRadius: '8px', height: '24px', position: 'relative', overflow: 'hidden' }}>
                  <div style={{
                    width: `${Math.min(100, fireMetrics.progressPct)}%`,
                    height: '100%',
                    backgroundColor: fireMetrics.progressPct >= 100 ? '#28a745' : '#007bff',
                    borderRadius: '8px',
                    transition: 'width 0.5s ease',
                  }} />
                  {[25, 50, 75].map(mark => (
                    <div key={mark} style={{
                      position: 'absolute', top: 0, left: `${mark}%`, width: '1px', height: '100%',
                      backgroundColor: 'rgba(0,0,0,0.15)',
                    }} />
                  ))}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem', fontSize: '0.78rem', color: '#888' }}>
                  <span>$0</span>
                  <span>{formatCurrency(fireMetrics.fireNumber * 0.25)}</span>
                  <span>{formatCurrency(fireMetrics.fireNumber * 0.5)}</span>
                  <span>{formatCurrency(fireMetrics.fireNumber * 0.75)}</span>
                  <span>{formatCurrency(fireMetrics.fireNumber)}</span>
                </div>
              </div>

              {/* FIRE Metrics */}
              <div style={styles.metricsGrid}>
                <div style={{ ...styles.metricCard, borderLeft: '4px solid #007bff' }}>
                  <div style={styles.metricLabel}>FIRE Number</div>
                  <div style={styles.metricValue}>{formatCurrency(fireMetrics.fireNumber)}</div>
                  <div style={styles.metricSub}>{formatCurrency(projParams.annualExpenses)}/yr at {projParams.swr}% SWR</div>
                </div>
                <div style={{ ...styles.metricCard, borderLeft: '4px solid #ffc107' }}>
                  <div style={styles.metricLabel}>Gap to FIRE</div>
                  <div style={{
                    ...styles.metricValue,
                    color: fireMetrics.gap <= 0 ? '#28a745' : '#333',
                  }}>
                    {fireMetrics.gap <= 0 ? 'FIRE Achieved!' : formatCurrency(fireMetrics.gap)}
                  </div>
                </div>
                <div style={{ ...styles.metricCard, borderLeft: '4px solid #28a745' }}>
                  <div style={styles.metricLabel}>Years to FIRE</div>
                  <div style={styles.metricValue}>
                    {fireMetrics.yearsToFire !== null
                      ? fireMetrics.yearsToFire === 0
                        ? 'Now!'
                        : `${fireMetrics.yearsToFire} years`
                      : '100+ years'}
                  </div>
                  {fireMetrics.yearsToFire !== null && fireMetrics.yearsToFire > 0 && (
                    <div style={styles.metricSub}>At age {projParams.currentAge + fireMetrics.yearsToFire}</div>
                  )}
                </div>
                <div style={{ ...styles.metricCard, borderLeft: '4px solid #6f42c1' }}>
                  <div style={styles.metricLabel}>Current Annual Investment Income</div>
                  <div style={styles.metricValue}>{formatCurrency(fireMetrics.currentAnnualIncome)}</div>
                  <div style={styles.metricSub}>{formatCurrency(fireMetrics.currentAnnualIncome / 12)}/month</div>
                </div>
              </div>

              {/* Milestone Cards */}
              <div style={{ ...styles.metricsGrid, marginBottom: '2rem' }}>
                <div style={{ ...styles.metricCard, borderLeft: `4px solid ${fireMetrics.coastFireReached ? '#28a745' : '#6c757d'}` }}>
                  <div style={styles.metricLabel}>Coast FIRE</div>
                  <div style={styles.metricValue}>
                    {fireMetrics.coastFireReached ? 'Reached!' : formatCurrency(fireMetrics.coastFireNumber)}
                  </div>
                  <div style={styles.metricSub}>
                    No contributions needed by age {projParams.targetAge}
                  </div>
                </div>
                <div style={{ ...styles.metricCard, borderLeft: `4px solid ${projParams.currentValue >= fireMetrics.baristaFireNumber ? '#28a745' : '#fd7e14'}` }}>
                  <div style={styles.metricLabel}>Barista FIRE</div>
                  <div style={styles.metricValue}>
                    {projParams.currentValue >= fireMetrics.baristaFireNumber ? 'Reached!' : formatCurrency(fireMetrics.baristaFireNumber)}
                  </div>
                  <div style={styles.metricSub}>50% expenses from portfolio</div>
                </div>
                <div style={{ ...styles.metricCard, borderLeft: '4px solid #17a2b8' }}>
                  <div style={styles.metricLabel}>Monte Carlo Success Rate</div>
                  <div style={{ ...styles.metricValue, color: monteCarloResults.successRate >= 80 ? '#28a745' : monteCarloResults.successRate >= 50 ? '#ffc107' : '#dc3545' }}>
                    {monteCarloResults.successRate.toFixed(0)}%
                  </div>
                  <div style={styles.metricSub}>{monteCarloResults.simulations} simulations over 30 years</div>
                </div>
              </div>

              {/* Projection Chart */}
              <div style={{ marginBottom: '2rem' }}>
                <h3 style={styles.subsectionTitle}>Portfolio Growth Projection</h3>
                <ResponsiveContainer width="100%" height={450}>
                  <AreaChart data={projectionData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="age"
                      label={{ value: 'Age', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis
                      tickFormatter={v => v >= 1000000 ? `$${(v / 1000000).toFixed(1)}M` : `$${(v / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      formatter={(value, name) => {
                        const labels = {
                          portfolio: 'Portfolio (Nominal)',
                          portfolioReal: 'Portfolio (Inflation-Adjusted)',
                          investmentIncome: 'Annual Investment Income',
                        };
                        return [formatCurrency(value), labels[name] || name];
                      }}
                      labelFormatter={l => `Age ${l}`}
                    />
                    <Legend />
                    <ReferenceLine
                      y={fireMetrics.fireNumber}
                      stroke="#dc3545"
                      strokeDasharray="5 5"
                      label={{ value: `FIRE: ${formatCurrency(fireMetrics.fireNumber)}`, position: 'right', fill: '#dc3545' }}
                    />
                    <ReferenceLine
                      x={projParams.targetAge}
                      stroke="#6f42c1"
                      strokeDasharray="4 4"
                      label={{ value: `Target: ${projParams.targetAge}`, position: 'top', fill: '#6f42c1' }}
                    />
                    <Area
                      type="monotone"
                      dataKey="portfolio"
                      stroke="#007bff"
                      fill="#007bff"
                      fillOpacity={0.1}
                      name="portfolio"
                    />
                    {projParams.inflationRate > 0 && (
                      <Area
                        type="monotone"
                        dataKey="portfolioReal"
                        stroke="#fd7e14"
                        fill="#fd7e14"
                        fillOpacity={0.05}
                        strokeDasharray="5 5"
                        name="portfolioReal"
                      />
                    )}
                    <Area
                      type="monotone"
                      dataKey="investmentIncome"
                      stroke="#28a745"
                      fill="#28a745"
                      fillOpacity={0.1}
                      name="investmentIncome"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Withdrawal Capacity Chart */}
              <div style={{ marginBottom: '2rem' }}>
                <h3 style={styles.subsectionTitle}>Annual Withdrawal Capacity Over Time</h3>
                <ResponsiveContainer width="100%" height={350}>
                  <AreaChart data={projectionData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="age" label={{ value: 'Age', position: 'insideBottom', offset: -5 }} />
                    <YAxis tickFormatter={v => v >= 1000000 ? `$${(v / 1000000).toFixed(1)}M` : `$${(v / 1000).toFixed(0)}k`} />
                    <Tooltip
                      formatter={(value, name) => {
                        const labels = {
                          withdrawalCapacity4: '4% SWR',
                          withdrawalCapacity3_5: '3.5% SWR',
                          withdrawalCapacity3: '3% SWR',
                        };
                        return [formatCurrency(value), labels[name] || name];
                      }}
                      labelFormatter={l => `Age ${l}`}
                    />
                    <Legend />
                    <ReferenceLine
                      y={projParams.annualExpenses}
                      stroke="#dc3545"
                      strokeDasharray="5 5"
                      label={{ value: `Expenses: ${formatCurrency(projParams.annualExpenses)}`, position: 'right', fill: '#dc3545' }}
                    />
                    <Area type="monotone" dataKey="withdrawalCapacity4" stroke="#28a745" fill="#28a745" fillOpacity={0.15} name="withdrawalCapacity4" />
                    <Area type="monotone" dataKey="withdrawalCapacity3_5" stroke="#ffc107" fill="#ffc107" fillOpacity={0.15} name="withdrawalCapacity3_5" />
                    <Area type="monotone" dataKey="withdrawalCapacity3" stroke="#dc3545" fill="#dc3545" fillOpacity={0.1} name="withdrawalCapacity3" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Monte Carlo Simulation (C7) */}
              <div style={{ marginBottom: '2rem' }}>
                <h3 style={styles.subsectionTitle}>Monte Carlo Simulation</h3>
                <p style={styles.helpText}>
                  {monteCarloResults.simulations} simulations using historical market volatility (16% std dev).
                  Success = portfolio reaches FIRE number within 30 years.
                </p>
                <ResponsiveContainer width="100%" height={350}>
                  <AreaChart data={monteCarloResults.percentileData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="age" label={{ value: 'Age', position: 'insideBottom', offset: -5 }} />
                    <YAxis tickFormatter={v => v >= 1000000 ? `$${(v / 1000000).toFixed(1)}M` : `$${(v / 1000).toFixed(0)}k`} />
                    <Tooltip
                      formatter={(value, name) => {
                        const labels = { p10: '10th %ile', p25: '25th %ile', p50: 'Median', p75: '75th %ile', p90: '90th %ile' };
                        return [formatCurrency(value), labels[name] || name];
                      }}
                      labelFormatter={l => `Age ${l}`}
                    />
                    <Legend />
                    <ReferenceLine
                      y={fireMetrics.fireNumber}
                      stroke="#dc3545"
                      strokeDasharray="5 5"
                      label={{ value: 'FIRE Number', position: 'right', fill: '#dc3545' }}
                    />
                    <Area type="monotone" dataKey="p90" stroke="#28a745" fill="#28a745" fillOpacity={0.08} name="p90" />
                    <Area type="monotone" dataKey="p75" stroke="#28a745" fill="#28a745" fillOpacity={0.12} name="p75" />
                    <Area type="monotone" dataKey="p50" stroke="#007bff" fill="#007bff" fillOpacity={0.15} name="p50" strokeWidth={2} />
                    <Area type="monotone" dataKey="p25" stroke="#ffc107" fill="#ffc107" fillOpacity={0.1} name="p25" />
                    <Area type="monotone" dataKey="p10" stroke="#dc3545" fill="#dc3545" fillOpacity={0.08} name="p10" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Tax-Aware Note (C8) */}
              <div style={{ marginBottom: '2rem', backgroundColor: '#fff3cd', border: '1px solid #ffc107', borderRadius: '8px', padding: '1rem 1.25rem' }}>
                <strong style={{ color: '#856404' }}>Tax Considerations</strong>
                <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9rem', color: '#856404', lineHeight: '1.5' }}>
                  Different account types have different tax treatment on withdrawal:
                  <strong> 401(k)/IRA</strong> withdrawals are taxed as ordinary income.
                  <strong> Roth IRA/Roth 401(k)</strong> withdrawals are tax-free (after age 59.5).
                  <strong> Brokerage</strong> gains are taxed at capital gains rates.
                  <strong> HSA</strong> withdrawals for medical expenses are tax-free.
                  Your actual withdrawal capacity may be 15-30% lower than shown after accounting for taxes on pre-tax accounts.
                </p>
              </div>

              {/* Scenario Comparison */}
              <div>
                <div style={styles.sectionHeader}>
                  <h3 style={styles.subsectionTitle}>Scenario Comparison</h3>
                  <button style={styles.primaryButton} onClick={addScenario}>+ Add Scenario</button>
                </div>
                <div style={styles.tableContainer}>
                  <table style={styles.table}>
                    <thead>
                      <tr>
                        <th style={styles.th}>Growth Rate (%)</th>
                        <th style={styles.th}>SWR (%)</th>
                        <th style={styles.th}>Annual Expenses ($)</th>
                        <th style={{ ...styles.th, textAlign: 'right' }}>FIRE Number</th>
                        <th style={{ ...styles.th, textAlign: 'right' }}>Gap</th>
                        <th style={{ ...styles.th, textAlign: 'right' }}>Years to FIRE</th>
                        <th style={{ ...styles.th, textAlign: 'right' }}>FIRE Age</th>
                        <th style={styles.th}></th>
                      </tr>
                    </thead>
                    <tbody>
                      {scenarioResults.map(s => (
                        <tr key={s.id}>
                          <td style={styles.td}>
                            <input
                              style={styles.inputSmall}
                              type="number"
                              step="0.5"
                              value={s.growthRate}
                              onChange={e => updateScenario(s.id, 'growthRate', e.target.value)}
                            />
                          </td>
                          <td style={styles.td}>
                            <input
                              style={styles.inputSmall}
                              type="number"
                              step="0.25"
                              value={s.swr}
                              onChange={e => updateScenario(s.id, 'swr', e.target.value)}
                            />
                          </td>
                          <td style={styles.td}>
                            <input
                              style={styles.inputSmall}
                              type="number"
                              step="1000"
                              value={s.annualExpenses}
                              onChange={e => updateScenario(s.id, 'annualExpenses', e.target.value)}
                            />
                          </td>
                          <td style={{ ...styles.td, textAlign: 'right', fontWeight: 'bold' }}>
                            {formatCurrency(s.fireNumber)}
                          </td>
                          <td style={{
                            ...styles.td,
                            textAlign: 'right',
                            color: s.gap <= 0 ? '#28a745' : '#333',
                          }}>
                            {s.gap <= 0 ? 'Achieved!' : formatCurrency(s.gap)}
                          </td>
                          <td style={{ ...styles.td, textAlign: 'right', fontWeight: 'bold' }}>
                            {s.yearsToFire !== null ? (s.yearsToFire === 0 ? 'Now' : s.yearsToFire) : '100+'}
                          </td>
                          <td style={{ ...styles.td, textAlign: 'right' }}>
                            {s.fireAge !== null ? s.fireAge : '-'}
                          </td>
                          <td style={styles.td}>
                            <button style={styles.iconBtn} onClick={() => removeScenario(s.id)} title="Remove">
                              🗑️
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ============ TAB 4: DOCUMENTATION ============ */}
          {activeTab === 'docs' && (
            <div style={styles.docsContainer}>
              <h2 style={styles.sectionTitle}>FIRE Tracker Documentation</h2>

              <div style={styles.docsSection}>
                <h3 style={styles.docsH3}>Overview</h3>
                <p style={styles.docsP}>
                  The FIRE (Financial Independence, Retire Early) Journey Tracker is a tool for monitoring your investment
                  portfolio, tracking investment income over time, and projecting when you can reach financial independence.
                  It has three functional tabs:
                </p>
                <ul style={styles.docsUl}>
                  <li><strong>Accounts &amp; Balances</strong> — manage your investment accounts and record periodic balance snapshots.</li>
                  <li><strong>Investment Income</strong> — see how much your money is growing on its own (separate from contributions).</li>
                  <li><strong>FIRE Projections</strong> — simulate different growth rates, withdrawal rates, and expense levels to estimate your FIRE date.</li>
                </ul>
              </div>

              <div style={styles.docsSection}>
                <h3 style={styles.docsH3}>Data Model</h3>
                <p style={styles.docsP}>
                  The tracker stores two types of historical data:
                </p>
                <div style={styles.docsSubsection}>
                  <h4 style={styles.docsH4}>Per-Account Snapshots</h4>
                  <p style={styles.docsP}>
                    Each investment account (401k, IRA, brokerage, etc.) can have balance snapshots recorded at different dates.
                    When you import from Monarch or add a snapshot manually, a record is created linking the account, date, balance,
                    and optional contribution amount. Having per-account data lets you filter the Investment Income chart to
                    see performance for specific accounts.
                  </p>
                </div>
                <div style={styles.docsSubsection}>
                  <h4 style={styles.docsH4}>Aggregate Portfolio Snapshots</h4>
                  <p style={styles.docsP}>
                    For historical dates where you don't have a per-account breakdown (e.g., an old Monarch &ldquo;all time&rdquo;
                    header showing a total), you can record a single total portfolio value for that date. These are used in the
                    Investment Income chart when viewing all accounts (unfiltered) and provide the historical baseline for the
                    growth trend line.
                  </p>
                </div>
              </div>

              <div style={styles.docsSection}>
                <h3 style={styles.docsH3}>Importing Data from Monarch Money</h3>
                <p style={styles.docsP}>
                  Monarch Money is used as the source of truth for account balances. There are two import workflows:
                </p>

                <div style={styles.docsSubsection}>
                  <h4 style={styles.docsH4}>1. Bulk Import (Per-Account Breakdown)</h4>
                  <p style={styles.docsP}>Steps:</p>
                  <ol style={styles.docsOl}>
                    <li>In Monarch, go to <strong>Investments</strong> and select the time period you want (e.g., &ldquo;1 month&rdquo;, &ldquo;3 months&rdquo;).</li>
                    <li>Select all the account text — account names, types, owners, and balances.</li>
                    <li>Copy the text to your clipboard.</li>
                    <li>In this app, go to <strong>Accounts &amp; Balances</strong> → click <strong>Bulk Import from Monarch</strong>.</li>
                    <li>Set the <strong>Snapshot Date</strong> to the date the balances represent (this is important for historical imports — use the end date of the Monarch period, not today&rsquo;s date).</li>
                    <li>Paste the text and click <strong>Import</strong>.</li>
                  </ol>
                  <p style={styles.docsP}>
                    The parser extracts account names, types, owners, and balances from the pasted text.
                    Existing accounts (matched by name) are updated; new accounts are created automatically.
                    A snapshot is recorded for each account at the specified date.
                  </p>
                  <div style={styles.docsTip}>
                    <strong>Tip:</strong> Import multiple Monarch time periods with different snapshot dates to build up historical
                    per-account data. For example, import &ldquo;1 month&rdquo; with today&rsquo;s date, then &ldquo;3 months&rdquo;
                    with the date from 3 months ago. The more dates you have, the more accurate the investment income calculations.
                  </div>
                </div>

                <div style={styles.docsSubsection}>
                  <h4 style={styles.docsH4}>2. Historical Portfolio Totals (Aggregate Snapshots)</h4>
                  <p style={styles.docsP}>Steps:</p>
                  <ol style={styles.docsOl}>
                    <li>In Monarch, look at the &ldquo;All Time&rdquo; or other historical view and note the total portfolio value and date.</li>
                    <li>In this app, go to <strong>Accounts &amp; Balances</strong> → scroll to <strong>Historical Portfolio Totals</strong>.</li>
                    <li>Enter the date and total value, then click <strong>Add Snapshot</strong>.</li>
                  </ol>
                  <p style={styles.docsP}>
                    Use this for older dates where you don&rsquo;t have a per-account breakdown. These aggregate snapshots fill in the
                    historical timeline and are included in the Investment Income chart when viewing all accounts.
                  </p>
                </div>

                <div style={styles.docsSubsection}>
                  <h4 style={styles.docsH4}>Recommended Import Schedule</h4>
                  <ul style={styles.docsUl}>
                    <li><strong>Monthly or quarterly:</strong> Do a bulk import from Monarch with the current period&rsquo;s data to keep per-account snapshots up to date.</li>
                    <li><strong>One-time backfill:</strong> Add aggregate portfolio totals from Monarch&rsquo;s &ldquo;All Time&rdquo; chart for key historical dates (e.g., year-ends, quarter-ends).</li>
                  </ul>
                </div>
              </div>

              <div style={styles.docsSection}>
                <h3 style={styles.docsH3}>Investment Income — How It Works</h3>
                <p style={styles.docsP}>
                  The Investment Income tab calculates how much of your portfolio growth came from market
                  returns versus new money you contributed. The core formula for each period is:
                </p>
                <div style={styles.docsFormula}>
                  Investment Income = Ending Balance − Starting Balance − Contributions
                </div>
                <p style={styles.docsP}>
                  This isolates the return generated by the market (dividends, capital appreciation, interest)
                  from the money you added during that period.
                </p>

                <div style={styles.docsSubsection}>
                  <h4 style={styles.docsH4}>Calendar Intervals &amp; Interpolation</h4>
                  <p style={styles.docsP}>
                    Snapshots rarely land exactly on calendar boundaries, so the system uses <strong>linear interpolation</strong> to
                    estimate portfolio values at standard period boundaries (month-end, quarter-end, or year-end).
                    For example, if you have snapshots on Jan 15 and Apr 20, the system interpolates to estimate values
                    at Mar 31 (quarter-end). Contributions recorded in snapshots are pro-rated to the periods they fall within.
                  </p>
                  <p style={styles.docsP}>
                    You can toggle between <strong>Monthly</strong>, <strong>Quarterly</strong> (default), and <strong>Yearly</strong> intervals
                    using the buttons at the top of the tab.
                  </p>
                </div>

                <div style={styles.docsSubsection}>
                  <h4 style={styles.docsH4}>Account Filtering</h4>
                  <p style={styles.docsP}>
                    The &ldquo;All Accounts&rdquo; filter button lets you select specific accounts to analyze.
                    When filtering, only per-account snapshot data is used (aggregate portfolio totals are excluded
                    since they represent the entire portfolio and can&rsquo;t be split by account).
                    You need at least two per-account snapshot dates for filtered views to show data.
                  </p>
                </div>

                <div style={styles.docsSubsection}>
                  <h4 style={styles.docsH4}>The Chart</h4>
                  <p style={styles.docsP}>
                    The &ldquo;Portfolio Growth Over Time&rdquo; chart uses a dual Y-axis:
                  </p>
                  <ul style={styles.docsUl}>
                    <li><strong>Left axis (bars):</strong> Investment Income (green) and Contributions (blue) per period. These are the incremental amounts.</li>
                    <li><strong>Right axis (line):</strong> Ending Balance trend — the total portfolio value over time.</li>
                  </ul>
                  <p style={styles.docsP}>
                    The dual axis prevents the large portfolio balance from squishing the smaller income/contribution bars.
                  </p>
                </div>
              </div>

              <div style={styles.docsSection}>
                <h3 style={styles.docsH3}>FIRE Projections — How It Works</h3>

                <div style={styles.docsSubsection}>
                  <h4 style={styles.docsH4}>FIRE Number</h4>
                  <p style={styles.docsP}>
                    Your FIRE number is the portfolio size needed to sustain your annual expenses indefinitely,
                    based on the Safe Withdrawal Rate (SWR):
                  </p>
                  <div style={styles.docsFormula}>
                    FIRE Number = Annual Expenses ÷ (SWR / 100)
                  </div>
                  <p style={styles.docsP}>
                    For example, with $100,000/year expenses and a 4% SWR, your FIRE number is $2,500,000.
                    A 3.5% SWR is more conservative and yields a higher target ($2,857,143).
                  </p>
                </div>

                <div style={styles.docsSubsection}>
                  <h4 style={styles.docsH4}>Safe Withdrawal Rate (SWR)</h4>
                  <p style={styles.docsP}>
                    The SWR is the percentage of your portfolio you can withdraw annually with a high probability of not
                    running out of money over a 30+ year retirement. The commonly cited 4% rule comes from the Trinity Study.
                    Lower SWR = more conservative = larger portfolio needed but higher safety margin.
                  </p>
                </div>

                <div style={styles.docsSubsection}>
                  <h4 style={styles.docsH4}>Growth Projection</h4>
                  <p style={styles.docsP}>
                    The projection uses compound growth with annual contributions:
                  </p>
                  <div style={styles.docsFormula}>
                    Year N Balance = Year (N-1) Balance × (1 + Growth Rate) + Annual Contribution
                  </div>
                  <p style={styles.docsP}>
                    The &ldquo;Years to FIRE&rdquo; is the first year where the projected balance meets or exceeds the FIRE number.
                    Growth rate represents average annual market return (typically 6–8% for a diversified stock portfolio
                    before inflation, or 4–6% real/inflation-adjusted).
                  </p>
                </div>

                <div style={styles.docsSubsection}>
                  <h4 style={styles.docsH4}>Scenario Comparison</h4>
                  <p style={styles.docsP}>
                    The scenario table lets you compare different combinations of growth rate, SWR, and expense levels
                    side by side. This is useful for stress-testing your plan:
                  </p>
                  <ul style={styles.docsUl}>
                    <li><strong>Optimistic:</strong> 8% growth, 4% SWR, lower expenses</li>
                    <li><strong>Moderate:</strong> 7% growth, 4% SWR, target expenses</li>
                    <li><strong>Conservative:</strong> 6% growth, 3.5% SWR, higher expenses</li>
                  </ul>
                </div>
              </div>

              <div style={styles.docsSection}>
                <h3 style={styles.docsH3}>Key Terms</h3>
                <div style={styles.docsTermGrid}>
                  {[
                    ['FIRE', 'Financial Independence, Retire Early — the point where investment income covers living expenses.'],
                    ['SWR', 'Safe Withdrawal Rate — the annual percentage you can withdraw from your portfolio sustainably (commonly 3.5–4%).'],
                    ['FIRE Number', 'Annual Expenses ÷ SWR — the total portfolio value needed for financial independence.'],
                    ['Investment Income', 'Portfolio growth minus contributions — the return generated by the market on your existing investments.'],
                    ['Contributions', 'New money added to investment accounts during a period (401k contributions, IRA deposits, etc.).'],
                    ['Linear Interpolation', 'A method used to estimate portfolio values between known snapshot dates by assuming steady growth between points.'],
                    ['Aggregate Snapshot', 'A total portfolio value recorded for a date without per-account breakdown. Used for historical backfill.'],
                  ].map(([term, def]) => (
                    <div key={term} style={styles.docsTerm}>
                      <dt style={styles.docsTermDt}>{term}</dt>
                      <dd style={styles.docsTermDd}>{def}</dd>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1rem 2rem',
    backgroundColor: 'white',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
  },
  homeButton: {
    background: 'none',
    border: 'none',
    fontSize: '1.5rem',
    cursor: 'pointer',
    padding: '0.25rem',
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
    fontSize: '0.9rem',
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
    maxWidth: '1200px',
    margin: '2rem auto',
    padding: '0 1rem',
  },
  tabs: {
    display: 'flex',
    gap: '0',
    marginBottom: '1.5rem',
    borderBottom: '2px solid #ddd',
    overflowX: 'auto',
  },
  tab: {
    padding: '0.75rem 1.5rem',
    background: 'none',
    border: 'none',
    borderBottom: '3px solid transparent',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '500',
    color: '#666',
    transition: 'all 0.2s',
    whiteSpace: 'nowrap',
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
  metricSub: {
    fontSize: '0.85rem',
    color: '#888',
    marginTop: '0.25rem',
  },
  actionBar: {
    display: 'flex',
    gap: '0.75rem',
    marginBottom: '1.5rem',
    flexWrap: 'wrap',
  },
  primaryButton: {
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
  formCard: {
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '1.5rem',
    marginBottom: '1.5rem',
    backgroundColor: '#fafafa',
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
    fontSize: '0.9rem',
  },
  input: {
    width: '100%',
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
    boxSizing: 'border-box',
  },
  inputSmall: {
    width: '100%',
    padding: '0.35rem 0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '0.9rem',
    boxSizing: 'border-box',
  },
  textarea: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
    width: '100%',
    fontFamily: 'monospace',
    boxSizing: 'border-box',
  },
  helpText: {
    color: '#666',
    fontSize: '0.9rem',
    marginBottom: '1rem',
  },
  successBox: {
    marginTop: '1rem',
    padding: '1rem',
    backgroundColor: '#d4edda',
    border: '1px solid #c3e6cb',
    borderRadius: '4px',
    color: '#155724',
  },
  errorBox: {
    marginBottom: '1rem',
    padding: '0.75rem 1rem',
    backgroundColor: '#f8d7da',
    border: '1px solid #f5c6cb',
    borderRadius: '4px',
    color: '#721c24',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  dismissBtn: {
    background: 'none',
    border: 'none',
    color: '#721c24',
    cursor: 'pointer',
    fontSize: '1.1rem',
    fontWeight: 'bold',
    padding: '0 0.5rem',
  },
  emptyState: {
    textAlign: 'center',
    padding: '3rem 1rem',
    color: '#666',
  },
  ownerGroup: {
    marginBottom: '2rem',
  },
  ownerTitle: {
    fontSize: '1.1rem',
    color: '#333',
    marginBottom: '0.75rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  ownerTotal: {
    fontWeight: 'bold',
    color: '#007bff',
  },
  tableContainer: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    textAlign: 'left',
    padding: '0.75rem',
    borderBottom: '2px solid #dee2e6',
    color: '#333',
    fontWeight: '600',
    fontSize: '0.9rem',
    whiteSpace: 'nowrap',
  },
  td: {
    padding: '0.75rem',
    borderBottom: '1px solid #eee',
    fontSize: '0.9rem',
  },
  badge: {
    display: 'inline-block',
    padding: '0.2rem 0.6rem',
    backgroundColor: '#e9ecef',
    borderRadius: '12px',
    fontSize: '0.8rem',
    color: '#495057',
  },
  iconBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '1rem',
    padding: '0.15rem 0.35rem',
  },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modal: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '2rem',
    width: '90%',
    maxWidth: '700px',
    maxHeight: '80vh',
    overflowY: 'auto',
    boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
  },
  snapshotTable: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
    marginBottom: '1rem',
  },
  snapshotHeader: {
    display: 'flex',
    gap: '1rem',
    fontWeight: 'bold',
    fontSize: '0.9rem',
    padding: '0.5rem 0',
    borderBottom: '1px solid #ddd',
  },
  snapshotRow: {
    display: 'flex',
    gap: '1rem',
    alignItems: 'center',
    padding: '0.5rem 0',
    borderBottom: '1px solid #f0f0f0',
  },
  snapshotsPanel: {
    backgroundColor: '#f0f4f8',
    padding: '1rem 1.5rem',
    borderTop: '1px solid #dee2e6',
    borderBottom: '2px solid #dee2e6',
  },
  snapshotsPanelHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.75rem',
  },
  thSm: {
    textAlign: 'left',
    padding: '0.5rem',
    borderBottom: '1px solid #ccc',
    fontWeight: '600',
    fontSize: '0.85rem',
    whiteSpace: 'nowrap',
  },
  tdSm: {
    padding: '0.5rem',
    borderBottom: '1px solid #e0e0e0',
    fontSize: '0.85rem',
  },
  intervalToggle: {
    display: 'flex',
    gap: '0',
    border: '1px solid #ddd',
    borderRadius: '6px',
    overflow: 'hidden',
  },
  intervalBtn: {
    padding: '0.4rem 1rem',
    border: 'none',
    backgroundColor: 'white',
    cursor: 'pointer',
    fontSize: '0.85rem',
    fontWeight: '500',
    color: '#666',
    borderRight: '1px solid #ddd',
    transition: 'all 0.15s',
  },
  intervalBtnActive: {
    backgroundColor: '#007bff',
    color: 'white',
  },
  filterContainer: {
    position: 'relative',
    display: 'inline-block',
  },
  filterBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.4rem',
    padding: '0.4rem 1rem',
    border: '1px solid #ddd',
    borderRadius: '6px',
    backgroundColor: 'white',
    cursor: 'pointer',
    fontSize: '0.85rem',
    fontWeight: '500',
    color: '#666',
    transition: 'all 0.15s',
  },
  filterBtnActive: {
    borderColor: '#007bff',
    color: '#007bff',
  },
  filterDropdown: {
    position: 'absolute',
    top: '100%',
    right: 0,
    marginTop: '0.4rem',
    backgroundColor: 'white',
    border: '1px solid #ddd',
    borderRadius: '8px',
    boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
    zIndex: 100,
    minWidth: '320px',
    maxHeight: '400px',
    display: 'flex',
    flexDirection: 'column',
  },
  filterHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.6rem 0.8rem',
    borderBottom: '1px solid #eee',
  },
  filterHeaderLabel: {
    fontSize: '0.8rem',
    fontWeight: '600',
    color: '#333',
  },
  filterActions: {
    display: 'flex',
    gap: '0.5rem',
  },
  filterActionBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '0.78rem',
    fontWeight: '500',
    color: '#007bff',
    padding: '0',
  },
  filterList: {
    overflowY: 'auto',
    padding: '0.4rem 0',
    flex: 1,
  },
  filterItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '0.4rem 0.8rem',
    cursor: 'pointer',
    fontSize: '0.82rem',
    color: '#333',
    transition: 'background 0.1s',
  },
  filterCheckbox: {
    width: '16px',
    height: '16px',
    cursor: 'pointer',
    accentColor: '#007bff',
  },
  docsContainer: {
    maxWidth: '800px',
    lineHeight: '1.7',
    color: '#333',
  },
  docsSection: {
    marginBottom: '2rem',
    paddingBottom: '1.5rem',
    borderBottom: '1px solid #eee',
  },
  docsSubsection: {
    marginTop: '1rem',
    marginLeft: '0.5rem',
  },
  docsH3: {
    fontSize: '1.2rem',
    fontWeight: '700',
    color: '#1a1a1a',
    margin: '0 0 0.6rem 0',
  },
  docsH4: {
    fontSize: '1rem',
    fontWeight: '600',
    color: '#333',
    margin: '0.8rem 0 0.4rem 0',
  },
  docsP: {
    margin: '0.4rem 0',
    fontSize: '0.92rem',
  },
  docsUl: {
    margin: '0.4rem 0',
    paddingLeft: '1.5rem',
    fontSize: '0.92rem',
  },
  docsOl: {
    margin: '0.4rem 0',
    paddingLeft: '1.5rem',
    fontSize: '0.92rem',
  },
  docsFormula: {
    fontFamily: 'monospace',
    backgroundColor: '#f4f6f9',
    border: '1px solid #e0e4ea',
    borderRadius: '6px',
    padding: '0.7rem 1rem',
    margin: '0.6rem 0',
    fontSize: '0.9rem',
    fontWeight: '600',
    color: '#1a1a1a',
  },
  docsTip: {
    backgroundColor: '#e8f4fd',
    border: '1px solid #b8daff',
    borderRadius: '6px',
    padding: '0.7rem 1rem',
    margin: '0.8rem 0',
    fontSize: '0.85rem',
    color: '#004085',
  },
  docsTermGrid: {
    display: 'grid',
    gap: '0.6rem',
    marginTop: '0.5rem',
  },
  docsTerm: {
    backgroundColor: '#f8f9fa',
    borderRadius: '6px',
    padding: '0.7rem 1rem',
  },
  docsTermDt: {
    fontWeight: '700',
    fontSize: '0.9rem',
    color: '#007bff',
    marginBottom: '0.15rem',
  },
  docsTermDd: {
    margin: 0,
    fontSize: '0.88rem',
    color: '#555',
  },
};
