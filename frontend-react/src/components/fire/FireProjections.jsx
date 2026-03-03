import React from 'react';
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
} from 'recharts';
import { formatCurrency } from '../../utils/formatters';

export default function FireProjections({
  projParams,
  setProjParams,
  fireMetrics,
  projectionData,
  monteCarloResults,
  scenarios,
  scenarioResults,
  addScenario,
  removeScenario,
  updateScenario,
  loading,
  handleSyncFromPortfolio,
  styles,
}) {
  return (
    <div>
      <h2 style={styles.sectionTitle}>FIRE Projections</h2>

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
            <input style={styles.input} type="number" value={projParams.currentValue}
              onChange={e => setProjParams({ ...projParams, currentValue: parseFloat(e.target.value) || 0 })} />
          </div>
          <div>
            <label style={styles.label}>Annual Contributions ($)</label>
            <input style={styles.input} type="number" value={projParams.annualContribution}
              onChange={e => setProjParams({ ...projParams, annualContribution: parseFloat(e.target.value) || 0 })} />
          </div>
          <div>
            <label style={styles.label}>Expected Annual Return (%)</label>
            <input style={styles.input} type="number" step="0.1" min="0" max="30" value={projParams.growthRate}
              onChange={e => setProjParams({ ...projParams, growthRate: parseFloat(e.target.value) || 0 })} />
            <input type="range" min="0" max="15" step="0.5" value={projParams.growthRate}
              onChange={e => setProjParams({ ...projParams, growthRate: parseFloat(e.target.value) })}
              style={{ width: '100%', marginTop: '0.25rem' }} />
          </div>
          <div>
            <label style={styles.label}>Inflation Rate (%)</label>
            <input style={styles.input} type="number" step="0.1" min="0" max="15" value={projParams.inflationRate}
              onChange={e => setProjParams({ ...projParams, inflationRate: parseFloat(e.target.value) || 0 })} />
            <input type="range" min="0" max="8" step="0.5" value={projParams.inflationRate}
              onChange={e => setProjParams({ ...projParams, inflationRate: parseFloat(e.target.value) })}
              style={{ width: '100%', marginTop: '0.25rem' }} />
          </div>
          <div>
            <label style={styles.label}>Annual Expenses in Retirement ($)</label>
            <input style={styles.input} type="number" value={projParams.annualExpenses}
              onChange={e => setProjParams({ ...projParams, annualExpenses: parseFloat(e.target.value) || 0 })} />
          </div>
          <div>
            <label style={styles.label}>Safe Withdrawal Rate (%)</label>
            <input style={styles.input} type="number" step="0.1" min="1" max="10" value={projParams.swr}
              onChange={e => setProjParams({ ...projParams, swr: parseFloat(e.target.value) || 4 })} />
            <input type="range" min="2" max="6" step="0.25" value={projParams.swr}
              onChange={e => setProjParams({ ...projParams, swr: parseFloat(e.target.value) })}
              style={{ width: '100%', marginTop: '0.25rem' }} />
          </div>
          <div>
            <label style={styles.label}>Current Age</label>
            <input style={styles.input} type="number" value={projParams.currentAge}
              onChange={e => setProjParams({ ...projParams, currentAge: parseInt(e.target.value) || 30 })} />
          </div>
          <div>
            <label style={styles.label}>Target Retirement Age</label>
            <input style={styles.input} type="number" value={projParams.targetAge}
              onChange={e => setProjParams({ ...projParams, targetAge: parseInt(e.target.value) || 65 })} />
          </div>
        </div>
      </div>

      {/* FIRE Progress Bar */}
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

      {/* Metrics */}
      <div style={styles.metricsGrid}>
        <div style={{ ...styles.metricCard, borderLeft: '4px solid #007bff' }}>
          <div style={styles.metricLabel}>FIRE Number</div>
          <div style={styles.metricValue}>{formatCurrency(fireMetrics.fireNumber)}</div>
          <div style={styles.metricSub}>{formatCurrency(projParams.annualExpenses)}/yr at {projParams.swr}% SWR</div>
        </div>
        <div style={{ ...styles.metricCard, borderLeft: '4px solid #ffc107' }}>
          <div style={styles.metricLabel}>Gap to FIRE</div>
          <div style={{ ...styles.metricValue, color: fireMetrics.gap <= 0 ? '#28a745' : '#333' }}>
            {fireMetrics.gap <= 0 ? 'FIRE Achieved!' : formatCurrency(fireMetrics.gap)}
          </div>
        </div>
        <div style={{ ...styles.metricCard, borderLeft: '4px solid #28a745' }}>
          <div style={styles.metricLabel}>Years to FIRE</div>
          <div style={styles.metricValue}>
            {fireMetrics.yearsToFire !== null
              ? fireMetrics.yearsToFire === 0 ? 'Now!' : `${fireMetrics.yearsToFire} years`
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

      {/* Milestones */}
      <div style={{ ...styles.metricsGrid, marginBottom: '2rem' }}>
        <div style={{ ...styles.metricCard, borderLeft: `4px solid ${fireMetrics.coastFireReached ? '#28a745' : '#6c757d'}` }}>
          <div style={styles.metricLabel}>Coast FIRE</div>
          <div style={styles.metricValue}>
            {fireMetrics.coastFireReached ? 'Reached!' : formatCurrency(fireMetrics.coastFireNumber)}
          </div>
          <div style={styles.metricSub}>No contributions needed by age {projParams.targetAge}</div>
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
            <XAxis dataKey="age" label={{ value: 'Age', position: 'insideBottom', offset: -5 }} />
            <YAxis tickFormatter={v => v >= 1000000 ? `$${(v / 1000000).toFixed(1)}M` : `$${(v / 1000).toFixed(0)}k`} />
            <Tooltip
              formatter={(value, name) => {
                const labels = { portfolio: 'Portfolio (Nominal)', portfolioReal: 'Portfolio (Inflation-Adjusted)', investmentIncome: 'Annual Investment Income' };
                return [formatCurrency(value), labels[name] || name];
              }}
              labelFormatter={l => `Age ${l}`}
            />
            <Legend />
            <ReferenceLine y={fireMetrics.fireNumber} stroke="#dc3545" strokeDasharray="5 5"
              label={{ value: `FIRE: ${formatCurrency(fireMetrics.fireNumber)}`, position: 'right', fill: '#dc3545' }} />
            <ReferenceLine x={projParams.targetAge} stroke="#6f42c1" strokeDasharray="4 4"
              label={{ value: `Target: ${projParams.targetAge}`, position: 'top', fill: '#6f42c1' }} />
            <Area type="monotone" dataKey="portfolio" stroke="#007bff" fill="#007bff" fillOpacity={0.1} name="portfolio" />
            {projParams.inflationRate > 0 && (
              <Area type="monotone" dataKey="portfolioReal" stroke="#fd7e14" fill="#fd7e14" fillOpacity={0.05}
                strokeDasharray="5 5" name="portfolioReal" />
            )}
            <Area type="monotone" dataKey="investmentIncome" stroke="#28a745" fill="#28a745" fillOpacity={0.1} name="investmentIncome" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Withdrawal Capacity */}
      <div style={{ marginBottom: '2rem' }}>
        <h3 style={styles.subsectionTitle}>Annual Withdrawal Capacity Over Time</h3>
        <ResponsiveContainer width="100%" height={350}>
          <AreaChart data={projectionData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="age" label={{ value: 'Age', position: 'insideBottom', offset: -5 }} />
            <YAxis tickFormatter={v => v >= 1000000 ? `$${(v / 1000000).toFixed(1)}M` : `$${(v / 1000).toFixed(0)}k`} />
            <Tooltip
              formatter={(value, name) => {
                const labels = { withdrawalCapacity4: '4% SWR', withdrawalCapacity3_5: '3.5% SWR', withdrawalCapacity3: '3% SWR' };
                return [formatCurrency(value), labels[name] || name];
              }}
              labelFormatter={l => `Age ${l}`}
            />
            <Legend />
            <ReferenceLine y={projParams.annualExpenses} stroke="#dc3545" strokeDasharray="5 5"
              label={{ value: `Expenses: ${formatCurrency(projParams.annualExpenses)}`, position: 'right', fill: '#dc3545' }} />
            <Area type="monotone" dataKey="withdrawalCapacity4" stroke="#28a745" fill="#28a745" fillOpacity={0.15} name="withdrawalCapacity4" />
            <Area type="monotone" dataKey="withdrawalCapacity3_5" stroke="#ffc107" fill="#ffc107" fillOpacity={0.15} name="withdrawalCapacity3_5" />
            <Area type="monotone" dataKey="withdrawalCapacity3" stroke="#dc3545" fill="#dc3545" fillOpacity={0.1} name="withdrawalCapacity3" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Monte Carlo */}
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
            <ReferenceLine y={fireMetrics.fireNumber} stroke="#dc3545" strokeDasharray="5 5"
              label={{ value: 'FIRE Number', position: 'right', fill: '#dc3545' }} />
            <Area type="monotone" dataKey="p90" stroke="#28a745" fill="#28a745" fillOpacity={0.08} name="p90" />
            <Area type="monotone" dataKey="p75" stroke="#28a745" fill="#28a745" fillOpacity={0.12} name="p75" />
            <Area type="monotone" dataKey="p50" stroke="#007bff" fill="#007bff" fillOpacity={0.15} name="p50" strokeWidth={2} />
            <Area type="monotone" dataKey="p25" stroke="#ffc107" fill="#ffc107" fillOpacity={0.1} name="p25" />
            <Area type="monotone" dataKey="p10" stroke="#dc3545" fill="#dc3545" fillOpacity={0.08} name="p10" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Tax Note */}
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

      {/* Scenarios */}
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
                    <input style={styles.inputSmall} type="number" step="0.5" value={s.growthRate}
                      onChange={e => updateScenario(s.id, 'growthRate', e.target.value)} />
                  </td>
                  <td style={styles.td}>
                    <input style={styles.inputSmall} type="number" step="0.25" value={s.swr}
                      onChange={e => updateScenario(s.id, 'swr', e.target.value)} />
                  </td>
                  <td style={styles.td}>
                    <input style={styles.inputSmall} type="number" step="1000" value={s.annualExpenses}
                      onChange={e => updateScenario(s.id, 'annualExpenses', e.target.value)} />
                  </td>
                  <td style={{ ...styles.td, textAlign: 'right', fontWeight: 'bold' }}>{formatCurrency(s.fireNumber)}</td>
                  <td style={{ ...styles.td, textAlign: 'right', color: s.gap <= 0 ? '#28a745' : '#333' }}>
                    {s.gap <= 0 ? 'Achieved!' : formatCurrency(s.gap)}
                  </td>
                  <td style={{ ...styles.td, textAlign: 'right', fontWeight: 'bold' }}>
                    {s.yearsToFire !== null ? (s.yearsToFire === 0 ? 'Now' : s.yearsToFire) : '100+'}
                  </td>
                  <td style={{ ...styles.td, textAlign: 'right' }}>{s.fireAge !== null ? s.fireAge : '-'}</td>
                  <td style={styles.td}>
                    <button style={styles.iconBtn} onClick={() => removeScenario(s.id)} title="Remove">🗑️</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
