import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { movieService } from '../services/movieService';
import { movieDetailsService } from '../services/movieDetailsService';
import { getErrorMessage } from '../utils/errorHandler';

export default function Movies() {
  const { user, logout } = useAuth();
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [yearFilter, setYearFilter] = useState('');
  const [activeTab, setActiveTab] = useState('view'); // 'view' or 'manage'
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingMovie, setEditingMovie] = useState(null);
  const [expandedMovies, setExpandedMovies] = useState(new Set());
  const [uploadedThumbnail, setUploadedThumbnail] = useState(null);
  const [movieDetails, setMovieDetails] = useState(null);
  const [fetchingDetails, setFetchingDetails] = useState(false);
  const [showNotes, setShowNotes] = useState(true);
  const [showWantToWatchOnly, setShowWantToWatchOnly] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    year: new Date().getFullYear().toString(),
    watched_date: '',
    status: 'watched',
    rating: 5.0,
    notes: '',
    thumbnail_url: '',
  });

  useEffect(() => {
    loadMovies();
  }, [yearFilter, showWantToWatchOnly]);

  const loadMovies = async () => {
    try {
      setLoading(true);
      setError('');
      const params = yearFilter ? { year: parseInt(yearFilter) } : {};
      const data = await movieService.getAll(params);
      
      // Filter by status if "Want to watch only" is enabled
      let filteredData = data || [];
      if (showWantToWatchOnly) {
        filteredData = filteredData.filter(movie => movie.status === 'want_to_watch');
      }
      
      setMovies(filteredData);
    } catch (err) {
      console.error('Error loading movies:', err);
      const errorMessage = getErrorMessage(err) || 'Failed to load movies';
      setError(errorMessage);
      setMovies([]);
    } finally {
      setLoading(false);
    }
  };


  const handleFetchDetails = async () => {
    if (!formData.title.trim()) {
      setError('Please enter a movie title first');
      return;
    }

    setFetchingDetails(true);
    setError('');
    try {
      const details = await movieDetailsService.getDetails(
        formData.title,
        formData.year || null
      );
      
      if (details.error) {
        setError(details.error);
        setMovieDetails(null);
      } else {
        setMovieDetails(details);
        // Auto-fill form with fetched data
        setFormData({
          ...formData,
          year: details.year ? details.year.split('–')[0] : formData.year, // Handle year ranges
          thumbnail_url: details.poster && details.poster !== 'N/A' ? details.poster : formData.thumbnail_url,
        });
      }
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError('Failed to fetch movie details: ' + errorMessage);
      setMovieDetails(null);
    } finally {
      setFetchingDetails(false);
    }
  };

  const handleThumbnailUpload = (event) => {
    const file = event.target.files[0];
    if (!file) {
      setUploadedThumbnail(null);
      setFormData({ ...formData, thumbnail_url: '' });
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
      const movieData = {
        ...formData,
        year: formData.year ? parseInt(formData.year) : null,
        rating: formData.rating ? parseFloat(formData.rating) : null,
        watched_date: formData.watched_date || null,
      };
      
      if (editingMovie) {
        await movieService.update(editingMovie.id, movieData);
        setEditingMovie(null);
      } else {
        await movieService.create(movieData);
      }
      
      resetForm();
      loadMovies();
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError((editingMovie ? 'Failed to update movie: ' : 'Failed to add movie: ') + errorMessage);
    }
  };

  const handleEdit = (movie) => {
    setEditingMovie(movie);
    setUploadedThumbnail(movie.thumbnail_url?.startsWith('data:') ? movie.thumbnail_url : null);
    setMovieDetails(null); // Clear details when editing
    setFormData({
      title: movie.title || '',
      year: movie.year ? movie.year.toString() : '',
      watched_date: movie.watched_date || '',
      status: movie.status || 'watched',
      rating: movie.rating || 5.0,
      notes: movie.notes || '',
      thumbnail_url: movie.thumbnail_url || '',
    });
    setShowAddForm(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this movie?')) {
      return;
    }
    
    try {
      await movieService.delete(id);
      loadMovies();
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError('Failed to delete movie: ' + errorMessage);
    }
  };

  const resetForm = () => {
    setShowAddForm(false);
    setEditingMovie(null);
    setUploadedThumbnail(null);
    setMovieDetails(null);
    setFormData({
      title: '',
      year: new Date().getFullYear().toString(),
      watched_date: '',
      status: 'watched',
      rating: 5.0,
      notes: '',
      thumbnail_url: '',
    });
    // Reset file input
    const fileInput = document.getElementById('thumbnail-upload');
    if (fileInput) {
      fileInput.value = '';
    }
  };

  const toggleExpanded = (movieId) => {
    const newExpanded = new Set(expandedMovies);
    if (newExpanded.has(movieId)) {
      newExpanded.delete(movieId);
    } else {
      newExpanded.add(movieId);
    }
    setExpandedMovies(newExpanded);
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
        <h1 style={styles.title}>🎬 Movies</h1>
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
            📺 View Movies
          </button>
          <button
            onClick={() => {
              setActiveTab('manage');
            }}
            style={activeTab === 'manage' ? styles.activeTab : styles.tab}
          >
            ⚙️ Manage Movies
          </button>
          <button
            onClick={() => {
              setActiveTab('details');
            }}
            style={activeTab === 'details' ? styles.activeTab : styles.tab}
          >
            📋 Movie Details
          </button>
        </div>

        {/* Year Filter and Options - shown in both tabs */}
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
                  checked={showWantToWatchOnly}
                  onChange={(e) => setShowWantToWatchOnly(e.target.checked)}
                  style={styles.checkbox}
                />
                In My Queue
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
                {showAddForm ? 'Cancel' : '+ Add Movie'}
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
              {editingMovie ? 'Edit Movie' : 'Add New Movie'}
            </h2>
            <p style={styles.formSubtitle}>
              Enter movie details manually and upload a custom thumbnail
            </p>

            <form onSubmit={handleSubmit} style={styles.form}>
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Title *</label>
                  <div style={styles.titleInputGroup}>
                    <input
                      type="text"
                      value={formData.title}
                      onChange={(e) => {
                        setFormData({ ...formData, title: e.target.value });
                        setMovieDetails(null); // Clear details when title changes
                      }}
                      required
                      style={styles.input}
                    />
                    <button
                      type="button"
                      onClick={handleFetchDetails}
                      disabled={fetchingDetails || !formData.title.trim()}
                      style={styles.fetchButton}
                      title="Fetch movie details from web"
                    >
                      {fetchingDetails ? '⏳' : '🌐'} {fetchingDetails ? 'Fetching...' : 'Fetch Details'}
                    </button>
                  </div>
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Year</label>
                  <input
                    type="number"
                    value={formData.year || currentYear}
                    onChange={(e) => setFormData({ ...formData, year: e.target.value })}
                    min="1900"
                    max={currentYear + 10}
                    style={styles.input}
                  />
                </div>
              </div>

              {/* Movie Details Display */}
              {movieDetails && !movieDetails.error && (
                <div style={styles.movieDetailsCard}>
                  <div style={styles.movieDetailsHeader}>
                    <h3 style={styles.movieDetailsTitle}>Movie Details</h3>
                    <button
                      type="button"
                      onClick={() => setMovieDetails(null)}
                      style={styles.closeDetailsButton}
                    >
                      ×
                    </button>
                  </div>
                  <div style={styles.movieDetailsContent}>
                    {movieDetails.poster && movieDetails.poster !== 'N/A' && (
                      <div style={styles.movieDetailsPoster}>
                        <img
                          src={movieDetails.poster}
                          alt={movieDetails.title}
                          style={styles.detailsPosterImage}
                        />
                      </div>
                    )}
                    <div style={styles.movieDetailsInfo}>
                      <div style={styles.detailsRow}>
                        <strong>Director:</strong> {movieDetails.director || 'N/A'}
                      </div>
                      <div style={styles.detailsRow}>
                        <strong>Release Year:</strong> {movieDetails.year || 'N/A'}
                      </div>
                      <div style={styles.detailsRow}>
                        <strong>Runtime:</strong> {movieDetails.runtime || 'N/A'}
                      </div>
                      <div style={styles.detailsRow}>
                        <strong>Rating:</strong> {movieDetails.rated || 'N/A'}
                      </div>
                      <div style={styles.detailsRow}>
                        <strong>Genres:</strong> {movieDetails.genres?.join(', ') || 'N/A'}
                      </div>
                      {movieDetails.ratings && movieDetails.ratings.length > 0 && (
                        <div style={styles.detailsRow}>
                          <strong>Scores:</strong>
                          <div style={styles.ratingsList}>
                            {movieDetails.ratings.map((rating, idx) => (
                              <span key={idx} style={styles.ratingBadge}>
                                {rating.source}: {rating.value}
                              </span>
                            ))}
                            {movieDetails.imdb_rating && (
                              <span style={styles.ratingBadge}>
                                IMDb: {movieDetails.imdb_rating}/10
                              </span>
                            )}
                            {movieDetails.metascore && (
                              <span style={styles.ratingBadge}>
                                Metascore: {movieDetails.metascore}
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                      {movieDetails.plot && (
                        <div style={styles.detailsRow}>
                          <strong>Synopsis:</strong>
                          <p style={styles.plotText}>{movieDetails.plot}</p>
                        </div>
                      )}
                      {movieDetails.actors && movieDetails.actors.length > 0 && (
                        <div style={styles.detailsRow}>
                          <strong>Cast:</strong> {movieDetails.actors.join(', ')}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
              
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
                  <label style={styles.label}>Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    style={styles.input}
                  >
                    <option value="watched">Watched</option>
                    <option value="currently_watching">Currently Watching</option>
                    <option value="want_to_watch">Want to Watch</option>
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
                <label style={styles.label}>Thumbnail</label>
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
                        alt="Thumbnail Preview"
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
                  {editingMovie ? 'Update Movie' : 'Add Movie'}
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

        {/* Movies Display - different based on active tab */}
        {loading ? (
          <div style={styles.loading}>Loading movies...</div>
        ) : movies.length === 0 ? (
          <div style={styles.empty}>
            {activeTab === 'view' 
              ? 'No movies found. Switch to Manage tab to add movies!' 
              : 'No movies found. Add your first movie!'}
          </div>
        ) : activeTab === 'view' ? (
          // View Mode - Clean browsing without edit/delete buttons
          <div style={styles.moviesGrid}>
            {movies.map((movie) => (
              <div key={movie.id} style={styles.movieCard}>
                {movie.thumbnail_url && (
                  <img
                    src={movie.thumbnail_url}
                    alt={movie.title}
                    style={styles.thumbnail}
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                )}
                {!movie.thumbnail_url && (
                  <div style={styles.thumbnailPlaceholder}>🎬</div>
                )}
                <div style={styles.movieInfo}>
                  <h3 style={styles.movieTitle}>{movie.title}</h3>
                  {movie.year && <p style={styles.movieYear}>{movie.year}</p>}
                  {movie.rating && (
                    <p style={styles.movieRating}>⭐ {movie.rating}/10</p>
                  )}
                  {movie.watched_date && (
                    <p style={styles.movieDate}>
                      Watched: {new Date(movie.watched_date).toLocaleDateString()}
                    </p>
                  )}
                  {movie.status && (
                    <span style={styles.badge}>{movie.status}</span>
                  )}
                  {showNotes && movie.notes && (
                    <p style={styles.movieNotes}>{movie.notes}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : activeTab === 'details' ? (
          // Details Tab - Expandable details view
          <div style={styles.detailsSection}>
            <h2 style={styles.detailsTitle}>Movie Details</h2>
            {movies.length === 0 ? (
              <div style={styles.empty}>No movies found. Add movies in the Manage Movies tab!</div>
            ) : (
              movies.map((movie) => (
                <div key={movie.id} style={styles.detailCard}>
                  <div
                    style={styles.detailHeader}
                    onClick={() => toggleExpanded(movie.id)}
                  >
                    <div>
                      <strong>{movie.title}</strong>
                      {movie.year && <span style={styles.detailYear}> ({movie.year})</span>}
                      {movie.watched_date && (
                        <span style={styles.detailDate}>
                          {' - '}
                          {new Date(movie.watched_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                    <span style={styles.expandIcon}>
                      {expandedMovies.has(movie.id) ? '▼' : '▶'}
                    </span>
                  </div>
                  
                  {expandedMovies.has(movie.id) && (
                    <div style={styles.detailContent}>
                      <div style={styles.detailRow}>
                        <div style={styles.detailCol}>
                          <strong>Watched:</strong> {movie.watched_date ? new Date(movie.watched_date).toLocaleDateString() : 'N/A'}
                        </div>
                        <div style={styles.detailCol}>
                          <strong>Rating:</strong> {movie.rating ? `${movie.rating}/10` : 'N/A'}
                        </div>
                        <div style={styles.detailCol}>
                          <strong>Status:</strong> {movie.status || 'N/A'}
                        </div>
                      </div>
                      {movie.notes && (
                        <div style={styles.detailNotes}>
                          <strong>Notes:</strong> {movie.notes}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        ) : (
          // Manage Mode - With edit/delete buttons
          <>
            <div style={styles.moviesGrid}>
              {movies.map((movie) => (
                <div key={movie.id} style={styles.movieCard}>
                  {movie.thumbnail_url && (
                    <img
                      src={movie.thumbnail_url}
                      alt={movie.title}
                      style={styles.thumbnail}
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  )}
                  {!movie.thumbnail_url && (
                    <div style={styles.thumbnailPlaceholder}>🎬</div>
                  )}
                  <div style={styles.movieInfo}>
                    <h3 style={styles.movieTitle}>{movie.title}</h3>
                    {movie.year && <p style={styles.movieYear}>{movie.year}</p>}
                    {movie.rating && (
                      <p style={styles.movieRating}>⭐ {movie.rating}/10</p>
                    )}
                    {movie.watched_date && (
                      <p style={styles.movieDate}>
                        Watched: {new Date(movie.watched_date).toLocaleDateString()}
                      </p>
                    )}
                    {movie.status && (
                      <span style={styles.badge}>{movie.status}</span>
                    )}
                    <div style={styles.movieActions}>
                      <button
                        onClick={() => handleEdit(movie)}
                        style={styles.editButton}
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(movie.id)}
                        style={styles.deleteButton}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

          </>
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
  formSubtitle: {
    marginTop: 0,
    marginBottom: '1.5rem',
    color: '#666',
    fontSize: '0.9rem',
  },
  titleInputGroup: {
    display: 'flex',
    gap: '0.5rem',
  },
  fetchButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#17a2b8',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    whiteSpace: 'nowrap',
    flexShrink: 0,
  },
  movieDetailsCard: {
    marginBottom: '1.5rem',
    padding: '1.5rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '8px',
    border: '1px solid #dee2e6',
  },
  movieDetailsHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  movieDetailsTitle: {
    margin: 0,
    fontSize: '1.2rem',
    color: '#333',
  },
  closeDetailsButton: {
    background: 'none',
    border: 'none',
    fontSize: '1.5rem',
    color: '#666',
    cursor: 'pointer',
    padding: '0',
    width: '30px',
    height: '30px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '4px',
  },
  movieDetailsContent: {
    display: 'flex',
    gap: '1.5rem',
    flexWrap: 'wrap',
  },
  movieDetailsPoster: {
    flexShrink: 0,
  },
  detailsPosterImage: {
    maxWidth: '200px',
    maxHeight: '300px',
    borderRadius: '4px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  movieDetailsInfo: {
    flex: 1,
    minWidth: '250px',
  },
  detailsRow: {
    marginBottom: '0.75rem',
    lineHeight: '1.6',
  },
  ratingsList: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.5rem',
    marginTop: '0.25rem',
  },
  ratingBadge: {
    display: 'inline-block',
    padding: '0.25rem 0.5rem',
    backgroundColor: '#e9ecef',
    color: '#495057',
    borderRadius: '4px',
    fontSize: '0.85rem',
  },
  plotText: {
    margin: '0.5rem 0 0 0',
    color: '#555',
    lineHeight: '1.6',
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
  moviesGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(min(250px, 100%), 1fr))',
    gap: 'clamp(1rem, 2vw, 1.5rem)',
    marginBottom: '3rem',
    width: '100%',
  },
  movieCard: {
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
  movieInfo: {
    padding: '1rem',
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },
  movieTitle: {
    margin: '0 0 0.5rem 0',
    fontSize: '1.1rem',
    color: '#333',
  },
  movieYear: {
    margin: '0 0 0.5rem 0',
    color: '#666',
    fontSize: '0.9rem',
  },
  movieRating: {
    margin: '0 0 0.5rem 0',
    color: '#333',
    fontWeight: '500',
  },
  movieDate: {
    margin: '0 0 0.5rem 0',
    color: '#666',
    fontSize: '0.9rem',
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
  movieActions: {
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
