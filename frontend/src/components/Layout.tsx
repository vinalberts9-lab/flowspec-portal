import React from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import Sidebar from './Sidebar';
import './Layout.css';

export default function Layout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="layout">
      <Sidebar />
      <div className="layout-content">
        <header className="layout-header">
          <div className="header-title">
            <h1>FlowSpec Portal</h1>
          </div>
          <div className="header-user">
            <span className="user-info">
              {user?.username} ({user?.role})
            </span>
            <button className="button button-logout" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </header>
        <main className="layout-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
