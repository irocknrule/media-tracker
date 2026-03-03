import React, { useRef, useState, useEffect } from 'react';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { formatCurrency, formatPercent } from '../../utils/formatters';

export default function FireIncome({
  incomeHistory,
  incomeInterval,
  setIncomeInterval,
  accounts,
  selectedAccountIds,
  setSelectedAccountIds,
  styles,
}) {
  const filterRef = useRef(null);
  const [showAccountFilter, setShowAccountFilter] = useState(false);

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

  return (
    <div>
      <div style={styles.sectionHeader}>
        <h2 style={styles.sectionTitle}>Investment Income</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={styles.intervalToggle}>
            {['monthly', 'quarterly', 'yearly'].map(iv => (
              <button
                key={iv}
                style={{ ...styles.intervalBtn, ...(incomeInterval === iv ? styles.intervalBtnActive : {}) }}
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
                  ...(selectedAccountIds !== null && selectedAccountIds.length !== accounts.length ? styles.filterBtnActive : {}),
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
                      <button style={styles.filterActionBtn} onClick={() => setSelectedAccountIds(accounts.map(a => a.id))}>Select All</button>
                      <button style={styles.filterActionBtn} onClick={() => setSelectedAccountIds([])}>Deselect All</button>
                    </div>
                  </div>
                  <div style={styles.filterList}>
                    {accounts.map(acct => {
                      const ids = selectedAccountIds ?? accounts.map(a => a.id);
                      const checked = ids.includes(acct.id);
                      return (
                        <label key={acct.id} style={styles.filterItem}
                          onMouseEnter={e => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                          onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}>
                          <input type="checkbox" style={styles.filterCheckbox} checked={checked}
                            onChange={() => {
                              const current = selectedAccountIds ?? accounts.map(a => a.id);
                              setSelectedAccountIds(checked ? current.filter(id => id !== acct.id) : [...current, acct.id]);
                            }} />
                          <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{acct.name}</span>
                          {acct.latest_balance != null && (
                            <span style={{ color: '#888', fontSize: '0.78rem', flexShrink: 0 }}>{formatCurrency(acct.latest_balance)}</span>
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
          <p>No income history yet. You need at least two snapshots to calculate investment income.</p>
        </div>
      ) : (
        <>
          <div style={styles.metricsGrid}>
            <div style={styles.metricCard}>
              <div style={styles.metricLabel}>Total Investment Income</div>
              <div style={{ ...styles.metricValue, color: incomeHistory.total_investment_income >= 0 ? '#28a745' : '#dc3545' }}>
                {formatCurrency(incomeHistory.total_investment_income)}
              </div>
            </div>
            {incomeHistory.entries.length > 0 && (
              <div style={styles.metricCard}>
                <div style={styles.metricLabel}>Last Period Income</div>
                <div style={{ ...styles.metricValue, color: incomeHistory.entries[incomeHistory.entries.length - 1].investment_income >= 0 ? '#28a745' : '#dc3545' }}>
                  {formatCurrency(incomeHistory.entries[incomeHistory.entries.length - 1].investment_income)}
                </div>
                <div style={styles.metricSub}>
                  {formatPercent(incomeHistory.entries[incomeHistory.entries.length - 1].growth_rate_pct)}
                </div>
              </div>
            )}
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <h3 style={styles.subsectionTitle}>Portfolio Growth Over Time</h3>
            <ResponsiveContainer width="100%" height={400}>
              <ComposedChart data={incomeHistory.entries}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period_end" />
                <YAxis yAxisId="left" tickFormatter={v => v >= 1000000 ? `$${(v / 1000000).toFixed(1)}M` : `$${(v / 1000).toFixed(0)}k`} />
                <YAxis yAxisId="right" orientation="right" tickFormatter={v => v >= 1000000 ? `$${(v / 1000000).toFixed(1)}M` : `$${(v / 1000).toFixed(0)}k`} stroke="#999" />
                <Tooltip formatter={(value, name) => [formatCurrency(value), name]} labelFormatter={l => `Period ending: ${l}`} />
                <Legend />
                <Bar yAxisId="left" dataKey="investment_income" fill="#28a745" name="Investment Income" />
                <Line yAxisId="right" type="monotone" dataKey="ending_balance" stroke="#999" name="Ending Balance" dot={false} strokeWidth={2} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

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
                    <td style={{ ...styles.td, textAlign: 'right', fontWeight: 'bold', color: entry.investment_income >= 0 ? '#28a745' : '#dc3545' }}>
                      {formatCurrency(entry.investment_income)}
                    </td>
                    <td style={{ ...styles.td, textAlign: 'right', color: entry.growth_rate_pct >= 0 ? '#28a745' : '#dc3545' }}>
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
  );
}
