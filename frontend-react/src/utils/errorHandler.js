/**
 * Extract a readable error message from an API error response
 * Handles both string errors and Pydantic validation error arrays
 */
export const getErrorMessage = (error) => {
  if (!error) {
    return 'An unknown error occurred';
  }

  // If it's already a string, return it
  if (typeof error === 'string') {
    return error;
  }

  // Check for axios error response
  const response = error.response || error;
  const detail = response?.data?.detail;

  if (!detail) {
    return error.message || 'An unknown error occurred';
  }

  // If detail is a string, return it
  if (typeof detail === 'string') {
    return detail;
  }

  // If detail is an array (Pydantic validation errors)
  if (Array.isArray(detail)) {
    // Extract messages from validation errors
    const messages = detail.map((err) => {
      if (typeof err === 'string') {
        return err;
      }
      // Handle Pydantic error object: {type, loc, msg, input, url}
      const field = Array.isArray(err.loc) ? err.loc.slice(1).join('.') : 'field';
      return `${field}: ${err.msg || err.message || 'Invalid value'}`;
    });
    return messages.join('; ');
  }

  // If detail is an object, try to extract a message
  if (typeof detail === 'object') {
    return detail.msg || detail.message || JSON.stringify(detail);
  }

  return error.message || 'An unknown error occurred';
};
