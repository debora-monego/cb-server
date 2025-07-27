import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../ui/button';

const LogoutTest = () => {
  const [status, setStatus] = useState('');
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    setStatus('Attempting to logout...');
    
    try {
      // Try with a direct axios call
      const axios = await import('axios');
      setStatus('Making direct API call to /api/auth/logout...');
      
      const response = await axios.default.post('/api/auth/logout', {}, {
        withCredentials: true
      });
      
      setStatus(`API response: ${JSON.stringify(response.data)}`);
      
      // Continue with context logout
      setStatus('Calling logout from AuthContext...');
      const result = await logout();
      
      setStatus(`Logout complete. Result: ${JSON.stringify(result)}`);
      setTimeout(() => navigate('/login'), 3000);
    } catch (error) {
      setStatus(`Error during logout: ${error.message}`);
      console.error('Detailed error:', error);
    }
  };

  return (
    <div className="p-4 border rounded shadow-sm max-w-md mx-auto mt-8">
      <h2 className="text-xl font-bold mb-4">Logout Test</h2>
      
      <Button 
        onClick={handleLogout}
        className="w-full mb-4"
      >
        Test Logout
      </Button>
      
      {status && (
        <div className="mt-4 p-3 bg-gray-100 rounded text-sm whitespace-pre-wrap">
          <strong>Status:</strong>
          <pre>{status}</pre>
        </div>
      )}
    </div>
  );
};

export default LogoutTest;