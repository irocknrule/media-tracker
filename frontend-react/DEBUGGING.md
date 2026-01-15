# Debugging the Blank Page Issue

If you're seeing a blank page after login, follow these steps:

## 1. Check Browser Console

Open your browser's developer tools (F12) and check the Console tab for any errors. Look for:
- JavaScript errors (red text)
- API errors
- Network errors

## 2. Check Network Tab

In the Network tab, check if:
- The login request succeeded (status 200)
- The `/auth/me` request succeeded
- The `/movies/` request is being made and what its status is

## 3. Verify Backend is Running

Make sure the backend is running on port 8000:
```bash
# Check if backend is running
curl http://localhost:8000/health
```

## 4. Check API URL

Verify the API URL is correct. In the browser console, you should see:
```
API Base URL: http://localhost:8000
```

If it's different, check your `.env` file or environment variables.

## 5. Check Authentication Token

In the browser console, run:
```javascript
localStorage.getItem('token')
```

This should return a JWT token string. If it's null, the login didn't save the token properly.

## 6. Common Issues

### CORS Errors
- Make sure the backend CORS is configured to allow your frontend origin
- Check the backend logs for CORS errors

### 401 Unauthorized
- The token might be invalid or expired
- Check if the token is being sent in the Authorization header
- Verify the backend is accepting the token format

### Network Errors
- Backend might not be running
- Wrong API URL
- Firewall blocking the connection

### JavaScript Errors
- Check the console for React errors
- The ErrorBoundary should catch and display React errors

## 7. Test API Directly

Test the API endpoints directly:
```bash
# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Get movies (replace TOKEN with the token from login)
curl -X GET "http://localhost:8000/movies/" \
  -H "Authorization: Bearer TOKEN"
```

## 8. Enable More Logging

The code now includes console.log statements. Check the console for:
- "API Base URL: ..."
- "Movies component mounted, loading movies..."
- "Error loading movies: ..."
- "API Error: ..."

These will help identify where the issue is occurring.
