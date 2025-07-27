import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Link } from 'react-router-dom';

const Dashboard = () => {
  const { currentUser } = useAuth();

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Welcome, {currentUser?.username}!</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>My Jobs</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-gray-600">Manage your molecular modeling jobs.</p>
            <Link to="/jobs" className="text-blue-600 hover:underline">View jobs</Link>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>New Job</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-gray-600">Start a new protein structure analysis job.</p>
            <Link to="/jobs/new" className="text-blue-600 hover:underline">Create job</Link>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-gray-600">Update your account information.</p>
            <Link to="/profile" className="text-blue-600 hover:underline">View profile</Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;