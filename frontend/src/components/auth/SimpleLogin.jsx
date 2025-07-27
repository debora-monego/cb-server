// src/components/auth/SimpleLogin.jsx
import React, { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";

// In SimpleLogin.jsx
// In SimpleLogin.jsx
const SimpleLogin = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [remember, setRemember] = useState(false);  // Add this state
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    
    const { login } = useAuth();
    
    const handleSubmit = async (e) => {
      e.preventDefault();
      
      if (!username || !password) {
        setError('Please enter both username and password');
        return;
      }
      
      setError('');
      setLoading(true);
      
      try {
        // Pass remember flag to login
        const result = await login(username, password, remember);
        
        if (result.success) {
          window.location.href = '/dashboard';
        } else {
          setError(result.message || 'Login failed. Please try again.');
        }
      } catch (err) {
        console.error('Login error:', err);
        setError('An unexpected error occurred. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    return (
      <div style={{ maxWidth: "400px", margin: "0 auto", padding: "20px" }}>
        <h2>Sign In</h2>
        
        <form onSubmit={handleSubmit}>
          {/* Username and password fields remain the same */}
          
          {/* Add remember-me checkbox */}
          <div style={{ marginBottom: "15px" }}>
            <label style={{ display: "flex", alignItems: "center" }}>
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                style={{ marginRight: "8px" }}
              />
              Remember me
            </label>
          </div>
          
          <button type="submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        
        {/* Link to password reset */}
        <div style={{ marginTop: "15px", textAlign: "center" }}>
          <p>
            <a href="/forgot-password" style={{ color: "#4f46e5", textDecoration: "none" }}>
              Forgot your password?
            </a>
          </p>
          <p>
            Don't have an account?{' '}
            <a href="/register" style={{ color: "#4f46e5", textDecoration: "none" }}>
              Register
            </a>
          </p>
        </div>
      </div>
    );
  };

export default SimpleLogin;