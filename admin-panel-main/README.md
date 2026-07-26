# Donate Admin Frontend

A modern, responsive admin panel frontend built with React, TypeScript, and Vite for managing and monitoring backend services.

## 🚀 Features

- **Modern Tech Stack**: React 18 + TypeScript + Vite
- **Beautiful UI**: Dark theme with Tailwind CSS
- **Service Monitoring**: Real-time health status and metrics
- **Responsive Design**: Mobile-friendly interface
- **Component Architecture**: Reusable components with TypeScript
- **API Integration**: Axios-based client with error handling
- **Routing**: React Router for navigation
- **Auto-refresh**: Automatic data updates every 30 seconds

## 📁 Project Structure

```
frontend/
├── public/
├── src/
│   ├── api/              # API client and utilities
│   │   ├── client.ts
│   │   └── index.ts
│   ├── components/        # Reusable UI components
│   │   ├── Layout.tsx
│   │   ├── ServiceCard.tsx
│   │   ├── DataTable.tsx
│   │   └── index.ts
│   ├── pages/            # Page components
│   │   ├── Dashboard.tsx
│   │   ├── PaymentService.tsx
│   │   ├── AuthService.tsx
│   │   ├── StreamerService.tsx
│   │   └── WidgetService.tsx
│   ├── types/            # TypeScript type definitions
│   │   └── index.ts
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

## 🛠️ Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with custom theme
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Icons**: Heroicons
- **UI Components**: Custom components with Tailwind

## 📋 Prerequisites

- Node.js 16+ 
- npm or yarn package manager
- Backend API running on `http://localhost:9005`

## 🚀 Installation & Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Build for production**:
   ```bash
   npm run build
   ```

4. **Preview production build**:
   ```bash
   npm run preview
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file in the root directory:

```env
VITE_API_BASE_URL=http://localhost:9005/api
```

### Vite Configuration

The `vite.config.ts` includes:

- Proxy configuration for API calls
- Path aliases (`@/` maps to `src/`)
- React plugin setup

### Tailwind CSS Configuration

Custom theme with:
- Dark mode support
- Custom color palette (success, warning, error)
- Extended animations and components

## 📊 Available Services

The admin panel monitors the following services:

- **Payment Service** (`/payment`)
  - Health: `GET /api/payment/health`
  - Stats: `GET /api/payment/stats`

- **Auth Service** (`/auth`)
  - Health: `GET /api/auth/health`
  - Stats: `GET /api/auth/stats`

- **Streamer Service** (`/streamer`)
  - Health: `GET /api/streamer/health`
  - Stats: `GET /api/streamer/stats`

- **Widget Service** (`/widget`)
  - Health: `GET /api/widget/health`
  - Stats: `GET /api/widget/stats`

## 🎨 UI Components

### Layout Component

- Sidebar navigation with responsive design
- Breadcrumb navigation
- Header with refresh controls
- Mobile-friendly collapsible menu

### ServiceCard Component

- Service health status display
- Real-time metrics
- Clickable navigation
- Status indicators with animations

### DataTable Component

- Sortable columns
- Pagination support
- Search functionality
- Loading states
- Error handling

## 🔄 API Integration

The frontend uses an Axios-based client with:

- Request/response interceptors
- Automatic error handling
- Authentication token support
- Timeout and retry logic

### Example API Usage

```typescript
import { apiClient } from '@/api';

// Get service health
const health = await apiClient.getServiceHealth('payment');

// Get service stats
const stats = await apiClient.getServiceStats('payment');

// Get paginated data
const payments = await apiClient.getPayments(
  filter,
  sort,
  { page: 1, limit: 10 }
);
```

## 🎯 Features Overview

### Dashboard

- System-wide health overview
- Service status cards with metrics
- Real-time updates
- Navigation to individual services

### Service Pages

- Individual service health monitoring
- Detailed performance metrics
- Service statistics
- Database information
- Auto-refresh capabilities

## 🔍 Development

### Code Style

- TypeScript strict mode enabled
- ESLint configuration for React
- Consistent component patterns
- Type-safe API integration

### Build Process

- TypeScript compilation
- React fast refresh in development
- Optimized production builds
- Asset optimization and bundling

## 📱 Responsive Design

The interface is fully responsive with:

- Mobile-first approach
- Collapsible sidebar for mobile
- Adaptive grid layouts
- Touch-friendly interactions

## 🚀 Deployment

### Production Build

```bash
npm run build
```

The build output will be in the `dist/` directory, ready for deployment to any static hosting service.

### Environment Configuration

Ensure the `VITE_API_BASE_URL` environment variable points to your backend API in production.

## 🔒 Security

- CORS configuration in Vite proxy
- Environment variable protection
- Input validation with TypeScript
- XSS prevention through React

## 🤝 Contributing

1. Follow the existing code patterns
2. Use TypeScript for new features
3. Maintain the component structure
4. Test responsive design
5. Update documentation as needed

## 📝 License

This project is part of the Donate Admin system.

---

**Note**: This frontend is designed to work with the corresponding FastAPI backend services. Ensure the backend is running and accessible at the configured API endpoint for full functionality.