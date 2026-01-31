import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import Login from './pages/Login';
import Home from './pages/Home';
import Movies from './pages/Movies';
import TVShows from './pages/TVShows';
import Books from './pages/Books';
import Music from './pages/Music';
import Habits from './pages/Habits';
import Workouts from './pages/Workouts';
import Portfolio from './pages/Portfolio';

function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ 
        padding: '2rem', 
        textAlign: 'center',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        Loading...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Home />
          </PrivateRoute>
        }
      />
      <Route
        path="/movies"
        element={
          <PrivateRoute>
            <Movies />
          </PrivateRoute>
        }
      />
      <Route
        path="/tv-shows"
        element={
          <PrivateRoute>
            <TVShows />
          </PrivateRoute>
        }
      />
      <Route
        path="/books/stats"
        element={
          <PrivateRoute>
            <Books initialTab="stats" />
          </PrivateRoute>
        }
      />
      <Route
        path="/books"
        element={
          <PrivateRoute>
            <Books />
          </PrivateRoute>
        }
      />
      <Route
        path="/music"
        element={
          <PrivateRoute>
            <Music />
          </PrivateRoute>
        }
      />
      <Route
        path="/habits"
        element={
          <PrivateRoute>
            <Habits />
          </PrivateRoute>
        }
      />
      <Route
        path="/workouts"
        element={
          <PrivateRoute>
            <Workouts />
          </PrivateRoute>
        }
      />
      <Route
        path="/portfolio"
        element={
          <PrivateRoute>
            <Portfolio />
          </PrivateRoute>
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
