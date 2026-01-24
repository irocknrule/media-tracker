import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { bookService } from '../services/bookService';
import { searchService } from '../services/searchService';
import { getErrorMessage } from '../utils/errorHandler';

export default function Books() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [yearFilter, setYearFilter] = useState('');
  const [activeTab, setActiveTab] = useState('view');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingBook, setEditingBook] = useState(null);
  const [expandedBooks, setExpandedBooks] = useState(new Set());
  const [uploadedThumbnail, setUploadedThumbnail] = useState(null);
  const [showNotes, setShowNotes] = useState(true);
  const [showWantToReadOnly, setShowWantToReadOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedBook, setSelectedBook] = useState(null);
  const [searching, setSearching] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    author: '',
    finished_date: '',
    status: 'finished',
    rating: 5.0,
    notes: '',
    thumbnail_url: '',
    pages: '',
  });

  useEffect(() => {
    loadBooks();
  }, [yearFilter, showWantToReadOnly, activeTab]);

  const loadBooks = async () => {
    try {
      setLoading(true);
      setError('');
      const params = yearFilter ? { year: parseInt(yearFilter) } : {};
      const data = await bookService.getAll(params);
      
      let filteredData = data || [];
      
      if (activeTab === 'view') {
        filteredData = filteredData.filter(book => book.status === 'finished');
      }
      
      if (activeTab === 'currently_reading') {
        filteredData = filteredData.filter(book => book.status === 'currently_reading');
      }
      
      if (activeTab === 'manage' && showWantToReadOnly) {
        filteredData = filteredData.filter(book => book.status === 'want_to_read');
      }
      
      setBooks(filteredData);
    } catch (err) {
      console.error('Error loading books:', err);
      const errorMessage = getErrorMessage(err) || 'Failed to load books';
      setError(errorMessage);
      setBooks([]);
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
      const results = await searchService.searchBooks(searchQuery);
      setSearchResults(results);
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError('Failed to search books: ' + errorMessage);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleSelectBook = (book) => {
    setSelectedBook(book);
    setFormData({
      ...formData,
      title: book.title || '',
      author: book.author || '',
      thumbnail_url: book.thumbnail || '',
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
      const bookData = {
        ...formData,
        pages: formData.pages ? parseInt(formData.pages) : null,
        rating: formData.rating ? parseFloat(formData.rating) : null,
        finished_date: formData.finished_date || null,
      };
      
      if (editingBook) {
        await bookService.update(editingBook.id, bookData);
        setEditingBook(null);
      } else {
        await bookService.create(bookData);
      }
      
      resetForm();
      loadBooks();
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError((editingBook ? 'Failed to update book: ' : 'Failed to add book: ') + errorMessage);
    }
  };

  const handleEdit = (book) => {
    setEditingBook(book);
    setUploadedThumbnail(book.thumbnail_url?.startsWith('data:') ? book.thumbnail_url : null);
    setSelectedBook(null);
    setFormData({
      title: book.title || '',
      author: book.author || '',
      finished_date: book.finished_date || '',
      status: book.status || 'finished',
      rating: book.rating || 5.0,
      notes: book.notes || '',
      thumbnail_url: book.thumbnail_url || '',
      pages: book.pages ? book.pages.toString() : '',
    });
    setShowAddForm(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this book?')) {
      return;
    }
    
    try {
      await bookService.delete(id);
      loadBooks();
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError('Failed to delete book: ' + errorMessage);
    }
  };

  const resetForm = () => {
    setShowAddForm(false);
    setEditingBook(null);
    setUploadedThumbnail(null);
    setSelectedBook(null);
    setSearchQuery('');
    setSearchResults([]);
    setFormData({
      title: '',
      author: '',
      finished_date: '',
      status: 'finished',
      rating: 5.0,
      notes: '',
      thumbnail_url: '',
      pages: '',
    });
    const fileInput = document.getElementById('thumbnail-upload');
    if (fileInput) {
      fileInput.value = '';
    }
  };

  const toggleExpanded = (bookId) => {
    const newExpanded = new Set(expandedBooks);
    if (newExpanded.has(bookId)) {
      newExpanded.delete(bookId);
    } else {
      newExpanded.add(bookId);
    }
    setExpandedBooks(newExpanded);
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
          <h1 style={styles.title}>📖 Books</h1>
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
            📖 View Books
          </button>
          <button
            onClick={() => {
              setActiveTab('currently_reading');
              setShowAddForm(false);
              resetForm();
            }}
            style={activeTab === 'currently_reading' ? styles.activeTab : styles.tab}
          >
            📚 Currently Reading
          </button>
          <button
            onClick={() => {
              setActiveTab('manage');
            }}
            style={activeTab === 'manage' ? styles.activeTab : styles.tab}
          >
            ⚙️ Manage Books
          </button>
          <button
            onClick={() => {
              setActiveTab('details');
            }}
            style={activeTab === 'details' ? styles.activeTab : styles.tab}
          >
            📋 Book Details
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
            {activeTab === 'manage' && (
              <label style={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={showWantToReadOnly}
                  onChange={(e) => setShowWantToReadOnly(e.target.checked)}
                  style={styles.checkbox}
                />
                Want to Read
              </label>
            )}
            
            {(activeTab === 'view' || activeTab === 'currently_reading') && (
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
                {showAddForm ? 'Cancel' : '+ Add Book'}
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
              {editingBook ? 'Edit Book' : 'Add New Book'}
            </h2>

            {/* Search */}
            {!editingBook && (
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
                    placeholder="🔍 Search for a book..."
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

                {searchResults.length > 0 && !selectedBook && (
                  <div style={styles.searchResults}>
                    <h3>Search Results</h3>
                    <div style={styles.resultsGrid}>
                      {searchResults.map((result, idx) => (
                        <div
                          key={idx}
                          style={styles.resultCard}
                          onClick={() => handleSelectBook(result)}
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
                            <div style={styles.resultPlaceholder}>📖</div>
                          )}
                          <div style={styles.resultInfo}>
                            <strong>{result.title}</strong>
                            {result.author && <p>by {result.author}</p>}
                            {result.year && <p>{result.year}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedBook && (
                  <div style={styles.selectedBook}>
                    <div style={styles.selectedBookHeader}>
                      <span>✅ Selected: <strong>{selectedBook.title}</strong></span>
                      <button
                        onClick={() => {
                          setSelectedBook(null);
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
                  <label style={styles.label}>Author</label>
                  <input
                    type="text"
                    value={formData.author}
                    onChange={(e) => setFormData({ ...formData, author: e.target.value })}
                    style={styles.input}
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Pages</label>
                  <input
                    type="number"
                    value={formData.pages}
                    onChange={(e) => setFormData({ ...formData, pages: e.target.value })}
                    min="1"
                    style={styles.input}
                  />
                </div>
              </div>
              
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Finished Date</label>
                  <input
                    type="date"
                    value={formData.finished_date}
                    onChange={(e) => setFormData({ ...formData, finished_date: e.target.value })}
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
                    <option value="finished">Finished</option>
                    <option value="currently_reading">Currently Reading</option>
                    <option value="want_to_read">Want to Read</option>
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
                  {editingBook ? 'Update Book' : 'Add Book'}
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
          <div style={styles.loading}>Loading books...</div>
        ) : books.length === 0 ? (
          <div style={styles.empty}>
            {activeTab === 'view' 
              ? 'No books found. Switch to Manage tab to add books!' 
              : activeTab === 'currently_reading'
              ? 'No currently reading books found. Switch to Manage tab to add books!'
              : 'No books found. Add your first book!'}
          </div>
        ) : (activeTab === 'view' || activeTab === 'currently_reading') ? (
          <div style={styles.booksGrid}>
            {books.map((book) => (
              <div key={book.id} style={styles.bookCard}>
                {book.thumbnail_url && (
                  <img
                    src={book.thumbnail_url}
                    alt={book.title}
                    style={styles.thumbnail}
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                )}
                {!book.thumbnail_url && (
                  <div style={styles.thumbnailPlaceholder}>📖</div>
                )}
                <div style={styles.bookInfo}>
                  <h3 style={styles.bookTitle}>{book.title}</h3>
                  {book.author && <p style={styles.bookAuthor}>by {book.author}</p>}
                  {book.pages && <p style={styles.bookPages}>{book.pages} pages</p>}
                  {book.rating && (
                    <p style={styles.bookRating}>⭐ {book.rating}/10</p>
                  )}
                  {book.finished_date && (
                    <p style={styles.bookDate}>
                      Finished: {new Date(book.finished_date).toLocaleDateString()}
                    </p>
                  )}
                  {showNotes && book.notes && (
                    <p style={styles.bookNotes}>{book.notes}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : activeTab === 'details' ? (
          <div style={styles.detailsSection}>
            <h2 style={styles.detailsTitle}>Book Details</h2>
            {books.length === 0 ? (
              <div style={styles.empty}>No books found. Add books in the Manage Books tab!</div>
            ) : (
              books.map((book) => (
                <div key={book.id} style={styles.detailCard}>
                  <div
                    style={styles.detailHeader}
                    onClick={() => toggleExpanded(book.id)}
                  >
                    <div>
                      <strong>{book.title}</strong>
                      {book.author && <span style={styles.detailAuthor}> by {book.author}</span>}
                      {book.finished_date && (
                        <span style={styles.detailDate}>
                          {' - '}
                          {new Date(book.finished_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                    <span style={styles.expandIcon}>
                      {expandedBooks.has(book.id) ? '▼' : '▶'}
                    </span>
                  </div>
                  
                  {expandedBooks.has(book.id) && (
                    <div style={styles.detailContent}>
                      <div style={styles.detailRow}>
                        <div style={styles.detailCol}>
                          <strong>Finished:</strong> {book.finished_date ? new Date(book.finished_date).toLocaleDateString() : 'N/A'}
                        </div>
                        <div style={styles.detailCol}>
                          <strong>Pages:</strong> {book.pages || 'N/A'}
                        </div>
                        <div style={styles.detailCol}>
                          <strong>Rating:</strong> {book.rating ? `${book.rating}/10` : 'N/A'}
                        </div>
                        <div style={styles.detailCol}>
                          <strong>Status:</strong> {book.status || 'N/A'}
                        </div>
                      </div>
                      {book.notes && (
                        <div style={styles.detailNotes}>
                          <strong>Notes:</strong> {book.notes}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        ) : (
          <div style={styles.booksGrid}>
            {books.map((book) => (
              <div key={book.id} style={styles.bookCard}>
                {book.thumbnail_url && (
                  <img
                    src={book.thumbnail_url}
                    alt={book.title}
                    style={styles.thumbnail}
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                )}
                {!book.thumbnail_url && (
                  <div style={styles.thumbnailPlaceholder}>📖</div>
                )}
                <div style={styles.bookInfo}>
                  <h3 style={styles.bookTitle}>{book.title}</h3>
                  {book.author && <p style={styles.bookAuthor}>by {book.author}</p>}
                  {book.pages && <p style={styles.bookPages}>{book.pages} pages</p>}
                  {book.rating && (
                    <p style={styles.bookRating}>⭐ {book.rating}/10</p>
                  )}
                  {book.finished_date && (
                    <p style={styles.bookDate}>
                      Finished: {new Date(book.finished_date).toLocaleDateString()}
                    </p>
                  )}
                  <div style={styles.bookActions}>
                    <button
                      onClick={() => handleEdit(book)}
                      style={styles.editButton}
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(book.id)}
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
  selectedBook: {
    marginTop: '1rem',
    padding: '1rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '4px',
  },
  selectedBookHeader: {
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
  booksGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(min(250px, 100%), 1fr))',
    gap: 'clamp(1rem, 2vw, 1.5rem)',
    marginBottom: '3rem',
    width: '100%',
  },
  bookCard: {
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
  bookInfo: {
    padding: '1rem',
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },
  bookTitle: {
    margin: '0 0 0.5rem 0',
    fontSize: '1.1rem',
    color: '#333',
  },
  bookAuthor: {
    margin: '0 0 0.5rem 0',
    color: '#666',
    fontSize: '0.9rem',
  },
  bookPages: {
    margin: '0 0 0.5rem 0',
    color: '#666',
    fontSize: '0.9rem',
  },
  bookRating: {
    margin: '0 0 0.5rem 0',
    color: '#333',
    fontWeight: '500',
  },
  bookDate: {
    margin: '0 0 0.5rem 0',
    color: '#666',
    fontSize: '0.9rem',
  },
  bookNotes: {
    margin: '0.5rem 0 0 0',
    color: '#666',
    fontSize: '0.85rem',
    fontStyle: 'italic',
  },
  bookActions: {
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
  detailAuthor: {
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
