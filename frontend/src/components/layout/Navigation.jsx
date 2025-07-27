import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

// Import icons (you'll need to install lucide-react or replace with your own icons)
const Home = () => <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" /></svg>;
const FileText = () => <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" /></svg>;
const Plus = () => <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" /></svg>;
const User = () => <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" /></svg>;
const LogOut = () => <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 001 1h12a1 1 0 001-1V7.414l-5-5H3zm3.293 9.293a1 1 0 011.414 0L10 14.586l2.293-2.293a1 1 0 011.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" /></svg>;
const Menu = () => <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>;
const X = () => <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>;

const Navigation = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  const handleLogout = async () => {
    try {
      console.log('Navigation: Handling logout click');
      
      // Get a direct reference to the logout function from useAuth
      const result = await logout();
      
      console.log('Navigation: Logout result:', result);
      
      // Add a small delay to ensure state updates
      setTimeout(() => {
        navigate('/login');
      }, 100);
    } catch (error) {
      console.error('Navigation: Logout error:', error);
      // Still redirect to login on error
      navigate('/login');
    }
  };
  
  const isActive = (path) => {
    return location.pathname === path ? 'bg-blue-700' : '';
  };
  
  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };
  
  // Close profile menu when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event) => {
      if (profileMenuOpen) {
        setProfileMenuOpen(false);
      }
    };
    
    // Add event listener when the dropdown is open
    if (profileMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    
    // Clean up event listener
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [profileMenuOpen]);
  
  return (
    <nav className="bg-blue-600 text-white shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          {/* Logo and main navigation */}
          <div className="flex items-center">
            <Link to="/dashboard" className="text-xl font-bold">
              Collagen
            </Link>
            
            {/* Desktop navigation */}
            <div className="hidden md:flex ml-10 space-x-8">
              <Link
                to="/dashboard"
                className={`flex items-center px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 ${isActive('/dashboard')}`}
              >
                <Home />
                <span className="ml-2">Dashboard</span>
              </Link>
              <Link
                to="/jobs"
                className={`flex items-center px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 ${isActive('/jobs')}`}
              >
                <FileText />
                <span className="ml-2">My Jobs</span>
              </Link>
              <Link
                to="/jobs/new"
                className={`flex items-center px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 ${isActive('/jobs/new')}`}
              >
                <Plus />
                <span className="ml-2">New Job</span>
              </Link>
            </div>
          </div>
          
          {/* User navigation */}
          <div className="hidden md:flex items-center space-x-4">
            <div className="relative">
              <button 
                className="flex items-center px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
                onClick={() => setProfileMenuOpen(!profileMenuOpen)}
              >
                <User />
                <span className="ml-2">{currentUser?.username}</span>
              </button>
              {profileMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10">
                  <Link
                    to="/profile"
                    className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    onClick={() => setProfileMenuOpen(false)}
                  >
                    Profile Settings
                  </Link>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      console.log("Logout button clicked");
                      setProfileMenuOpen(false);
                      
                      fetch('/api/auth/logout', {
                        method: 'POST',
                        credentials: 'include',
                        headers: {
                          'Content-Type': 'application/json'
                        }
                      })
                      .then(response => {
                        console.log("Logout response:", response);
                        window.location.href = '/login';
                      })
                      .catch(error => {
                        console.error("Logout error:", error);
                        window.location.href = '/login';
                      });
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
          
          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              type="button"
              className="p-2 rounded-md hover:bg-blue-700"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X /> : <Menu />}
            </button>
          </div>
        </div>
      </div>
      
      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1">
            <Link
              to="/dashboard"
              className={`flex items-center px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 ${isActive('/dashboard')}`}
              onClick={closeMobileMenu}
            >
              <Home />
              <span className="ml-2">Dashboard</span>
            </Link>
            <Link
              to="/jobs"
              className={`flex items-center px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 ${isActive('/jobs')}`}
              onClick={closeMobileMenu}
            >
              <FileText />
              <span className="ml-2">My Jobs</span>
            </Link>
            <Link
              to="/jobs/new"
              className={`flex items-center px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 ${isActive('/jobs/new')}`}
              onClick={closeMobileMenu}
            >
              <Plus />
              <span className="ml-2">New Job</span>
            </Link>
            <Link
              to="/profile"
              className={`flex items-center px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 ${isActive('/profile')}`}
              onClick={closeMobileMenu}
            >
              <User />
              <span className="ml-2">Profile</span>
            </Link>
            <button
              onClick={() => {
                handleLogout();
                closeMobileMenu();
              }}
              className="flex w-full items-center px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
            >
              <LogOut />
              <span className="ml-2">Sign Out</span>
            </button>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navigation;