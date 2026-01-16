# Media Tracker - React Frontend

This is a React proof-of-concept frontend for the Media Tracker application, focusing on the Movies feature.

## Development

### Prerequisites
- Node.js 18+ and npm

### Setup
```bash
cd frontend-react
npm install
```

### Run Development Server
```bash
npm run dev
```

The app will be available at http://localhost:3000

### Environment Variables
Create a `.env` file in the `frontend-react` directory:
```
VITE_API_BASE_URL=http://localhost:8000
```

## Docker

### Build and Run with Docker Compose
From the project root:
```bash
docker-compose up frontend-react
```

The React frontend will be available at http://localhost:3000

## Features

- ✅ Authentication (Login/Logout)
- ✅ Movies list with filtering by year
- ✅ Add new movies
- ✅ Delete movies
- ✅ Responsive grid layout
- ✅ Movie thumbnails
- ✅ Status badges
- ✅ Ratings display

## API Integration

The frontend communicates with the FastAPI backend running on port 8000. Make sure the backend is running before starting the frontend.

## Next Steps

- Add edit functionality for movies
- Implement search functionality
- Add pagination
- Improve error handling
- Add loading states
- Enhance UI/UX with a component library (Material-UI, Ant Design, etc.)
