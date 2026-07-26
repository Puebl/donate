import React from 'react';
import { ServiceInfo } from '../types';

interface ServiceCardProps {
  service: ServiceInfo;
  onClick?: () => void;
}

const ServiceCard: React.FC<ServiceCardProps> = ({ service, onClick }) => {
  const tables = (service.stats as any)?.tables as Record<string, number> | undefined;

  return (
    <div
      onClick={onClick}
      className="bg-gray-900 border border-gray-800 rounded-lg p-6 hover:border-gray-700 hover:shadow-lg transition-all cursor-pointer group"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white group-hover:text-primary-400 transition-colors">
          {service.name}
        </h3>
        <svg
          className="w-4 h-4 text-gray-600 group-hover:text-primary-400 transition-colors"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>

      <p className="text-gray-400 text-sm mb-4">
        {service.description}
      </p>

      {tables && Object.keys(tables).length > 0 && (
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(tables).map(([tableName, count]) => (
            <div key={tableName} className="bg-gray-800 rounded p-3">
              <div className="text-xs text-gray-500 mb-1 capitalize">{tableName}</div>
              <div className="text-lg font-semibold text-white">
                {count.toLocaleString('ru-RU')}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ServiceCard;
