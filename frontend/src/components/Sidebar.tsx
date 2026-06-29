import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Sidebar.css';

export default function Sidebar() {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>FlowSpec</h2>
        <p>BGP Portal</p>
      </div>
      <nav className="sidebar-nav">
        <Link
          to="/"
          className={`nav-item ${isActive('/') && !isActive('/rules') ? 'active' : ''}`}
        >
          📊 Dashboard
        </Link>
        <Link
          to="/rules"
          className={`nav-item ${isActive('/rules') ? 'active' : ''}`}
        >
          📋 Rules
        </Link>
        <Link
          to="/rules/create"
          className="nav-item"
        >
          ➕ Create Rule
        </Link>
        <Link
          to="/audit-logs"
          className={`nav-item ${isActive('/audit-logs') ? 'active' : ''}`}
        >
          📝 Audit Logs
        </Link>
      </nav>
    </aside>
  );
}
