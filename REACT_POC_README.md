# React Movies POC - Quick Start Guide

This document explains how to test the React proof-of-concept frontend for the Movies feature.

## What's Included

- ✅ React 18 with Vite
- ✅ React Router for navigation
- ✅ Authentication flow (Login/Logout)
- ✅ Movies page with full CRUD operations
- ✅ Docker configuration
- ✅ Responsive UI with inline styles

## Quick Start

### Option 1: Local Development (Recommended for Testing)

1. **Install dependencies:**
   ```bash
   cd frontend-react
   npm install
   ```

2. **Create `.env` file:**
   ```bash
   echo "VITE_API_BASE_URL=http://localhost:8000" > .env
   ```

3. **Start the backend** (if not already running):
   ```bash
   # From project root
   docker-compose up backend
   # Or run directly: uvicorn backend.main:app --reload
   ```

4. **Start the React dev server:**
   ```bash
   cd frontend-react
   npm run dev
   ```

5. **Access the app:**
   - React frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API docs: http://localhost:8000/docs

### Option 2: Docker (Production-like)

1. **Build and run all services:**
   ```bash
   # From project root
   docker-compose up --build
   ```

2. **Access the app:**
   - React frontend: http://localhost:3000
   - Streamlit frontend: http://localhost:8501 (still available)
   - Backend API: http://localhost:8000

## Testing the POC

1. **Login:**
   - Navigate to http://localhost:3000
   - You'll be redirected to `/login`
   - Use your existing Media Tracker credentials

2. **View Movies:**
   - After login, you'll see the Movies page
   - Movies are displayed in a responsive grid
   - Filter by year using the dropdown

3. **Add a Movie:**
   - Click "+ Add Movie" button
   - Fill in the form (title is required)
   - Submit to add the movie

4. **Delete a Movie:**
   - Click "Delete" on any movie card
   - Confirm the deletion

## Architecture

```
frontend-react/
├── src/
│   ├── components/       # Reusable components (empty for now)
│   ├── contexts/         # React Context (AuthContext)
│   ├── pages/            # Page components (Login, Movies)
│   ├── services/         # API services (api.js, authService.js, movieService.js)
│   ├── utils/            # Utility functions (empty for now)
│   ├── App.jsx           # Main app component with routing
│   ├── main.jsx          # Entry point
│   └── index.css         # Global styles
├── Dockerfile            # Multi-stage build for production
├── nginx.conf            # Nginx config for serving React app
├── package.json          # Dependencies
└── vite.config.js        # Vite configuration
```

## Key Features Implemented

### Authentication
- JWT token-based authentication
- Token stored in localStorage
- Automatic token injection in API requests
- Protected routes with redirect to login

### Movies Page
- List all movies with thumbnails
- Filter by year
- Add new movies with form
- Delete movies
- Display movie details (title, year, rating, status, notes)
- Responsive grid layout

### API Integration
- Axios for HTTP requests
- Request/response interceptors
- Error handling
- CORS support (already configured in backend)

## Comparison: React vs Streamlit

### React Advantages (This POC)
- ✅ Modern, responsive UI
- ✅ Better performance for complex interactions
- ✅ Full control over styling and UX
- ✅ Better mobile experience
- ✅ Can be extended to mobile app (React Native)
- ✅ Industry-standard stack

### Streamlit Advantages (Current)
- ✅ Python-only (no JavaScript needed)
- ✅ Rapid prototyping
- ✅ Built-in widgets and charts
- ✅ Less code for simple UIs
- ✅ Already working and familiar

## Next Steps for Full Migration

If you decide to proceed with React:

1. **Add remaining pages:**
   - TV Shows
   - Books
   - Music
   - Analytics
   - Portfolio
   - Workouts
   - Habits

2. **Enhance UI:**
   - Add a UI component library (Material-UI, Ant Design, or Tailwind CSS)
   - Improve loading states
   - Add error boundaries
   - Add toast notifications

3. **Add features:**
   - Edit functionality for movies
   - Search functionality
   - Pagination
   - Image upload
   - Advanced filtering

4. **Improve code:**
   - Add TypeScript
   - Add unit tests
   - Add E2E tests
   - Code splitting for performance

## Troubleshooting

### CORS Issues
- The backend already has CORS configured to allow all origins
- If you see CORS errors, check that the backend is running

### API Connection Issues
- Verify `VITE_API_BASE_URL` is set correctly
- Check that the backend is running on port 8000
- In Docker, use `http://localhost:8000` (not `http://backend:8000`) since requests come from the browser

### Build Issues
- Make sure Node.js 18+ is installed
- Delete `node_modules` and `package-lock.json`, then run `npm install` again

## Notes

- This is a proof of concept focusing on the Movies feature
- The UI uses inline styles for simplicity (can be replaced with CSS modules, styled-components, or a UI library)
- Authentication is basic but functional
- The code is structured to be easily extensible
