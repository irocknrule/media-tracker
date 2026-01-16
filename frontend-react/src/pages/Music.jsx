import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { musicService } from '../services/musicService';
import { searchService } from '../services/searchService';
import { getErrorMessage } from '../utils/errorHandler';

export default function Music() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [music, setMusic] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [yearFilter, setYearFilter] = useState('');
  const [activeTab, setActiveTab] = useState('view');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingMusic, setEditingMusic] = useState(null);
  const [expandedMusic, setExpandedMusic] = useState(new Set());
  const [uploadedThumbnail, setUploadedThumbnail] = useState(null);
  const [showNotes, setShowNotes] = useState(true);
  const [showWantToListenOnly, setShowWantToListenOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedMusic, setSelectedMusic] = useState(null);
  const [searching, setSearching] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    artist: '',
    album: '',
    listened_date: '',
    status: 'listened',
    rating: 5.0,
    notes: '',
    thumbnail_url: '',
  });

  useEffect(() => {
    loadMusic();
  }, [yearFilter, showWantToListenOnly, activeTab]);

  const loadMusic = async () => {
    try {
      setLoading(true);
      setError('');
      const params = yearFilter ? { year: parseInt(yearFilter) } : {};
      const data = await musicService.getAll(params);
      
      let filteredData = data || [];
      
      if (activeTab === 'view') {
        filteredData = filteredData.filter(music => music.status === 'listened');
      }
      
      if (activeTab === 'manage' && showWantToListenOnly) {
        filteredData = filteredData.filter(music => music.status === 'want_to_listen');
      }
      
      setMusic(filteredData);
    } catch (err) {
      console.error('Error loading music:', err);
      const errorMessage = getErrorMessage(err) || 'Failed to load music';
      setError(errorMessage);
      setMusic([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    setError('');
    try {
      const results = await searchService.searchMusic(searchQuery);
      setSearchResults(results);
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError('Failed to search music: ' + errorMessage);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleSelectMusic = (music) => {
    setSelectedMusic(music);
    setFormData({
      ...formData,
      title: music.title || '',
      artist: music.artist || '',
      album: music.title || '',
      thumbnail_url: music.thumbnail || '',
    });
  };

  const handleThumbnailUpload = (event) => {
    const file = event.target.files[0];
    if (!file) {
      setUploadedThumbnail(null);
      setFormData({ ...formData, thumbnail_url: '' });
      return;
    }

    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      setError('Please upload a valid image file (PNG, JPG, GIF, or WebP)');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError('Image file size must be less than 5MB');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const base64String = e.target.result;
      setUploadedThumbnail(base64String);
      setFormData({ ...formData, thumbnail_url: base64String });
    };
    reader.onerror = () => {
      setError('Failed to read image file');
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const musicData = {
        ...formData,
        rating: formData.rating ? parseFloat(formData.rating) : null,
        listened_date: formData.listened_date || null,
      };
      
      if (editingMusic) {
        await musicService.update(editingMusic.id, musicData);
        setEditingMusic(null);
      } else {
        await musicService.create(musicData);
      }
      
      resetForm();
      loadMusic();
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError((editingMusic ? 'Failed to update music: ' : 'Failed to add music: ') + errorMessage);
    }
  };

  const handleEdit = (music) => {
    setEditingMusic(music);
    setUploadedThumbnail(music.thumbnail_url?.startsWith('data:') ? music.thumbnail_url : null);
    setSelectedMusic(null);
    setFormData({
      title: music.title || '',
      artist: music.artist || '',
      album: music.album || '',
      listened_date: music.listened_date || '',
      status: music.status || 'listened',
      rating: music.rating || 5.0,
      notes: music.notes || '',
      thumbnail_url: music.thumbnail_url || '',
    });
    setShowAddForm(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this music entry?')) {
      return;
    }
    
    try {
      await musicService.delete(id);
      loadMusic();
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError('Failed to delete music: ' + errorMessage);
    }
  };

  const resetForm = () => {
    setShowAddForm(false);
    setEditingMusic(null);
    setUploadedThumbnail(null);
    setSelectedMusic(null);
    setSearchQuery('');
    setSearchResults([]);
    setFormData({
      title: '',
      artist: '',
      album: '',
      listened_date: '',
      status: 'listened',
      rating: 5.0,
      notes: '',
      thumbnail_url: '',
    });
    const fileInput = document.getElementById('thumbnail-upload');
    if (fileInput) {
      fileInput.value = '';
    }
  };

  const toggleExpanded = (musicId) => {
    const newExpanded = new Set(expandedMusic);
    if (newExpanded.has(musicId)) {
      newExpanded.delete(musicId);
    } else {
      newExpanded.add(musicId);
    }
    setExpandedMusic(newExpanded);
  };

  const currentYear = new Date().getFullYear();
  const years = ['All', ...Array.from({ length: currentYear - 1900 + 1 }, (_, i) => currentYear - i)];

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
            onClick={() => navigate('/')}
            style={styles.homeButton}
            title="Go to Home"
          >
            🏠
          </button>
          <h1 style={styles.title}>🎵 Music</h1>
        </div>
        <div style={styles.headerActions}>
          <span style={styles.userInfo}>Welcome, {user?.username || 'User'}</span>
          <button onClick={logout} style={styles.logoutButton}>
            Logout
          </button>
        </div>
      </header>

      <div style={styles.content}>
        <div style={styles.tabContainer}>
          <button
            onClick={() => {
              setActiveTab('view');
              setShowAddForm(false);
              resetForm();
            }}
            style={activeTab === 'view' ? styles.activeTab : styles.tab}
          >
            🎵 View Music
          </button>
          <button
            onClick={() => {
              setActiveTab('manage');
            }}
            style={activeTab === 'manage' ? styles.activeTab : styles.tab}
          >
            ⚙️ Manage Music
          </button>
          <button
            onClick={() => {
              setActiveTab('details');
            }}
            style={activeTab === 'details' ? styles.activeTab : styles.tab}
          >
            📋 Music Details
          </button>
        </div>

        <div style={styles.controls}>
          <div style={styles.filterGroup}>
            <label htmlFor="yearFilter" style={styles.label}>
              Filter by Year:
            </label>
            <select
              id="yearFilter"
              value={yearFilter}
              onChange={(e) => setYearFilter(e.target.value === 'All' ? '' : e.target.value)}
              style={styles.select}
            >
              {years.map((year) => (
                <option key={year} value={year === 'All' ? '' : year}>
                  {year}
                </option>
              ))}
            </select>
          </div>
          
          <div style={styles.controlsRight}>
            {activeTab !== 'details' && (
              <label style={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={showWantToListenOnly}
                  onChange={(e) => setShowWantToListenOnly(e.target.checked)}
                  style={styles.checkbox}
                />
                Want to Listen
              </label>
            )}
            
            {activeTab === 'view' && (
              <label style={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={showNotes}
                  onChange={(e) => setShowNotes(e.target.checked)}
                  style={styles.checkbox}
                />
                Show Notes
              </label>
            )}
            
            {activeTab === 'manage' && (
              <button
                onClick={() => {
                  if (showAddForm) {
                    resetForm();
                  } else {
                    setShowAddForm(true);
                  }
                }}
                style={styles.addButton}
              >
                {showAddForm ? 'Cancel' : '+ Add Music'}
              </button>
            )}
          </div>
        </div>

        {error && (
          <div style={styles.error}>
            {typeof error === 'string' ? error : getErrorMessage(error)}
          </div>
        )}

        {activeTab === 'manage' && showAddForm && (
          <div style={styles.formCard}>
            <h2 style={styles.formTitle}>
              {editingMusic ? 'Edit Music' : 'Add New Music'}
            </h2>

            {/* Search */}
            {!editingMusic && (
              <div style={styles.searchSection}>
                <div style={styles.searchInputGroup}>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleSearch();
                      }
                    }}
                    placeholder="🔍 Search for an album or song..."
                    style={styles.searchInput}
                  />
                  <button
                    onClick={handleSearch}
                    disabled={searching || !searchQuery.trim()}
                    style={styles.searchButton}
                  >
                    {searching ? '⏳ Searching...' : 'Search'}
                  </button>
                </div>

                {searchResults.length > 0 && !selectedMusic && (
                  <div style={styles.searchResults}>
                    <h3>Search Results</h3>
                    <div style={styles.resultsGrid}>
                      {searchResults.map((result, idx) => (
                        <div
                          key={idx}
                          style={styles.resultCard}
                          onClick={() => handleSelectMusic(result)}
                        >
                          {result.thumbnail && (
                            <img
                              src={result.thumbnail}
                              alt={result.title}
                              style={styles.resultThumbnail}
                              onError={(e) => {
                                e.target.style.display = 'none';
                              }}
                            />
                          )}
                          {!result.thumbnail && (
                            <div style={styles.resultPlaceholder}>🎵</div>
                          )}
                          <div style={styles.resultInfo}>
                            <strong>{result.title}</strong>
                            {result.artist && <p>by {result.artist}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedMusic && (
                  <div style={styles.selectedMusic}>
                    <div style={styles.selectedMusicHeader}>
                      <span>✅ Selected: <strong>{selectedMusic.title}</strong></span>
                      <button
                        onClick={() => {
                          setSelectedMusic(null);
                          setSearchQuery('');
                          setSearchResults([]);
                        }}
                        style={styles.clearButton}
                      >
                        Clear Selection
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            <form onSubmit={handleSubmit} style={styles.form}>
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Title *</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    required
                    style={styles.input}
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Artist</label>
                  <input
                    type="text"
                    value={formData.artist}
                    onChange={(e) => setFormData({ ...formData, artist: e.target.value })}
                    style={styles.input}
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Album</label>
                  <input
                    type="text"
                    value={formData.album}
                    onChange={(e) => setFormData({ ...formData, album: e.target.value })}
                    style={styles.input}
                    placeholder="Optional - defaults to title"
                  />
                </div>
              </div>
              
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Listened Date</label>
                  <input
                    type="date"
                    value={formData.listened_date}
                    onChange={(e) => setFormData({ ...formData, listened_date: e.target.value })}
                    style={styles.input}
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    style={styles.input}
                  >
                    <option value="listened">Listened</option>
                    <option value="currently_listening">Currently Listening</option>
                    <option value="want_to_listen">Want to Listen</option>
                    <option value="dropped">Dropped</option>
                  </select>
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>
                    Rating: {formData.rating}/10
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="10"
                    step="0.5"
                    value={formData.rating}
                    onChange={(e) => setFormData({ ...formData, rating: parseFloat(e.target.value) })}
                    style={styles.slider}
                  />
                </div>
              </div>
              
              <div style={styles.formGroup}>
                <label style={styles.label}>Cover Image</label>
                <div style={styles.thumbnailSection}>
                  <div style={styles.thumbnailOptions}>
                    <label style={styles.uploadLabel}>
                      <input
                        id="thumbnail-upload"
                        type="file"
                        accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
                        onChange={handleThumbnailUpload}
                        style={styles.fileInput}
                      />
                      <span style={styles.uploadButton}>📁 Upload Image</span>
                    </label>
                    <span style={styles.thumbnailOr}>or</span>
                    <input
                      type="url"
                      value={formData.thumbnail_url && !formData.thumbnail_url.startsWith('data:') ? formData.thumbnail_url : ''}
                      onChange={(e) => {
                        setFormData({ ...formData, thumbnail_url: e.target.value });
                        setUploadedThumbnail(null);
                      }}
                      placeholder="Enter image URL"
                      style={styles.input}
                    />
                  </div>
                  {(uploadedThumbnail || (formData.thumbnail_url && !formData.thumbnail_url.startsWith('data:') && formData.thumbnail_url)) && (
                    <div style={styles.thumbnailPreviewContainer}>
                      <img
                        src={uploadedThumbnail || formData.thumbnail_url}
                        alt="Cover Preview"
                        style={styles.thumbnailPreview}
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                      {uploadedThumbnail && (
                        <button
                          type="button"
                          onClick={() => {
                            setUploadedThumbnail(null);
                            setFormData({ ...formData, thumbnail_url: '' });
                            const fileInput = document.getElementById('thumbnail-upload');
                            if (fileInput) {
                              fileInput.value = '';
                            }
                          }}
                          style={styles.removeThumbnailButton}
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
              
              <div style={styles.formGroup}>
                <label style={styles.label}>Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows="3"
                  style={styles.textarea}
                />
              </div>
              
              <div style={styles.formActions}>
                <button type="submit" style={styles.submitButton}>
                  {editingMusic ? 'Update Music' : 'Add Music'}
                </button>
                <button
                  type="button"
                  onClick={resetForm}
                  style={styles.cancelButton}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {loading ? (
          <div style={styles.loading}>Loading music...</div>
        ) : music.length === 0 ? (
          <div style={styles.empty}>
            {activeTab === 'view' 
              ? 'No music found. Switch to Manage tab to add music!' 
              : 'No music found. Add your first music entry!'}
          </div>
        ) : activeTab === 'view' ? (
          <div style={styles.musicGrid}>
            {music.map((musicItem) => (
              <div key={musicItem.id} style={styles.musicCard}>
                {musicItem.thumbnail_url && (
                  <img
                    src={musicItem.thumbnail_url}
                    alt={musicItem.title}
                    style={styles.thumbnail}
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                )}
                {!musicItem.thumbnail_url && (
                  <div style={styles.thumbnailPlaceholder}>🎵</div>
                )}
                <div style={styles.musicInfo}>
                  <h3 style={styles.musicTitle}>{musicItem.title}</h3>
                  {musicItem.artist && <p style={styles.musicArtist}>by {musicItem.artist}</p>}
                  {musicItem.album && <p style={styles.musicAlbum}>{musicItem.album}</p>}
                  {musicItem.rating && (
                    <p style={styles.musicRating}>⭐ {musicItem.rating}/10</p>
                  )}
                  {musicItem.listened_date && (
                    <p style={styles.musicDate}>
                      Listened: {new Date(musicItem.listened_date).toLocaleDateString()}
                    </p>
                  )}
                  {showNotes && musicItem.notes && (
                    <p style={styles.musicNotes}>{musicItem.notes}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : activeTab === 'details' ? (
          <div style={styles.detailsSection}>
            <h2 style={styles.detailsTitle}>Music Details</h2>
            {music.length === 0 ? (
              <div style={styles.empty}>No music found. Add music in the Manage Music tab!</div>
            ) : (
              music.map((musicItem) => (
                <div key={musicItem.id} style={styles.detailCard}>
                  <div
                    style={styles.detailHeader}
                    onClick={() => toggleExpanded(musicItem.id)}
                  >
                    <div>
                      <strong>{musicItem.title}</strong>
                      {musicItem.artist && <span style={styles.detailArtist}> by {musicItem.artist}</span>}
                      {musicItem.listened_date && (
                        <span style={styles.detailDate}>
                          {' - '}
                          {new Date(musicItem.listened_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                    <span style={styles.expandIcon}>
                      {expandedMusic.has(musicItem.id) ? '▼' : '▶'}
                    </span>
                  </div>
                  
                  {expandedMusic.has(musicItem.id) && (
                    <div style={styles.detailContent}>
                      <div style={styles.detailRow}>
                        <div style={styles.detailCol}>
                          <strong>Listened:</strong> {musicItem.listened_date ? new Date(musicItem.listened_date).toLocaleDateString() : 'N/A'}
                        </div>
                        <div style={styles.detailCol}>
                          <strong>Album:</strong> {musicItem.album || 'N/A'}
                        </div>
                        <div style={styles.detailCol}>
                          <strong>Rating:</strong> {musicItem.rating ? `${musicItem.rating}/10` : 'N/A'}
                        </div>
                        <div style={styles.detailCol}>
                          <strong>Status:</strong> {musicItem.status || 'N/A'}
                        </div>
                      </div>
                      {musicItem.notes && (
                        <div style={styles.detailNotes}>
                          <strong>Notes:</strong> {musicItem.notes}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        ) : (
          <div style={styles.musicGrid}>
            {music.map((musicItem) => (
              <div key={musicItem.id} style={styles.musicCard}>
                {musicItem.thumbnail_url && (
                  <img
                    src={musicItem.thumbnail_url}
                    alt={musicItem.title}
                    style={styles.thumbnail}
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                )}
                {!musicItem.thumbnail_url && (
                  <div style={styles.thumbnailPlaceholder}>🎵</div>
                )}
                <div style={styles.musicInfo}>
                  <h3 style={styles.musicTitle}>{musicItem.title}</h3>
                  {musicItem.artist && <p style={styles.musicArtist}>by {musicItem.artist}</p>}
                  {musicItem.album && <p style={styles.musicAlbum}>{musicItem.album}</p>}
                  {musicItem.rating && (
                    <p style={styles.musicRating}>⭐ {musicItem.rating}/10</p>
                  )}
                  {musicItem.listened_date && (
                    <p style={styles.musicDate}>
                      Listened: {new Date(musicItem.listened_date).toLocaleDateString()}
                    </p>
                  )}
                  <div style={styles.musicActions}>
                    <button
                      onClick={() => handleEdit(musicItem)}
                      style={styles.editButton}
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(musicItem.id)}
                      style={styles.deleteButton}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Styles - same structure as Movies.jsx
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
    maxWidth: '100%',
    margin: '0 auto',
    padding: 'clamp(1rem, 3vw, 2rem)',
    boxSizing: 'border-box',
  },
  tabContainer: {
    display: 'flex',
    gap: '0.5rem',
    marginBottom: '2rem',
    borderBottom: '2px solid #dee2e6',
  },
  tab: {
    padding: '0.75rem 1.5rem',
    backgroundColor: 'transparent',
    color: '#666',
    border: 'none',
    borderBottom: '2px solid transparent',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '500',
    marginBottom: '-2px',
    transition: 'all 0.2s',
  },
  activeTab: {
    padding: '0.75rem 1.5rem',
    backgroundColor: 'transparent',
    color: '#007bff',
    border: 'none',
    borderBottom: '2px solid #007bff',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '600',
    marginBottom: '-2px',
  },
  controls: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '2rem',
    gap: '1rem',
    flexWrap: 'wrap',
  },
  controlsRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  checkboxLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    cursor: 'pointer',
    userSelect: 'none',
    color: '#333',
    fontSize: '0.9rem',
  },
  checkbox: {
    width: '18px',
    height: '18px',
    cursor: 'pointer',
  },
  filterGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  label: {
    fontWeight: '500',
    color: '#333',
    marginBottom: '0.25rem',
    display: 'block',
  },
  select: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
  },
  addButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
  },
  error: {
    backgroundColor: '#fee',
    color: '#c33',
    padding: '1rem',
    borderRadius: '4px',
    marginBottom: '1rem',
  },
  formCard: {
    backgroundColor: 'white',
    padding: 'clamp(1rem, 3vw, 2rem)',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    marginBottom: '2rem',
    width: '100%',
    boxSizing: 'border-box',
  },
  formTitle: {
    marginTop: 0,
    marginBottom: '0.5rem',
  },
  searchSection: {
    marginBottom: '2rem',
  },
  searchInputGroup: {
    display: 'flex',
    gap: '0.5rem',
    marginBottom: '1rem',
  },
  searchInput: {
    flex: 1,
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
  },
  searchButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
  },
  searchResults: {
    marginTop: '1rem',
  },
  resultsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
    gap: '1rem',
    marginTop: '1rem',
  },
  resultCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: '4px',
    padding: '0.5rem',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  resultThumbnail: {
    width: '100%',
    height: '200px',
    objectFit: 'cover',
    borderRadius: '4px',
    marginBottom: '0.5rem',
  },
  resultPlaceholder: {
    width: '100%',
    height: '200px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#e9ecef',
    borderRadius: '4px',
    fontSize: '3rem',
    marginBottom: '0.5rem',
  },
  resultInfo: {
    textAlign: 'center',
    fontSize: '0.9rem',
  },
  selectedMusic: {
    marginTop: '1rem',
    padding: '1rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '4px',
  },
  selectedMusicHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  clearButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
  },
  formRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
    marginBottom: '1rem',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
  },
  input: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
  },
  slider: {
    width: '100%',
  },
  thumbnailSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  thumbnailOptions: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    flexWrap: 'wrap',
  },
  uploadLabel: {
    cursor: 'pointer',
  },
  fileInput: {
    display: 'none',
  },
  uploadButton: {
    display: 'inline-block',
    padding: '0.5rem 1rem',
    backgroundColor: '#6c757d',
    color: 'white',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  thumbnailOr: {
    color: '#666',
    fontSize: '0.9rem',
  },
  thumbnailPreviewContainer: {
    position: 'relative',
    display: 'inline-block',
  },
  thumbnailPreview: {
    maxWidth: '200px',
    maxHeight: '300px',
    borderRadius: '4px',
    border: '1px solid #ddd',
    display: 'block',
  },
  removeThumbnailButton: {
    position: 'absolute',
    top: '0.5rem',
    right: '0.5rem',
    padding: '0.25rem 0.5rem',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.8rem',
  },
  textarea: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
    fontFamily: 'inherit',
  },
  formActions: {
    display: 'flex',
    gap: '1rem',
    marginTop: '1rem',
  },
  submitButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
  },
  cancelButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
  },
  loading: {
    textAlign: 'center',
    padding: '2rem',
    color: '#666',
  },
  empty: {
    textAlign: 'center',
    padding: '2rem',
    color: '#666',
  },
  musicGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(min(250px, 100%), 1fr))',
    gap: 'clamp(1rem, 2vw, 1.5rem)',
    marginBottom: '3rem',
    width: '100%',
  },
  musicCard: {
    backgroundColor: 'white',
    borderRadius: '8px',
    overflow: 'hidden',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    display: 'flex',
    flexDirection: 'column',
    transition: 'transform 0.2s, box-shadow 0.2s',
  },
  thumbnail: {
    width: '100%',
    height: '350px',
    objectFit: 'cover',
  },
  thumbnailPlaceholder: {
    width: '100%',
    height: '350px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '4rem',
    backgroundColor: '#f0f0f0',
  },
  musicInfo: {
    padding: '1rem',
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },
  musicTitle: {
    margin: '0 0 0.5rem 0',
    fontSize: '1.1rem',
    color: '#333',
  },
  musicArtist: {
    margin: '0 0 0.5rem 0',
    color: '#666',
    fontSize: '0.9rem',
  },
  musicAlbum: {
    margin: '0 0 0.5rem 0',
    color: '#666',
    fontSize: '0.9rem',
  },
  musicRating: {
    margin: '0 0 0.5rem 0',
    color: '#333',
    fontWeight: '500',
  },
  musicDate: {
    margin: '0 0 0.5rem 0',
    color: '#666',
    fontSize: '0.9rem',
  },
  musicNotes: {
    margin: '0.5rem 0 0 0',
    color: '#666',
    fontSize: '0.85rem',
    fontStyle: 'italic',
  },
  musicActions: {
    display: 'flex',
    gap: '0.5rem',
    marginTop: 'auto',
  },
  editButton: {
    padding: '0.5rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    flex: 1,
  },
  deleteButton: {
    padding: '0.5rem',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    flex: 1,
  },
  detailsSection: {
    marginTop: '3rem',
    backgroundColor: 'white',
    padding: 'clamp(1rem, 3vw, 2rem)',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    width: '100%',
    boxSizing: 'border-box',
  },
  detailsTitle: {
    marginTop: 0,
    marginBottom: '1.5rem',
  },
  detailCard: {
    border: '1px solid #ddd',
    borderRadius: '4px',
    marginBottom: '0.5rem',
    overflow: 'hidden',
  },
  detailHeader: {
    padding: '1rem',
    backgroundColor: '#f8f9fa',
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    userSelect: 'none',
  },
  detailArtist: {
    color: '#666',
    fontWeight: 'normal',
  },
  detailDate: {
    color: '#666',
    fontWeight: 'normal',
  },
  expandIcon: {
    color: '#666',
    fontSize: '0.8rem',
  },
  detailContent: {
    padding: '1rem',
  },
  detailRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
    marginBottom: '1rem',
  },
  detailCol: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  detailNotes: {
    paddingTop: '1rem',
    borderTop: '1px solid #eee',
  },
};
