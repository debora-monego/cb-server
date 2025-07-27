// src/services/authService.js

// API service for authentication
const authAPI = {
  // Login user
  async login(username, password, remember = false) {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      // Include credentials to ensure cookies are sent/received
      credentials: 'include',
      body: JSON.stringify({ username, password, remember }),
    });
    
    return response.json();
  },
  
  // Register user
  async register(username, email, password) {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ username, email, password }),
    });
    
    return response.json();
  },
  
  // Logout user
  async logout() {
    const response = await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
    });
    
    return response.json();
  },
  
  // Get user profile
  async getProfile() {
    const response = await fetch('/api/auth/profile', {
      credentials: 'include',
    });
    
    if (response.ok) {
      return response.json();
    }
    throw new Error('Failed to get profile');
  },
  
  // Check authentication status
  async checkAuth() {
    try {
      const response = await fetch('/api/auth/check-auth', {
        credentials: 'include',
      });
      
      return response.json();
    } catch (error) {
      console.error('Error checking authentication:', error);
      return { authenticated: false };
    }
  },

  // Request password reset
  async requestPasswordReset(email) {
    const response = await fetch('/api/auth/reset_password_request', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });
    
    return response.json();
  },

  // Reset password with token
  async resetPassword(token, password) {
    const response = await fetch(`/api/auth/reset_password/${token}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ password }),
    });
    
    return response.json();
  },

  // Verify reset token
  async verifyResetToken(token) {
    const response = await fetch(`/api/auth/verify_reset_token/${token}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    return response.json();
  }
};

export default authAPI;