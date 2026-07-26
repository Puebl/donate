import React from 'react';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  count?: number;
}

const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  variant = 'text',
  width,
  height,
  count = 1,
}) => {
  const baseClasses = 'animate-pulse bg-gray-700';
  
  const variantClasses = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  const defaultDimensions = {
    text: { width: '100%', height: '1rem' },
    circular: { width: '2.5rem', height: '2.5rem' },
    rectangular: { width: '100%', height: '4rem' },
  };

  const style: React.CSSProperties = {
    width: width ?? defaultDimensions[variant].width,
    height: height ?? defaultDimensions[variant].height,
  };

  const elements = Array.from({ length: count }, (_, i) => (
    <div
      key={i}
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
    />
  ));

  return count > 1 ? <>{elements}</> : elements[0];
};

interface TableSkeletonProps {
  columns: number;
  rows?: number;
}

export const TableSkeleton: React.FC<TableSkeletonProps> = ({ columns, rows = 5 }) => {
  return (
    <>
      {Array.from({ length: rows }, (_, rowIndex) => (
        <tr key={rowIndex} className="border-b border-gray-800">
          {Array.from({ length: columns }, (_, colIndex) => (
            <td key={colIndex} className="px-4 py-3">
              <Skeleton 
                variant="text" 
                width={colIndex === 0 ? '3rem' : `${60 + Math.random() * 40}%`}
                height="1.25rem"
              />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
};

interface CardSkeletonProps {
  hasIcon?: boolean;
}

export const CardSkeleton: React.FC<CardSkeletonProps> = ({ hasIcon = false }) => {
  return (
    <div className="card animate-pulse">
      {hasIcon && (
        <div className="flex items-center gap-3 mb-4">
          <Skeleton variant="circular" width="2.5rem" height="2.5rem" />
          <div className="flex-1">
            <Skeleton variant="text" width="60%" height="1.25rem" className="mb-2" />
            <Skeleton variant="text" width="40%" height="0.875rem" />
          </div>
        </div>
      )}
      <Skeleton variant="text" width="30%" height="0.875rem" className="mb-3" />
      <Skeleton variant="text" width="50%" height="2rem" className="mb-2" />
      <Skeleton variant="text" width="70%" height="0.875rem" />
    </div>
  );
};

interface StatCardSkeletonProps {
  count?: number;
}

export const StatCardSkeleton: React.FC<StatCardSkeletonProps> = ({ count = 1 }) => {
  return (
    <>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="card animate-pulse">
          <Skeleton variant="text" width="40%" height="0.875rem" className="mb-3" />
          <Skeleton variant="text" width="60%" height="2rem" className="mb-2" />
          <Skeleton variant="text" width="50%" height="0.75rem" />
        </div>
      ))}
    </>
  );
};

export default Skeleton;
