import React from 'react';
import { useParams } from 'react-router-dom';

const JobDetail = () => {
  const { jobId } = useParams();
  
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Job Details</h1>
      <p className="text-gray-600">This is a placeholder for job #{jobId} details.</p>
    </div>
  );
};

export default JobDetail;