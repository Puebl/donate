import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  HomeIcon, 
  CreditCardIcon, 
  UserIcon, 
  VideoCameraIcon, 
  PuzzlePieceIcon,
  ChartBarIcon,
  Bars3Icon,
  XMarkIcon,
  ArrowRightOnRectangleIcon
} from '@heroicons/react/24/outline';
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const { logout } = useAuth();

  const navigation = [
    {
      name: 'Главная',
      href: '/',
      icon: HomeIcon,
    },
    {
      name: 'Платежи',
      href: '/payment',
      icon: CreditCardIcon,
    },
    {
      name: 'Авторизация',
      href: '/auth',
      icon: UserIcon,
    },
    {
      name: 'Стримеры',
      href: '/streamer',
      icon: VideoCameraIcon,
    },
    {
      name: 'Виджеты',
      href: '/widget',
      icon: PuzzlePieceIcon,
    },
    {
      name: 'Статистика',
      href: '/statistics',
      icon: ChartBarIcon,
    },
  ];

  const getBreadcrumbs = () => {
    const pathnames = location.pathname.split('/').filter(x => x);
    return pathnames.map((name, index) => {
      const routeTo = `/${pathnames.slice(0, index + 1).join('/')}`;
      const isLast = index === pathnames.length - 1;
      const displayName = navigation.find(item => item.href === routeTo)?.name || name;
      
      return (
        <div key={name} className="flex items-center">
          <span className="text-gray-400 mx-2">/</span>
          {isLast ? (
            <span className="text-gray-100 font-medium">{displayName}</span>
          ) : (
            <NavLink
              to={routeTo}
              className="text-gray-400 hover:text-gray-100 transition-colors"
            >
              {displayName}
            </NavLink>
          )}
        </div>
      );
    });
  };

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 z-50 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-900 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-gray-900">
          <div className="flex h-16 items-center justify-between px-6">
            <h1 className="text-xl font-bold text-white">Админ-панель</h1>
            <button
              onClick={() => setSidebarOpen(false)}
              className="text-gray-400 hover:text-white"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) =>
                  `group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`
                }
              >
                <item.icon
                  className={`mr-3 h-5 w-5 ${
                    location.pathname === item.href ? 'text-white' : 'text-gray-400 group-hover:text-gray-300'
                  }`}
                  aria-hidden="true"
                />
                {item.name}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-grow flex-col overflow-y-auto bg-gray-900 border-r border-gray-800">
          <div className="flex h-16 items-center px-6">
            <h1 className="text-xl font-bold text-white">Админ-панель</h1>
          </div>
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`
                }
              >
                <item.icon
                  className={`mr-3 h-5 w-5 ${
                    location.pathname === item.href ? 'text-white' : 'text-gray-400 group-hover:text-gray-300'
                  }`}
                  aria-hidden="true"
                />
                {item.name}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-800 bg-gray-950 px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
          <button
            type="button"
            className="lg:hidden -m-2.5 p-2.5 text-gray-400 hover:text-gray-100"
            onClick={() => setSidebarOpen(true)}
          >
            <Bars3Icon className="h-6 w-6" aria-hidden="true" />
          </button>

          {/* Breadcrumb */}
          <div className="flex flex-1 items-center">
            <nav className="flex items-center text-sm">
              <NavLink
                to="/"
                className="text-gray-400 hover:text-gray-100 transition-colors"
              >
                Главная
              </NavLink>
              {getBreadcrumbs()}
            </nav>
          </div>

          {/* Right side */}
          <div className="flex items-center gap-x-4">
            <div className="text-sm text-gray-400">
              {new Date().toLocaleDateString('ru-RU', {
                weekday: 'short',
                year: 'numeric',
                month: 'short',
                day: 'numeric',
              })}
            </div>
            <button
              onClick={logout}
              className="flex items-center gap-2 px-3 py-2 text-sm text-gray-400 hover:text-white transition-colors"
            >
              <ArrowRightOnRectangleIcon className="h-5 w-5" />
              <span className="hidden sm:inline">Выйти</span>
            </button>
          </div>
        </div>

        {/* Page content */}
        <main className="py-6">
          <div className="px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;