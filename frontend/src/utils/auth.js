// frontend/src/utils/auth.js
const API_URL = 'http://localhost:5000/api/auth';

export const loginUser = async (credentials) => {
  try {
    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',  // Important for cookies!
      body: JSON.stringify(credentials),
    });
    
    return await response.json();
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

export const logoutUser = async () => {
  try {
    const response = await fetch(`${API_URL}/logout`, {
      method: 'POST',
      credentials: 'include',  // Important for cookies!
    });
    
    return await response.json();
  } catch (error) {
    console.error('Logout error:', error);
    throw error;
  }
};

export const checkAuth = async () => {
  try {
    const response = await fetch(`${API_URL}/check-auth`, {
      credentials: 'include',  // Important for cookies!
    });
    
    return await response.json();
  } catch (error) {
    console.error('Auth check error:', error);
    return { authenticated: false };
  }
};