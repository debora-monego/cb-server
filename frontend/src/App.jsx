import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Login from './components/auth/Login';
import Registration from './components/auth/Registration';
import Dashboard from './components/Dashboard';
import ProtectedRoute from './components/auth/ProtectedRoute';
import ForgotPassword from './components/auth/ForgotPassword';
import ResetPassword from './components/auth/ResetPassword';
import Layout from './components/layout/Layout';
// import JobList from './components/jobs/JobList';
// import JobWizard from './components/jobs/JobWizard';
// import JobDetail from './components/jobs/JobDetail';
import Profile from './components/auth/Profile';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<Navigate to="/dashboard" />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Registration />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password/:token" element={<ResetPassword />} />
          
          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/dashboard" element={<Dashboard />} />
              {/* <Route path="/jobs" element={<JobList />} /> */}
              {/* <Route path="/jobs/new" element={<JobWizard />} /> */}
              {/* <Route path="/jobs/:jobId" element={<JobDetail />} /> */}
              <Route path="/profile" element={<Profile />} />
              {/* Add other protected routes here */}
            </Route>
          </Route>
          
          {/* Catch-all route */}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;