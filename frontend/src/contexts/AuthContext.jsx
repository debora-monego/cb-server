import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

// Create the authentication context
const AuthContext = createContext();

// Custom hook to use the auth context
export const useAuth = () => {
  return useContext(AuthContext);
};

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Configure axios to include credentials for session cookies
  axios.defaults.withCredentials = true;

  // Check authentication status when the component mounts
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const response = await axios.get('/api/auth/check-auth');
        if (response.data.status === 'success' && response.data.authenticated) {
          setCurrentUser({
            username: response.data.username
          });
        }
      } catch (error) {
        console.error('Auth check error:', error);
        setCurrentUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  // Login function
  const login = async (username, password, remember = false) => {
    try {
      const response = await axios.post('/api/auth/login', {
        username,
        password,
        remember
      });

      if (response.data.status === 'success') {
        setCurrentUser({
          username: response.data.username
        });
        
        return { 
          success: true 
        };
      } else {
        return { 
          success: false, 
          message: response.data.message || 'Login failed' 
        };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        message: error.response?.data?.message || 'An error occurred during login' 
      };
    }
  };

  // Logout function
  const logout = async () => {
    try {
      console.log('AuthContext: Attempting to logout...');
      
      // Use explicit configuration for the request
      const response = await axios.post('/api/auth/logout', {}, {
        withCredentials: true
      });
      
      console.log('AuthContext: Logout response:', response.data);
      
      // Clear user state
      setCurrentUser(null);
      
      // For debugging - log cookie state
      console.log('Cookies after logout:', document.cookie);
      
      return { 
        success: true,
        message: response.data.message || 'Successfully logged out'
      };
    } catch (error) {
      console.error('AuthContext: Logout error:', error);
      
      // Even if the request fails, we should still log the user out on the frontend
      setCurrentUser(null);
      
      return { 
        success: true, // Still return success for UI flow
        message: 'You have been logged out locally. There was an issue communicating with the server.'
      };
    }
  };

  // Register function
  const register = async (username, email, password) => {
    try {
      const response = await axios.post('/api/auth/register', {
        username,
        email,
        password
      });

      if (response.data.status === 'success') {
        setCurrentUser({
          username: response.data.username
        });
        
        return { 
          success: true 
        };
      } else {
        return { 
          success: false, 
          message: response.data.message || 'Registration failed' 
        };
      }
    } catch (error) {
      console.error('Registration error:', error);
      return { 
        success: false, 
        message: error.response?.data?.message || 'An error occurred during registration' 
      };
    }
  };

  // Request password reset
  const requestPasswordReset = async (email) => {
    try {
      const response = await axios.post('/api/auth/reset_password_request', { email });
      return { 
        success: response.data.status === 'success', 
        message: response.data.message 
      };
    } catch (error) {
      console.error('Password reset request error:', error);
      return { 
        success: false, 
        message: error.response?.data?.message || 'An error occurred while requesting password reset' 
      };
    }
  };

  // Reset password with token
  const resetPassword = async (token, password) => {
    try {
      const response = await axios.post(`/api/auth/reset_password/${token}`, { password });
      return { 
        success: response.data.status === 'success', 
        message: response.data.message 
      };
    } catch (error) {
      console.error('Password reset error:', error);
      return { 
        success: false, 
        message: error.response?.data?.message || 'An error occurred while resetting password' 
      };
    }
  };

  // Verify reset token
  const verifyResetToken = async (token) => {
    try {
      const response = await axios.get(`/api/auth/verify_reset_token/${token}`);
      return { 
        success: response.data.status === 'success', 
        email: response.data.email 
      };
    } catch (error) {
      console.error('Token verification error:', error);
      return { 
        success: false, 
        message: error.response?.data?.message || 'Invalid or expired token' 
      };
    }
  };

  // Update user profile
  const updateProfile = async (data) => {
    try {
      const response = await axios.put('/api/auth/profile', data);
      return { 
        success: response.data.status === 'success', 
        message: response.data.message 
      };
    } catch (error) {
      console.error('Profile update error:', error);
      return { 
        success: false, 
        message: error.response?.data?.message || 'An error occurred while updating profile' 
      };
    }
  };

  // Delete account
  const deleteAccount = async (password) => {
    try {
      const response = await axios.delete('/api/auth/delete_account', {
        data: { password }
      });
      
      if (response.data.status === 'success') {
        setCurrentUser(null);
      }
      
      return { 
        success: response.data.status === 'success', 
        message: response.data.message 
      };
    } catch (error) {
      console.error('Account deletion error:', error);
      return { 
        success: false, 
        message: error.response?.data?.message || 'An error occurred while deleting account' 
      };
    }
  };

  // Context value
  const value = {
    currentUser,
    loading,
    login,
    logout,
    register,
    requestPasswordReset,
    resetPassword,
    verifyResetToken,
    updateProfile,
    deleteAccount
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export default AuthContext;