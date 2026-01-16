import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { tvShowService } from '../services/tvShowService';
import { tvShowDetailsService } from '../services/tvShowDetailsService';
import { getErrorMessage } from '../utils/errorHandler';

export default function TVShows() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [tvShows, setTvShows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [yearFilter, setYearFilter] = useState('');
  const [activeTab, setActiveTab] = useState('view'); // 'view', 'manage', 'details', 'currently_watching'
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingShow, setEditingShow] = useState(null);
  const [editingSeason, setEditingSeason] = useState(null);
  const [uploadedThumbnail, setUploadedThumbnail] = useState(null);
  const [expandedShows, setExpandedShows] = useState(new Set());
  const [showNotes, setShowNotes] = useState(true);
  const [showWantToWatchOnly, setShowWantToWatchOnly] = useState(false);
  
  // Search and add form state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedShow, setSelectedShow] = useState(null);
  const [seasons, setSeasons] = useState([]);
  const [selectedSeason, setSelectedSeason] = useState(null);
  const [searching, setSearching] = useState(false);
  const [loadingSeasons, setLoadingSeasons] = useState(false);
  
  // Form data
  const [formData, setFormData] = useState({
    title: '',
    season: 1,
    status: 'watched',
    watched_date: '',
    rating: 5.0,
    notes: '',
    show_thumbnail_url: '',
    season_thumbnail_url: '',
  });

  useEffect(() => {
    loadTVShows();
  }, [yearFilter, showWantToWatchOnly, activeTab]);

  const loadTVShows = async () => {
    try {
      setLoading(true);
      setError('');
      const params = yearFilter ? { year: parseInt(yearFilter) } : {};
      const data = await tvShowService.getAll(params);
      
      // Filter TV shows based on active tab and filters
      let filteredData = data || [];
      
      if (activeTab === 'view') {
        // View tab: Only show watched shows
        filteredData = filteredData.filter(show => show.status === 'watched');
      } else if (activeTab === 'currently_watching') {
        // Currently Watching tab: Only show currently watching shows
        filteredData = filteredData.filter(show => show.status === 'currently_watching');
      }
      
      // Apply "Want to watch only" filter (only in Manage tab)
      if (activeTab === 'manage' && showWantToWatchOnly) {
        filteredData = filteredData.filter(show => show.status === 'want_to_watch');
      }
      
      setTvShows(filteredData);
    } catch (err) {
      console.error('Error loading TV shows:', err);
      const errorMessage = getErrorMessage(err) || 'Failed to load TV shows';
      setError(errorMessage);
      setTvShows([]);
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
      const results = await tvShowDetailsService.search(searchQuery);
      setSearchResults(results);
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError('Failed to search TV shows: ' + errorMessage);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleThumbnailUpload = (event, isSeason = false) => {
    const file = event.target.files[0];
    if (!file) {
      setUploadedThumbnail(null);
      if (isSeason) {
        setFormData({ ...formData, season_thumbnail_url: '' });
      } else {
        setFormData({ ...formData, show_thumbnail_url: '' });
      }
      return;
    }

    // Validate file type
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      setError('Please upload a valid image file (PNG, JPG, GIF, or WebP)');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('Image file size must be less than 5MB');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const base64String = e.target.result;
      setUploadedThumbnail(base64String);
      if (isSeason) {
        setFormData({ ...formData, season_thumbnail_url: base64String });
      } else {
        setFormData({ ...formData, show_thumbnail_url: base64String });
      }
    };
    reader.onerror = () => {
      setError('Failed to read image file');
    };
    reader.readAsDataURL(file);
  };

  const handleSelectShow = async (show) => {
    setSelectedShow(show);
    setFormData({
      ...formData,
      title: show.title || '',
      show_thumbnail_url: show.thumbnail || '',
    });

    if (show.tvmaze_id) {
      setLoadingSeasons(true);
      try {
        const seasonsData = await tvShowDetailsService.getSeasons(show.tvmaze_id);
        setSeasons(seasonsData || []);
      } catch (err) {
        const errorMessage = getErrorMessage(err);
        setError('Failed to load seasons: ' + errorMessage);
        setSeasons([]);
      } finally {
        setLoadingSeasons(false);
      }
    } else {
      setSeasons([]);
    }
  };

  const handleSelectSeason = (season) => {
    setSelectedSeason(season);
    setFormData({
      ...formData,
      season: season.number || 1,
      season_thumbnail_url: season.image || formData.season_thumbnail_url,
    });
  };

  const handleEdit = (show, season = null) => {
    setEditingShow(show);
    if (season) {
      // Editing a specific season
      setEditingSeason(season);
      setUploadedThumbnail(season.season_thumbnail_url?.startsWith('data:') ? season.season_thumbnail_url : null);
      setFormData({
        title: show.title || '',
        season: season.season_number || 1,
        status: show.status || 'watched',
        watched_date: season.watched_date || '',
        rating: season.rating || 5.0,
        notes: season.notes || '',
        show_thumbnail_url: show.show_thumbnail_url || '',
        season_thumbnail_url: season.season_thumbnail_url || '',
      });
    } else {
      // Editing show metadata (first season if available)
      const firstSeason = show.seasons && show.seasons.length > 0 ? show.seasons[0] : null;
      setEditingSeason(firstSeason);
      setUploadedThumbnail(firstSeason?.season_thumbnail_url?.startsWith('data:') ? firstSeason.season_thumbnail_url : null);
      setFormData({
        title: show.title || '',
        season: firstSeason ? firstSeason.season_number : 1,
        status: show.status || 'watched',
        watched_date: firstSeason ? (firstSeason.watched_date || '') : '',
        rating: firstSeason ? (firstSeason.rating || 5.0) : 5.0,
        notes: firstSeason ? (firstSeason.notes || '') : '',
        show_thumbnail_url: show.show_thumbnail_url || '',
        season_thumbnail_url: firstSeason ? (firstSeason.season_thumbnail_url || '') : '',
      });
    }
    setShowAddForm(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingShow) {
        // Update show metadata
        const showUpdateData = {
          title: formData.title,
          status: formData.status,
          show_thumbnail_url: formData.show_thumbnail_url || null,
        };
        await tvShowService.update(editingShow.id, showUpdateData);
        
        // Update the season being edited
        if (editingSeason) {
          const seasonUpdateData = {
            season_number: formData.season ? parseInt(formData.season) : editingSeason.season_number,
            watched_date: formData.watched_date || null,
            rating: formData.rating ? parseFloat(formData.rating) : null,
            notes: formData.notes || null,
            season_thumbnail_url: formData.season_thumbnail_url || null,
          };
          await tvShowService.updateSeason(editingSeason.id, seasonUpdateData);
        }
        setEditingShow(null);
        setEditingSeason(null);
      } else {
        // Create new show with season
        const showData = {
          title: formData.title,
          season: formData.season ? parseInt(formData.season) : 1,
          status: formData.status,
          watched_date: formData.watched_date || null,
          rating: formData.rating ? parseFloat(formData.rating) : null,
          notes: formData.notes || null,
          thumbnail_url: formData.season_thumbnail_url || formData.show_thumbnail_url || null,
        };
        await tvShowService.createLegacy(showData);
      }
      
      resetForm();
      loadTVShows();
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError((editingShow ? 'Failed to update TV show: ' : 'Failed to add TV show: ') + errorMessage);
    }
  };

  const handleDeleteShow = async (showId) => {
    if (!window.confirm('Are you sure you want to delete this TV show and all its seasons?')) {
      return;
    }

    try {
      await tvShowService.delete(showId);
      loadTVShows();
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError('Failed to delete TV show: ' + errorMessage);
    }
  };

  const handleDeleteSeason = async (seasonId) => {
    if (!window.confirm('Are you sure you want to delete this season?')) {
      return;
    }

    try {
      await tvShowService.deleteSeason(seasonId);
      loadTVShows();
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError('Failed to delete season: ' + errorMessage);
    }
  };

  const resetForm = () => {
    setShowAddForm(false);
    setEditingShow(null);
    setEditingSeason(null);
    setUploadedThumbnail(null);
    setSearchQuery('');
    setSearchResults([]);
    setSelectedShow(null);
    setSelectedSeason(null);
    setSeasons([]);
    setFormData({
      title: '',
      season: 1,
      status: 'watched',
      watched_date: '',
      rating: 5.0,
      notes: '',
      show_thumbnail_url: '',
      season_thumbnail_url: '',
    });
    // Reset file inputs
    const showFileInput = document.getElementById('show-thumbnail-upload');
    const seasonFileInput = document.getElementById('season-thumbnail-upload');
    if (showFileInput) showFileInput.value = '';
    if (seasonFileInput) seasonFileInput.value = '';
  };

  const toggleExpanded = (showId) => {
    const newExpanded = new Set(expandedShows);
    if (newExpanded.has(showId)) {
      newExpanded.delete(showId);
    } else {
      newExpanded.add(showId);
    }
    setExpandedShows(newExpanded);
  };

  // Group seasons by year
  const groupSeasonsByYear = (seasons) => {
    const grouped = {};
    seasons.forEach((season) => {
      if (season.watched_date) {
        const year = season.watched_date.split('-')[0];
        if (!grouped[year]) {
          grouped[year] = [];
        }
        grouped[year].push(season);
      } else {
        if (!grouped['Unknown']) {
          grouped['Unknown'] = [];
        }
        grouped['Unknown'].push(season);
      }
    });
    return grouped;
  };

  const currentYear = new Date().getFullYear();
  const years = ['All', ...Array.from({ length: currentYear - 2020 + 2 }, (_, i) => currentYear + 1 - i)];

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
          <h1 style={styles.title}>📺 TV Shows</h1>
        </div>
        <div style={styles.headerActions}>
          <span style={styles.userInfo}>Welcome, {user?.username || 'User'}</span>
          <button onClick={logout} style={styles.logoutButton}>
            Logout
          </button>
        </div>
      </header>

      <div style={styles.content}>
        {/* Tab Navigation */}
        <div style={styles.tabContainer}>
          <button
            onClick={() => {
              setActiveTab('view');
              setShowAddForm(false);
              resetForm();
            }}
            style={activeTab === 'view' ? styles.activeTab : styles.tab}
          >
            📺 View TV Shows
          </button>
          <button
            onClick={() => {
              setActiveTab('currently_watching');
              setShowAddForm(false);
              resetForm();
            }}
            style={activeTab === 'currently_watching' ? styles.activeTab : styles.tab}
          >
            👀 Currently Watching
          </button>
          <button
            onClick={() => {
              setActiveTab('manage');
            }}
            style={activeTab === 'manage' ? styles.activeTab : styles.tab}
          >
            ⚙️ Manage TV Shows
          </button>
          <button
            onClick={() => {
              setActiveTab('details');
            }}
            style={activeTab === 'details' ? styles.activeTab : styles.tab}
          >
            📋 TV Show Details
          </button>
        </div>

        {/* Year Filter and Options */}
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
            {activeTab === 'manage' && (
              <label style={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={showWantToWatchOnly}
                  onChange={(e) => setShowWantToWatchOnly(e.target.checked)}
                  style={styles.checkbox}
                />
                In My Queue
              </label>
            )}
            
            {(activeTab === 'view' || activeTab === 'currently_watching') && (
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
                {showAddForm ? 'Cancel' : '+ Add TV Show'}
              </button>
            )}
          </div>
        </div>

        {error && (
          <div style={styles.error}>
            {typeof error === 'string' ? error : getErrorMessage(error)}
          </div>
        )}

        {/* Add/Edit Form - only in manage tab */}
        {activeTab === 'manage' && showAddForm && (
          <div style={styles.formCard}>
            <h2 style={styles.formTitle}>
              {editingShow ? 'Edit TV Show' : 'Add New TV Show'}
            </h2>

            {/* Search */}
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
                  placeholder="🔍 Search for a TV show..."
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

              {/* Search Results */}
              {searchResults.length > 0 && !selectedShow && (
                <div style={styles.searchResults}>
                  <h3>Search Results</h3>
                  <div style={styles.resultsGrid}>
                    {searchResults.map((result, idx) => (
                      <div
                        key={idx}
                        style={styles.resultCard}
                        onClick={() => handleSelectShow(result)}
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
                          <div style={styles.resultPlaceholder}>📺</div>
                        )}
                        <div style={styles.resultInfo}>
                          <strong>{result.title}</strong>
                          {result.year && <p>{result.year}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Selected Show */}
              {selectedShow && (
                <div style={styles.selectedShow}>
                  <div style={styles.selectedShowHeader}>
                    <span>✅ Selected: <strong>{selectedShow.title}</strong></span>
                    <button
                      onClick={resetForm}
                      style={styles.clearButton}
                    >
                      Clear Selection
                    </button>
                  </div>

                  {/* Seasons Selection */}
                  {loadingSeasons ? (
                    <div style={styles.loading}>Loading seasons...</div>
                  ) : seasons.length > 0 ? (
                    <>
                      <h3 style={styles.seasonsSelectTitle}>Select a Season</h3>
                      <div style={styles.seasonsSelectGrid}>
                        {seasons.map((season) => (
                          <div
                            key={season.number}
                            style={{
                              ...styles.seasonSelectCard,
                              ...(selectedSeason?.number === season.number ? styles.seasonSelectCardActive : {}),
                            }}
                            onClick={() => handleSelectSeason(season)}
                          >
                            {season.image && (
                              <img
                                src={season.image}
                                alt={`Season ${season.number}`}
                                style={styles.seasonSelectThumbnail}
                                onError={(e) => {
                                  e.target.style.display = 'none';
                                }}
                              />
                            )}
                            {!season.image && (
                              <div style={styles.seasonSelectPlaceholder}>📺</div>
                            )}
                            <div style={styles.seasonSelectInfo}>
                              <strong>{season.name || `Season ${season.number}`}</strong>
                              {season.episode_count && (
                                <p>{season.episode_count} episodes</p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </>
                  ) : (
                    <p style={styles.noSeasonsInfo}>No seasons found for this TV show.</p>
                  )}
                </div>
              )}
            </div>

            {/* Add Form */}
            <form onSubmit={handleSubmit} style={styles.form}>
              <h3 style={styles.formTitle}>
                {editingShow && editingSeason
                  ? `Edit Season ${editingSeason.season_number} of ${editingShow.title}`
                  : editingShow
                  ? `Edit ${editingShow.title}`
                  : 'Add TV Show Season'}
              </h3>
              
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
                  <label style={styles.label}>Season</label>
                  <input
                    type="number"
                    value={formData.season}
                    onChange={(e) => setFormData({ ...formData, season: parseInt(e.target.value) || 1 })}
                    min="1"
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
                    <option value="currently_watching">Currently Watching</option>
                    <option value="want_to_watch">Want to Watch</option>
                    <option value="watched">Watched</option>
                    <option value="dropped">Dropped</option>
                  </select>
                </div>
              </div>

              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Watched Date</label>
                  <input
                    type="date"
                    value={formData.watched_date}
                    onChange={(e) => setFormData({ ...formData, watched_date: e.target.value })}
                    style={styles.input}
                  />
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
                <label style={styles.label}>Show Thumbnail (Main Poster)</label>
                <div style={styles.thumbnailSection}>
                  <div style={styles.thumbnailOptions}>
                    <label style={styles.uploadLabel}>
                      <input
                        id="show-thumbnail-upload"
                        type="file"
                        accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
                        onChange={(e) => handleThumbnailUpload(e, false)}
                        style={styles.fileInput}
                      />
                      <span style={styles.uploadButton}>📁 Upload Image</span>
                    </label>
                    <span style={styles.thumbnailOr}>or</span>
                    <input
                      type="url"
                      value={formData.show_thumbnail_url && !formData.show_thumbnail_url.startsWith('data:') ? formData.show_thumbnail_url : ''}
                      onChange={(e) => {
                        setFormData({ ...formData, show_thumbnail_url: e.target.value });
                        if (formData.show_thumbnail_url && formData.show_thumbnail_url.startsWith('data:')) {
                          setUploadedThumbnail(null);
                        }
                      }}
                      placeholder="Enter image URL"
                      style={styles.input}
                    />
                  </div>
                  {(formData.show_thumbnail_url && !formData.show_thumbnail_url.startsWith('data:') && formData.show_thumbnail_url) && (
                    <div style={styles.thumbnailPreviewContainer}>
                      <img
                        src={formData.show_thumbnail_url}
                        alt="Show Thumbnail Preview"
                        style={styles.thumbnailPreview}
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                    </div>
                  )}
                </div>
              </div>

              <div style={styles.formGroup}>
                <label style={styles.label}>Season Thumbnail (Season-Specific Poster)</label>
                <p style={styles.helpText}>Each season can have its own unique thumbnail/poster</p>
                <div style={styles.thumbnailSection}>
                  <div style={styles.thumbnailOptions}>
                    <label style={styles.uploadLabel}>
                      <input
                        id="season-thumbnail-upload"
                        type="file"
                        accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
                        onChange={(e) => handleThumbnailUpload(e, true)}
                        style={styles.fileInput}
                      />
                      <span style={styles.uploadButton}>📁 Upload Image</span>
                    </label>
                    <span style={styles.thumbnailOr}>or</span>
                    <input
                      type="url"
                      value={formData.season_thumbnail_url && !formData.season_thumbnail_url.startsWith('data:') ? formData.season_thumbnail_url : ''}
                      onChange={(e) => {
                        setFormData({ ...formData, season_thumbnail_url: e.target.value });
                        if (formData.season_thumbnail_url && formData.season_thumbnail_url.startsWith('data:')) {
                          setUploadedThumbnail(null);
                        }
                      }}
                      placeholder="Enter image URL"
                      style={styles.input}
                    />
                  </div>
                  {(uploadedThumbnail || (formData.season_thumbnail_url && !formData.season_thumbnail_url.startsWith('data:') && formData.season_thumbnail_url)) && (
                    <div style={styles.thumbnailPreviewContainer}>
                      <img
                        src={uploadedThumbnail || formData.season_thumbnail_url}
                        alt="Season Thumbnail Preview"
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
                            setFormData({ ...formData, season_thumbnail_url: '' });
                            const fileInput = document.getElementById('season-thumbnail-upload');
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
                  {editingShow ? 'Update TV Show' : 'Add TV Show Season'}
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

        {/* TV Shows Display - different based on active tab */}
        {loading ? (
          <div style={styles.loading}>Loading TV shows...</div>
        ) : tvShows.length === 0 ? (
          <div style={styles.empty}>
            {activeTab === 'view' 
              ? 'No TV shows found. Switch to Manage tab to add TV shows!' 
              : activeTab === 'currently_watching'
              ? 'No currently watching shows. Add shows and mark them as "Currently Watching"!'
              : 'No TV shows found. Add your first TV show!'}
          </div>
        ) : (activeTab === 'view' || activeTab === 'currently_watching') ? (
          // View Mode / Currently Watching Mode - Clean browsing without edit/delete buttons
          <div style={styles.showsGrid}>
            {tvShows.map((show) => (
              <div key={show.id} style={styles.showCard}>
                {show.show_thumbnail_url && (
                  <img
                    src={show.show_thumbnail_url}
                    alt={show.title}
                    style={styles.thumbnail}
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                )}
                {!show.show_thumbnail_url && (
                  <div style={styles.thumbnailPlaceholder}>📺</div>
                )}
                <div style={styles.showInfo}>
                  <h3 style={styles.showTitle}>{show.title}</h3>
                  {show.year && <p style={styles.showYear}>Year: {show.year}</p>}
                  {show.genres && <p style={styles.showGenres}>Genres: {show.genres}</p>}
                  <p style={styles.seasonCount}>
                    {show.seasons?.length || 0} {show.seasons?.length === 1 ? 'season' : 'seasons'}
                  </p>
                  {show.overall_rating && (
                    <p style={styles.showRating}>⭐ {show.overall_rating}/10</p>
                  )}
                  {showNotes && show.seasons && show.seasons.length > 0 && (
                    <div style={styles.seasonsNotes}>
                      {show.seasons.map((season, idx) => (
                        season.notes && (
                          <p key={idx} style={styles.seasonNote}>
                            <strong>S{season.season_number}:</strong> {season.notes}
                          </p>
                        )
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : activeTab === 'details' ? (
          // Details Tab - Expandable details view
          <div style={styles.detailsSection}>
            <h2 style={styles.detailsTitle}>TV Show Details</h2>
            {tvShows.length === 0 ? (
              <div style={styles.empty}>No TV shows found. Add TV shows in the Manage TV Shows tab!</div>
            ) : (
              tvShows.map((show) => {
                const showSeasons = show.seasons || [];
                const seasonsByYear = groupSeasonsByYear(showSeasons);
                const yearKeys = Object.keys(seasonsByYear).sort((a, b) => {
                  if (a === 'Unknown') return 1;
                  if (b === 'Unknown') return -1;
                  return parseInt(b) - parseInt(a);
                });

                return (
                  <div key={show.id} style={styles.detailCard}>
                    <div
                      style={styles.detailHeader}
                      onClick={() => toggleExpanded(show.id)}
                    >
                      <div>
                        <strong>{show.title}</strong>
                        {show.year && <span style={styles.detailYear}> ({show.year})</span>}
                      </div>
                      <span style={styles.expandIcon}>
                        {expandedShows.has(show.id) ? '▼' : '▶'}
                      </span>
                    </div>
                    
                    {expandedShows.has(show.id) && (
                      <div style={styles.detailContent}>
                        <div style={styles.detailRow}>
                          {show.genres && (
                            <div style={styles.detailCol}>
                              <strong>Genres:</strong> {show.genres}
                            </div>
                          )}
                          {show.overall_rating && (
                            <div style={styles.detailCol}>
                              <strong>Overall Rating:</strong> {show.overall_rating}/10
                            </div>
                          )}
                          <div style={styles.detailCol}>
                            <strong>Status:</strong> {show.status || 'N/A'}
                          </div>
                        </div>
                        {showSeasons.length > 0 && (
                          <div style={styles.seasonsSection}>
                            <h3 style={styles.seasonsTitle}>Seasons</h3>
                            {yearKeys.map((year) => {
                              const yearSeasons = seasonsByYear[year]
                                .sort((a, b) => a.season_number - b.season_number);
                              
                              return (
                                <div key={year} style={styles.yearGroup}>
                                  <h4 style={styles.yearTitle}>{year}</h4>
                                  <div style={styles.seasonsGrid}>
                                    {yearSeasons.map((season) => (
                                      <div key={season.id} style={styles.seasonCard}>
                                        {season.season_thumbnail_url && (
                                          <img
                                            src={season.season_thumbnail_url}
                                            alt={`Season ${season.season_number}`}
                                            style={styles.seasonThumbnail}
                                            onError={(e) => {
                                              e.target.style.display = 'none';
                                            }}
                                          />
                                        )}
                                        {!season.season_thumbnail_url && (
                                          <div style={styles.seasonPlaceholder}>
                                            S{season.season_number}
                                          </div>
                                        )}
                                        <div style={styles.seasonInfo}>
                                          <strong>S{season.season_number}</strong>
                                          {season.watched_date && (
                                            <p style={styles.seasonDate}>
                                              {new Date(season.watched_date).toLocaleDateString()}
                                            </p>
                                          )}
                                          {season.rating && (
                                            <p style={styles.seasonRating}>⭐ {season.rating}/10</p>
                                          )}
                                          {season.notes && (
                                            <p style={styles.seasonNotesText}>{season.notes}</p>
                                          )}
                                          <button
                                            onClick={() => handleEdit(show, season)}
                                            style={styles.editSeasonButton}
                                            title="Edit this season"
                                          >
                                            Edit Season
                                          </button>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        ) : (
          // Manage Mode - With edit/delete buttons
          <div style={styles.showsGrid}>
            {tvShows.map((show) => (
              <div key={show.id} style={styles.showCard}>
                {show.show_thumbnail_url && (
                  <img
                    src={show.show_thumbnail_url}
                    alt={show.title}
                    style={styles.thumbnail}
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                )}
                {!show.show_thumbnail_url && (
                  <div style={styles.thumbnailPlaceholder}>📺</div>
                )}
                <div style={styles.showInfo}>
                  <h3 style={styles.showTitle}>{show.title}</h3>
                  {show.year && <p style={styles.showYear}>Year: {show.year}</p>}
                  {show.genres && <p style={styles.showGenres}>Genres: {show.genres}</p>}
                  <p style={styles.seasonCount}>
                    {show.seasons?.length || 0} {show.seasons?.length === 1 ? 'season' : 'seasons'}
                  </p>
                  {show.overall_rating && (
                    <p style={styles.showRating}>⭐ {show.overall_rating}/10</p>
                  )}
                  <div style={styles.statusInput}>
                    <input
                      type="text"
                      value={show.status || 'watched'}
                      readOnly
                      style={styles.statusField}
                    />
                  </div>
                  <div style={styles.showActions}>
                    <button
                      onClick={() => handleEdit(show)}
                      style={styles.editButton}
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteShow(show.id)}
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
    marginBottom: '1.5rem',
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
  selectedShow: {
    marginTop: '1rem',
    padding: '1rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '4px',
  },
  selectedShowHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
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
  seasonsSelectTitle: {
    marginBottom: '1rem',
  },
  seasonsSelectGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
    gap: '1rem',
  },
  seasonSelectCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: '4px',
    padding: '0.5rem',
    cursor: 'pointer',
    transition: 'all 0.2s',
    border: '2px solid transparent',
  },
  seasonSelectCardActive: {
    borderColor: '#007bff',
    backgroundColor: '#e7f3ff',
  },
  seasonSelectThumbnail: {
    width: '100%',
    height: '200px',
    objectFit: 'cover',
    borderRadius: '4px',
    marginBottom: '0.5rem',
  },
  seasonSelectPlaceholder: {
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
  seasonSelectInfo: {
    textAlign: 'center',
    fontSize: '0.9rem',
  },
  noSeasonsInfo: {
    color: '#666',
    fontStyle: 'italic',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    marginTop: '2rem',
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
  helpText: {
    fontSize: '0.85rem',
    color: '#666',
    marginTop: '-0.5rem',
    marginBottom: '0.5rem',
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
  editSeasonButton: {
    marginTop: '0.5rem',
    padding: '0.25rem 0.5rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.8rem',
    width: '100%',
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
  showsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(min(250px, 100%), 1fr))',
    gap: 'clamp(1rem, 2vw, 1.5rem)',
    marginBottom: '3rem',
    width: '100%',
  },
  showCard: {
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
  showInfo: {
    padding: '1rem',
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },
  showTitle: {
    margin: '0 0 0.5rem 0',
    fontSize: '1.1rem',
    color: '#333',
  },
  showYear: {
    margin: '0 0 0.5rem 0',
    color: '#666',
    fontSize: '0.9rem',
  },
  showGenres: {
    margin: '0 0 0.5rem 0',
    color: '#666',
    fontSize: '0.9rem',
  },
  seasonCount: {
    margin: '0 0 0.5rem 0',
    color: '#666',
    fontSize: '0.9rem',
  },
  showRating: {
    margin: '0 0 0.5rem 0',
    color: '#333',
    fontWeight: '500',
  },
  badge: {
    display: 'inline-block',
    padding: '0.25rem 0.5rem',
    backgroundColor: '#e9ecef',
    color: '#495057',
    borderRadius: '4px',
    fontSize: '0.8rem',
    marginBottom: '0.5rem',
  },
  seasonsNotes: {
    marginTop: '0.5rem',
  },
  seasonNote: {
    margin: '0.25rem 0',
    fontSize: '0.85rem',
    color: '#666',
  },
  statusInput: {
    marginBottom: '0.5rem',
  },
  statusField: {
    width: '100%',
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '0.9rem',
    backgroundColor: '#f8f9fa',
    color: '#666',
  },
  showActions: {
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
  detailYear: {
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
  seasonsSection: {
    marginTop: '1rem',
  },
  seasonsTitle: {
    marginBottom: '1rem',
    fontSize: '1.1rem',
  },
  yearGroup: {
    marginBottom: '2rem',
  },
  yearTitle: {
    marginBottom: '0.5rem',
    fontSize: '1rem',
    color: '#333',
  },
  seasonsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
    gap: '1rem',
  },
  seasonCard: {
    position: 'relative',
    backgroundColor: '#f8f9fa',
    borderRadius: '4px',
    padding: '0.5rem',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  seasonThumbnail: {
    width: '100%',
    maxHeight: '150px',
    objectFit: 'contain',
    borderRadius: '4px',
    marginBottom: '0.5rem',
  },
  seasonPlaceholder: {
    width: '100%',
    height: '100px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#e9ecef',
    borderRadius: '4px',
    fontSize: '1.5rem',
    marginBottom: '0.5rem',
  },
  seasonInfo: {
    width: '100%',
    textAlign: 'center',
    fontSize: '0.9rem',
  },
  seasonDate: {
    margin: '0.25rem 0',
    fontSize: '0.8rem',
    color: '#666',
  },
  seasonRating: {
    margin: '0.25rem 0',
    fontSize: '0.8rem',
    color: '#333',
  },
  seasonNotesText: {
    margin: '0.25rem 0',
    fontSize: '0.8rem',
    color: '#666',
    fontStyle: 'italic',
  },
};
