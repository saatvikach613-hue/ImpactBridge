import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './index.css';
import LoginPage    from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import SessionPage  from './pages/SessionPage';
import WishlistPage from './pages/WishlistPage';
import { getRole }  from './api/client';

function PrivateRoute({ children, roles }) {
  const token = localStorage.getItem('token');
  const role  = getRole();
  if (!token) return <Navigate to="/login" />;
  if (roles && !roles.includes(role)) return <Navigate to="/login" />;
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={
          <PrivateRoute roles={['coordinator']}>
            <DashboardPage />
          </PrivateRoute>
        } />
        <Route path="/session" element={
          <PrivateRoute roles={['volunteer', 'coordinator']}>
            <SessionPage />
          </PrivateRoute>
        } />
        <Route path="/wishlist" element={<WishlistPage />} />
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
  );
}
