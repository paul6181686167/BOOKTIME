import React from 'react';

const LoadingSkeleton = () => {
  return (
    <div className="book-card bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Image skeleton */}
      <div className="aspect-[2/3] bg-gray-200 loading-skeleton"></div>
      
      {/* Content skeleton */}
      <div className="p-4">
        {/* Title skeleton */}
        <div className="h-4 bg-gray-200 rounded loading-skeleton mb-2"></div>
        <div className="h-4 bg-gray-200 rounded loading-skeleton w-3/4 mb-3"></div>
        
        {/* Author skeleton */}
        <div className="h-3 bg-gray-200 rounded loading-skeleton w-1/2 mb-3"></div>
        
        {/* Progress bar skeleton */}
        <div className="h-2 bg-gray-200 rounded loading-skeleton mb-3"></div>
        
        {/* Date skeleton */}
        <div className="h-3 bg-gray-200 rounded loading-skeleton w-2/3"></div>
      </div>
    </div>
  );
};

export default LoadingSkeleton;