import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { ServiceStats } from '../types';
import { 
  CreditCardIcon, 
  UserIcon, 
  VideoCameraIcon, 
  PuzzlePieceIcon 
} from '@heroicons/react/24/outline';

interface ServiceCardData {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  stats: ServiceStats | null;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [services, setServices] = useState<ServiceCardData[]>([]);
  const [loading, setLoading] = useState(true);

  const serviceDefinitions = [
    {
      id: 'payment',
      name: 'Платежи',
      description: 'Балансы, транзакции и комиссии',
      icon: CreditCardIcon,
    },
    {
      id: 'auth',
      name: 'Авторизация',
      description: 'Пользователи и сессии',
      icon: UserIcon,
    },
    {
      id: 'streamer',
      name: 'Стримеры',
      description: 'Аккаунты стримеров',
      icon: VideoCameraIcon,
    },
    {
      id: 'widget',
      name: 'Виджеты',
      description: 'Виджеты и донаты',
      icon: PuzzlePieceIcon,
    }
  ];

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const statsData = await apiClient.getAllServiceStats();
        
        const servicesWithStats = serviceDefinitions.map(service => ({
          ...service,
          stats: statsData[service.id as keyof typeof statsData] || null
        }));
        
        setServices(servicesWithStats);
      } catch (err) {
        console.error('Failed to fetch stats:', err);
        setServices(serviceDefinitions.map(s => ({ ...s, stats: null })));
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Панель управления</h1>
        <p className="text-gray-400">Выберите раздел для работы</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {services.map((service) => {
          const Icon = service.icon;
          const tables = (service.stats as any)?.tables as Record<string, number> | undefined;
          
          return (
            <div
              key={service.id}
              onClick={() => navigate(`/${service.id}`)}
              className="bg-gray-900 border border-gray-800 rounded-lg p-6 hover:border-gray-700 hover:shadow-lg transition-all cursor-pointer group"
            >
              <div className="flex items-start gap-4">
                <div className="p-3 bg-gray-800 rounded-lg group-hover:bg-gray-700 transition-colors">
                  <Icon className="h-8 w-8 text-blue-400" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors">
                    {service.name}
                  </h3>
                  <p className="text-gray-400 text-sm mt-1">
                    {service.description}
                  </p>
                  
                  {tables && Object.keys(tables).length > 0 && (
                    <div className="flex flex-wrap gap-3 mt-4">
                      {Object.entries(tables).map(([tableName, count]) => (
                        <div key={tableName} className="text-xs">
                          <span className="text-gray-500">{tableName}:</span>{' '}
                          <span className="text-white font-medium">{count.toLocaleString('ru-RU')}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <svg
                  className="w-5 h-5 text-gray-600 group-hover:text-blue-400 transition-colors"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Dashboard;
