import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { tvShowService } from '../services/tvShowService';
import { movieService } from '../services/movieService';

export default function Home() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    movies: 0,
    tvShows: 0,
    currentlyWatching: 0,
  });
  const [loading, setLoading] = useState(true);
  const [hoveredCard, setHoveredCard] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const [movies, tvShows] = await Promise.all([
        movieService.getAll(),
        tvShowService.getAll(),
      ]);

      const currentlyWatching = tvShows.filter(
        (show) => show.status === 'currently_watching'
      ).length;

      setStats({
        movies: movies?.length || 0,
        tvShows: tvShows?.length || 0,
        currentlyWatching,
      });
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
    }
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
        <h1 style={styles.title}>📚 Personal Tracker</h1>
        <div style={styles.headerActions}>
          <span style={styles.userInfo}>Welcome, {user?.username || 'User'}</span>
          <button onClick={logout} style={styles.logoutButton}>
            Logout
          </button>
        </div>
      </header>

      <div style={styles.content}>
        {/* Quick Stats */}
        {!loading && (
          <div style={styles.statsSection}>
            <h2 style={styles.sectionTitle}>Quick Stats</h2>
            <div style={styles.statsGrid}>
              <div style={styles.statCard}>
                <div style={styles.statIcon}>🎬</div>
                <div style={styles.statValue}>{stats.movies}</div>
                <div style={styles.statLabel}>Movies</div>
              </div>
              <div style={styles.statCard}>
                <div style={styles.statIcon}>📺</div>
                <div style={styles.statValue}>{stats.tvShows}</div>
                <div style={styles.statLabel}>TV Shows</div>
              </div>
              <div style={styles.statCard}>
                <div style={styles.statIcon}>👀</div>
                <div style={styles.statValue}>{stats.currentlyWatching}</div>
                <div style={styles.statLabel}>Currently Watching</div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Cards */}
        <div style={styles.navigationSection}>
          <h2 style={styles.sectionTitle}>Navigate</h2>
          <div style={styles.navGrid}>
            <div
              style={{
                ...styles.navCard,
                ...(hoveredCard === 'movies' ? styles.navCardHover : {}),
              }}
              onClick={() => navigate('/movies')}
              onMouseEnter={() => setHoveredCard('movies')}
              onMouseLeave={() => setHoveredCard(null)}
            >
              <div style={styles.navIcon}>🎬</div>
              <h3 style={styles.navTitle}>Movies</h3>
              <p style={styles.navDescription}>
                Track movies you've watched, want to watch, or are currently watching
              </p>
            </div>

            <div
              style={{
                ...styles.navCard,
                ...(hoveredCard === 'tv-shows' ? styles.navCardHover : {}),
              }}
              onClick={() => navigate('/tv-shows')}
              onMouseEnter={() => setHoveredCard('tv-shows')}
              onMouseLeave={() => setHoveredCard(null)}
            >
              <div style={styles.navIcon}>📺</div>
              <h3 style={styles.navTitle}>TV Shows</h3>
              <p style={styles.navDescription}>
                Track TV shows and seasons with Plex-style organization
              </p>
            </div>

            <div
              style={{
                ...styles.navCard,
                ...(hoveredCard === 'books' ? styles.navCardHover : {}),
              }}
              onClick={() => navigate('/books')}
              onMouseEnter={() => setHoveredCard('books')}
              onMouseLeave={() => setHoveredCard(null)}
            >
              <div style={styles.navIcon}>📖</div>
              <h3 style={styles.navTitle}>Books</h3>
              <p style={styles.navDescription}>
                Track books you've read, want to read, or are currently reading
              </p>
            </div>

            <div
              style={{
                ...styles.navCard,
                ...(hoveredCard === 'music' ? styles.navCardHover : {}),
              }}
              onClick={() => navigate('/music')}
              onMouseEnter={() => setHoveredCard('music')}
              onMouseLeave={() => setHoveredCard(null)}
            >
              <div style={styles.navIcon}>🎵</div>
              <h3 style={styles.navTitle}>Music</h3>
              <p style={styles.navDescription}>
                Track albums and songs you've listened to
              </p>
            </div>

            <div
              style={{
                ...styles.navCard,
                ...(hoveredCard === 'habits' ? styles.navCardHover : {}),
              }}
              onClick={() => navigate('/habits')}
              onMouseEnter={() => setHoveredCard('habits')}
              onMouseLeave={() => setHoveredCard(null)}
            >
              <div style={styles.navIcon}>📅</div>
              <h3 style={styles.navTitle}>Habit Tracker</h3>
              <p style={styles.navDescription}>
                Track daily habits including exercise, mindfulness, and music practice
              </p>
            </div>

            <div
              style={{
                ...styles.navCard,
                ...(hoveredCard === 'workouts' ? styles.navCardHover : {}),
              }}
              onClick={() => navigate('/workouts')}
              onMouseEnter={() => setHoveredCard('workouts')}
              onMouseLeave={() => setHoveredCard(null)}
            >
              <div style={styles.navIcon}>💪</div>
              <h3 style={styles.navTitle}>Workout Tracker</h3>
              <p style={styles.navDescription}>
                Track workouts, manage exercises, and create workout templates
              </p>
            </div>

            <div
              style={{
                ...styles.navCard,
                ...(hoveredCard === 'portfolio' ? styles.navCardHover : {}),
              }}
              onClick={() => navigate('/portfolio')}
              onMouseEnter={() => setHoveredCard('portfolio')}
              onMouseLeave={() => setHoveredCard(null)}
            >
              <div style={styles.navIcon}>💼</div>
              <h3 style={styles.navTitle}>Portfolio Tracker</h3>
              <p style={styles.navDescription}>
                Track investments, view holdings, manage transactions, and monitor asset allocation
              </p>
            </div>

            <div
              style={{
                ...styles.navCard,
                ...(hoveredCard === 'fire' ? styles.navCardHover : {}),
              }}
              onClick={() => navigate('/fire')}
              onMouseEnter={() => setHoveredCard('fire')}
              onMouseLeave={() => setHoveredCard(null)}
            >
              <div style={styles.navIcon}>🔥</div>
              <h3 style={styles.navTitle}>FIRE Journey</h3>
              <p style={styles.navDescription}>
                Track investment accounts, monitor growth, and project your path to financial independence
              </p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div style={styles.actionsSection}>
          <h2 style={styles.sectionTitle}>Quick Actions</h2>
          <div style={styles.actionsGrid}>
            <button
              style={{
                ...styles.actionButton,
                ...(hoveredCard === 'add-movie' ? styles.actionButtonHover : {}),
              }}
              onClick={() => navigate('/movies')}
              onMouseEnter={() => setHoveredCard('add-movie')}
              onMouseLeave={() => setHoveredCard(null)}
            >
              ➕ Add Movie
            </button>
            <button
              style={{
                ...styles.actionButton,
                ...(hoveredCard === 'add-tv' ? styles.actionButtonHover : {}),
              }}
              onClick={() => navigate('/tv-shows')}
              onMouseEnter={() => setHoveredCard('add-tv')}
              onMouseLeave={() => setHoveredCard(null)}
            >
              ➕ Add TV Show
            </button>
            <button
              style={{
                ...styles.actionButton,
                ...(hoveredCard === 'add-book' ? styles.actionButtonHover : {}),
              }}
              onClick={() => navigate('/books')}
              onMouseEnter={() => setHoveredCard('add-book')}
              onMouseLeave={() => setHoveredCard(null)}
            >
              ➕ Add Book
            </button>
            <button
              style={{
                ...styles.actionButton,
                ...(hoveredCard === 'books-stats' ? styles.actionButtonHover : {}),
              }}
              onClick={() => navigate('/books/stats')}
              onMouseEnter={() => setHoveredCard('books-stats')}
              onMouseLeave={() => setHoveredCard(null)}
            >
              📊 Books Stats
            </button>
            <button
              style={{
                ...styles.actionButton,
                ...(hoveredCard === 'add-music' ? styles.actionButtonHover : {}),
              }}
              onClick={() => navigate('/music')}
              onMouseEnter={() => setHoveredCard('add-music')}
              onMouseLeave={() => setHoveredCard(null)}
            >
              ➕ Add Music
            </button>
          </div>
        </div>
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
    maxWidth: '1200px',
    margin: '0 auto',
    padding: 'clamp(1rem, 3vw, 2rem)',
    boxSizing: 'border-box',
  },
  statsSection: {
    marginBottom: '3rem',
  },
  sectionTitle: {
    marginTop: 0,
    marginBottom: '1.5rem',
    fontSize: '1.5rem',
    color: '#333',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1.5rem',
  },
  statCard: {
    backgroundColor: 'white',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    textAlign: 'center',
    transition: 'transform 0.2s, box-shadow 0.2s',
  },
  statIcon: {
    fontSize: '3rem',
    marginBottom: '1rem',
  },
  statValue: {
    fontSize: '2.5rem',
    fontWeight: 'bold',
    color: '#007bff',
    marginBottom: '0.5rem',
  },
  statLabel: {
    fontSize: '1rem',
    color: '#666',
  },
  navigationSection: {
    marginBottom: '3rem',
  },
  navGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '1.5rem',
  },
  navCard: {
    backgroundColor: 'white',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    cursor: 'pointer',
    transition: 'transform 0.2s, box-shadow 0.2s',
    textAlign: 'center',
  },
  navCardHover: {
    transform: 'translateY(-4px)',
    boxShadow: '0 4px 8px rgba(0,0,0,0.15)',
  },
  navCardPlaceholder: {
    backgroundColor: 'white',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    textAlign: 'center',
    opacity: 0.6,
  },
  navIcon: {
    fontSize: '3rem',
    marginBottom: '1rem',
  },
  navTitle: {
    margin: '0 0 1rem 0',
    fontSize: '1.3rem',
    color: '#333',
  },
  navDescription: {
    margin: 0,
    color: '#666',
    fontSize: '0.9rem',
    lineHeight: '1.5',
  },
  actionsSection: {
    marginBottom: '2rem',
  },
  actionsGrid: {
    display: 'flex',
    gap: '1rem',
    flexWrap: 'wrap',
  },
  actionButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '500',
    transition: 'background-color 0.2s',
  },
  actionButtonHover: {
    backgroundColor: '#0056b3',
  },
};
