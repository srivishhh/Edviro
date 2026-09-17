import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './ThemeProvider';
import { AuthProvider, useAuth } from './AuthContext';
import { SmoothScrollProvider } from './SmoothScrollProvider';
import { RealtimeProvider } from '../hooks/useRealtime';
import CommandCenter from '../features/command-center/CommandCenter';
import Assets from '../features/assets/Assets';
import AssetDetail from '../features/assets/AssetDetail';
import Investigations from '../features/investigations/Investigations';
import InvestigationDetail from '../features/investigations/InvestigationDetail';
import TechnicianProfile from '../features/technician/TechnicianProfile';
import Rewards from '../features/technician/Rewards';
import Login from '../features/auth/Login';
import AdminConsole from '../features/admin/AdminConsole';

// Root gatekeeper based on authentication
const RootRedirect: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }
  if (user.role === 'admin') {
    return <Navigate to="/admin" replace />;
  }
  return <Navigate to="/dashboard" replace />;
};

// Protected Route for Technician Pages
const TechnicianRoute: React.FC<{ element: React.ReactElement }> = ({ element }) => {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }
  return element;
};

// Protected Route for Admin Page
const AdminRoute: React.FC<{ element: React.ReactElement }> = ({ element }) => {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }
  if (user.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }
  return element;
};

const Router: React.FC = () => (
  <ThemeProvider>
    <AuthProvider>
      <SmoothScrollProvider>
        <RealtimeProvider>
          <BrowserRouter>
            <Routes>
              {/* Public Entry / Auth */}
              <Route path="/login" element={<Login />} />
              <Route path="/" element={<RootRedirect />} />

              {/* Technician Domain */}
              <Route path="/dashboard" element={<TechnicianRoute element={<CommandCenter />} />} />
              <Route path="/assets" element={<TechnicianRoute element={<Assets />} />} />
              <Route path="/assets/:id" element={<TechnicianRoute element={<AssetDetail />} />} />
              <Route path="/investigations" element={<TechnicianRoute element={<Investigations />} />} />
              <Route path="/investigations/:id" element={<TechnicianRoute element={<InvestigationDetail />} />} />
              <Route path="/profile" element={<TechnicianRoute element={<TechnicianProfile />} />} />
              <Route path="/rewards" element={<TechnicianRoute element={<Rewards />} />} />

              {/* Admin Domain */}
              <Route path="/admin" element={<AdminRoute element={<AdminConsole />} />} />

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </RealtimeProvider>
      </SmoothScrollProvider>
    </AuthProvider>
  </ThemeProvider>
);

export default Router;
