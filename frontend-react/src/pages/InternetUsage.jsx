import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { internetUsageService } from '../services/internetUsageService';
import { getErrorMessage } from '../utils/errorHandler';
import ConfirmModal from '../components/ConfirmModal';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

const MONTH_NAMES = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

function formatUsageFromGb(gb) {
  if (gb == null || Number.isNaN(gb)) return '—';
  if (gb >= 1000) return `${(gb / 1000).toFixed(2)} TB`;
  if (gb >= 1) return `${gb.toFixed(1)} GB`;
  return `${(gb * 1000).toFixed(0)} MB`;
}

function gbToFormFields(totalGb) {
  if (totalGb >= 1000) {
    return { amount: String((totalGb / 1000).toFixed(totalGb % 1000 === 0 ? 1 : 2)), unit: 'tb' };
  }
  return { amount: String(Math.round(totalGb * 10) / 10), unit: 'gb' };
}

export default function InternetUsage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [parseLoading, setParseLoading] = useState(false);
  const [ocrPreview, setOcrPreview] = useState('');
  const [parseNote, setParseNote] = useState('');
  const [confirmModal, setConfirmModal] = useState(null);

  const [entrySource, setEntrySource] = useState('manual');
  const [form, setForm] = useState({
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    totalAmount: '',
    totalUnit: 'tb',
    downloadGb: '',
    uploadGb: '',
    notes: '',
  });

  const loadRows = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await internetUsageService.list();
      setRows(data || []);
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to load usage');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRows();
  }, [loadRows]);

  const chartData = useMemo(() => {
    return [...rows]
      .sort((a, b) => a.year - b.year || a.month - b.month)
      .map((r) => ({
        label: `${r.year}-${String(r.month).padStart(2, '0')}`,
        totalTb: r.total_gb / 1000,
        totalGb: r.total_gb,
      }));
  }, [rows]);

  const applyParseResult = (data) => {
    setOcrPreview(data.ocr_text_preview || '');
    setParseNote(data.parse_note || '');
    if (data.suggested_year != null) {
      setForm((f) => ({ ...f, year: data.suggested_year }));
    }
    if (data.suggested_month != null) {
      setForm((f) => ({ ...f, month: data.suggested_month }));
    }
    if (data.suggested_total_gb != null) {
      const { amount, unit } = gbToFormFields(data.suggested_total_gb);
      setForm((f) => ({ ...f, totalAmount: amount, totalUnit: unit }));
    }
    setEntrySource('eero_snapshot');
    setSuccess('Parsed screenshot — review numbers, then save.');
  };

  const onFileSelected = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    try {
      setParseLoading(true);
      setError('');
      setSuccess('');
      const data = await internetUsageService.parseEeroScreenshot(file);
      applyParseResult(data);
    } catch (err) {
      setError(getErrorMessage(err) || 'Could not parse image');
    } finally {
      setParseLoading(false);
    }
  };

  const totalGbFromForm = () => {
    const n = parseFloat(form.totalAmount);
    if (Number.isNaN(n) || n <= 0) return null;
    return form.totalUnit === 'tb' ? n * 1000 : n;
  };

  const handleSave = async (e) => {
    e.preventDefault();
    const totalGb = totalGbFromForm();
    if (totalGb == null) {
      setError('Enter a positive total (TB or GB).');
      return;
    }
    const downloadGb =
      form.downloadGb === '' ? null : parseFloat(form.downloadGb);
    const uploadGb = form.uploadGb === '' ? null : parseFloat(form.uploadGb);
    if (downloadGb != null && (Number.isNaN(downloadGb) || downloadGb < 0)) {
      setError('Download must be a non-negative number or empty.');
      return;
    }
    if (uploadGb != null && (Number.isNaN(uploadGb) || uploadGb < 0)) {
      setError('Upload must be a non-negative number or empty.');
      return;
    }
    try {
      setError('');
      await internetUsageService.upsertMonth({
        year: form.year,
        month: form.month,
        total_gb: totalGb,
        download_gb: downloadGb,
        upload_gb: uploadGb,
        source: entrySource,
        notes: form.notes.trim() || null,
      });
      setSuccess(`Saved ${form.year}–${String(form.month).padStart(2, '0')}.`);
      setEntrySource('manual');
      await loadRows();
    } catch (err) {
      setError(getErrorMessage(err) || 'Save failed');
    }
  };

  const startEdit = (row) => {
    const { amount, unit } = gbToFormFields(row.total_gb);
    setForm({
      year: row.year,
      month: row.month,
      totalAmount: amount,
      totalUnit: unit,
      downloadGb: row.download_gb != null ? String(row.download_gb) : '',
      uploadGb: row.upload_gb != null ? String(row.upload_gb) : '',
      notes: row.notes || '',
    });
    setEntrySource(row.source || 'manual');
    setOcrPreview('');
    setParseNote('');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const requestDelete = (row) => {
    setConfirmModal({
      title: 'Delete this month?',
      message: `Remove usage for ${row.year} ${MONTH_NAMES[row.month - 1]} (${formatUsageFromGb(row.total_gb)})?`,
      danger: true,
      onConfirm: async () => {
        setConfirmModal(null);
        try {
          await internetUsageService.delete(row.id);
          setSuccess('Deleted.');
          await loadRows();
        } catch (err) {
          setError(getErrorMessage(err) || 'Delete failed');
        }
      },
    });
  };

  if (!user) {
    return (
      <div style={styles.container}>
        <div style={{ padding: '2rem', textAlign: 'center' }}>Loading...</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <button
            type="button"
            onClick={() => navigate('/')}
            style={styles.homeButton}
            title="Go to Home"
          >
            🏠
          </button>
          <h1 style={styles.title}>📶 Home Internet usage</h1>
        </div>
        <div style={styles.headerActions}>
          <span style={styles.userInfo}>Welcome, {user?.username || 'User'}</span>
          <button type="button" onClick={logout} style={styles.logoutButton}>
            Logout
          </button>
        </div>
      </header>

      {error && (
        <div style={styles.errorBox}>
          {error}
          <button type="button" onClick={() => setError('')} style={styles.dismissButton}>
            ×
          </button>
        </div>
      )}

      {success && (
        <div style={styles.successBox}>
          {success}
          <button type="button" onClick={() => setSuccess('')} style={styles.dismissButton}>
            ×
          </button>
        </div>
      )}

      <div style={styles.content}>
        <p style={styles.intro}>
          Log one total per calendar month. Enter numbers yourself, or upload a screenshot from the
          eero app <strong>Activity → Data usage → Month</strong>; the server uses OCR to suggest the
          month and the large total (TB/GB). Always verify before saving.
        </p>

        <section style={styles.card}>
          <h2 style={styles.cardTitle}>Add or update a month</h2>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            style={{ display: 'none' }}
            onChange={onFileSelected}
          />
          <div style={styles.uploadRow}>
            <button
              type="button"
              style={styles.secondaryButton}
              disabled={parseLoading}
              onClick={() => fileInputRef.current?.click()}
            >
              {parseLoading ? 'Reading image…' : 'Upload eero screenshot'}
            </button>
            <span style={styles.hint}>PNG or JPEG, max 15 MB. Requires Tesseract on the server.</span>
          </div>

          <form onSubmit={handleSave} style={styles.form}>
            <div style={styles.formRow}>
              <label style={styles.label}>
                Year
                <input
                  type="number"
                  min={2000}
                  max={2100}
                  value={form.year}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, year: parseInt(e.target.value, 10) || f.year }))
                  }
                  style={styles.input}
                />
              </label>
              <label style={styles.label}>
                Month
                <select
                  value={form.month}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, month: parseInt(e.target.value, 10) }))
                  }
                  style={styles.input}
                >
                  {MONTH_NAMES.map((name, i) => (
                    <option key={name} value={i + 1}>
                      {name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div style={styles.formRow}>
              <label style={styles.label}>
                Total usage
                <div style={styles.inline}>
                  <input
                    type="number"
                    step="any"
                    min="0"
                    required
                    value={form.totalAmount}
                    onChange={(e) => {
                      setEntrySource('manual');
                      setForm((f) => ({ ...f, totalAmount: e.target.value }));
                    }}
                    style={{ ...styles.input, flex: 1 }}
                    placeholder="e.g. 1.1"
                  />
                  <select
                    value={form.totalUnit}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, totalUnit: e.target.value }))
                    }
                    style={{ ...styles.input, width: '90px' }}
                  >
                    <option value="tb">TB</option>
                    <option value="gb">GB</option>
                  </select>
                </div>
              </label>
            </div>
            <div style={styles.formRow}>
              <label style={styles.label}>
                Download (GB, optional)
                <input
                  type="number"
                  step="any"
                  min="0"
                  value={form.downloadGb}
                  onChange={(e) => {
                    setEntrySource('manual');
                    setForm((f) => ({ ...f, downloadGb: e.target.value }));
                  }}
                  style={styles.input}
                  placeholder="optional"
                />
              </label>
              <label style={styles.label}>
                Upload (GB, optional)
                <input
                  type="number"
                  step="any"
                  min="0"
                  value={form.uploadGb}
                  onChange={(e) => {
                    setEntrySource('manual');
                    setForm((f) => ({ ...f, uploadGb: e.target.value }));
                  }}
                  style={styles.input}
                  placeholder="optional"
                />
              </label>
            </div>
            <label style={{ ...styles.label, display: 'block' }}>
              Notes (optional)
              <textarea
                value={form.notes}
                onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                style={{ ...styles.input, width: '100%', minHeight: '72px' }}
                placeholder="e.g. eero screenshot Mar 2026"
              />
            </label>
            <div style={styles.formActions}>
              <button type="submit" style={styles.primaryButton}>
                Save month
              </button>
              <span style={styles.meta}>
                Source: {entrySource === 'eero_snapshot' ? 'eero snapshot (OCR)' : 'Manual'}
              </span>
            </div>
          </form>

          {(ocrPreview || parseNote) && (
            <div style={styles.ocrSection}>
              {parseNote && <p style={styles.parseNote}>{parseNote}</p>}
              {ocrPreview && (
                <details>
                  <summary style={styles.summary}>OCR text preview</summary>
                  <pre style={styles.pre}>{ocrPreview}</pre>
                </details>
              )}
            </div>
          )}
        </section>

        <section style={styles.card}>
          <h2 style={styles.cardTitle}>History</h2>
          {loading ? (
            <p style={styles.muted}>Loading…</p>
          ) : rows.length === 0 ? (
            <p style={styles.muted}>No months logged yet.</p>
          ) : (
            <>
              <div style={{ width: '100%', height: 320, marginBottom: '1.5rem' }}>
                <ResponsiveContainer>
                  <BarChart data={chartData} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis
                      tickFormatter={(v) => `${v} TB`}
                      tick={{ fontSize: 11 }}
                      width={48}
                    />
                    <Tooltip
                      formatter={(value) => [`${Number(value).toFixed(2)} TB`, 'Total']}
                      labelFormatter={(l) => `Month: ${l}`}
                    />
                    <Bar dataKey="totalTb" fill="#6f42c1" name="Total" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div style={styles.tableWrap}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th style={styles.th}>Month</th>
                      <th style={styles.th}>Total</th>
                      <th style={styles.th}>Down / Up</th>
                      <th style={styles.th}>Source</th>
                      <th style={styles.th} />
                    </tr>
                  </thead>
                  <tbody>
                    {[...rows]
                      .sort((a, b) => b.year - a.year || b.month - a.month)
                      .map((r) => (
                        <tr key={r.id}>
                          <td style={styles.td}>
                            {r.year} {MONTH_NAMES[r.month - 1]}
                          </td>
                          <td style={styles.td}>{formatUsageFromGb(r.total_gb)}</td>
                          <td style={styles.td}>
                            {r.download_gb != null || r.upload_gb != null
                              ? `${r.download_gb != null ? formatUsageFromGb(r.download_gb) : '—'} / ${r.upload_gb != null ? formatUsageFromGb(r.upload_gb) : '—'}`
                              : '—'}
                          </td>
                          <td style={styles.td}>
                            {r.source === 'eero_snapshot' ? 'eero (OCR)' : 'Manual'}
                          </td>
                          <td style={styles.tdActions}>
                            <button
                              type="button"
                              style={styles.linkButton}
                              onClick={() => startEdit(r)}
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              style={styles.dangerLink}
                              onClick={() => requestDelete(r)}
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </section>
      </div>

      {confirmModal && (
        <ConfirmModal
          title={confirmModal.title}
          message={confirmModal.message}
          confirmLabel="Delete"
          danger={confirmModal.danger}
          onConfirm={confirmModal.onConfirm}
          onCancel={() => setConfirmModal(null)}
        />
      )}
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
  errorBox: {
    backgroundColor: '#f8d7da',
    color: '#721c24',
    padding: '1rem',
    margin: '1rem',
    borderRadius: '4px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  successBox: {
    backgroundColor: '#d4edda',
    color: '#155724',
    padding: '1rem',
    margin: '1rem',
    borderRadius: '4px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  dismissButton: {
    background: 'none',
    border: 'none',
    fontSize: '1.5rem',
    cursor: 'pointer',
    color: 'inherit',
  },
  content: {
    maxWidth: '960px',
    margin: '0 auto',
    padding: 'clamp(1rem, 3vw, 2rem)',
    boxSizing: 'border-box',
  },
  intro: {
    color: '#555',
    lineHeight: 1.5,
    marginBottom: '1.5rem',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.08)',
    padding: '1.5rem',
    marginBottom: '1.5rem',
  },
  cardTitle: {
    marginTop: 0,
    marginBottom: '1rem',
    fontSize: '1.2rem',
    color: '#333',
  },
  uploadRow: {
    display: 'flex',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: '0.75rem',
    marginBottom: '1.25rem',
  },
  secondaryButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#e9ecef',
    color: '#333',
    border: '1px solid #ced4da',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.95rem',
  },
  hint: {
    fontSize: '0.85rem',
    color: '#666',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  formRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
  },
  label: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.35rem',
    fontSize: '0.9rem',
    color: '#444',
    fontWeight: 500,
  },
  input: {
    padding: '0.5rem 0.65rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
  },
  inline: {
    display: 'flex',
    gap: '0.5rem',
    alignItems: 'center',
  },
  formActions: {
    display: 'flex',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: '1rem',
    marginTop: '0.5rem',
  },
  primaryButton: {
    padding: '0.65rem 1.25rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: 500,
  },
  meta: {
    fontSize: '0.85rem',
    color: '#666',
  },
  ocrSection: {
    marginTop: '1.25rem',
    paddingTop: '1rem',
    borderTop: '1px solid #eee',
  },
  parseNote: {
    color: '#856404',
    backgroundColor: '#fff3cd',
    padding: '0.75rem',
    borderRadius: '4px',
    fontSize: '0.9rem',
  },
  summary: {
    cursor: 'pointer',
    color: '#007bff',
    marginBottom: '0.5rem',
  },
  pre: {
    maxHeight: '220px',
    overflow: 'auto',
    fontSize: '0.75rem',
    backgroundColor: '#f8f9fa',
    padding: '0.75rem',
    borderRadius: '4px',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  muted: {
    color: '#666',
  },
  tableWrap: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '0.95rem',
  },
  th: {
    textAlign: 'left',
    padding: '0.65rem',
    borderBottom: '2px solid #dee2e6',
    color: '#495057',
  },
  td: {
    padding: '0.65rem',
    borderBottom: '1px solid #eee',
    verticalAlign: 'middle',
  },
  tdActions: {
    padding: '0.65rem',
    borderBottom: '1px solid #eee',
    whiteSpace: 'nowrap',
    textAlign: 'right',
  },
  linkButton: {
    background: 'none',
    border: 'none',
    color: '#007bff',
    cursor: 'pointer',
    marginRight: '0.75rem',
    fontSize: '0.9rem',
    textDecoration: 'underline',
  },
  dangerLink: {
    background: 'none',
    border: 'none',
    color: '#dc3545',
    cursor: 'pointer',
    fontSize: '0.9rem',
    textDecoration: 'underline',
  },
};
