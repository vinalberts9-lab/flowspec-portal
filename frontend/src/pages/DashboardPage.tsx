import React, { useEffect, useState } from 'react';
import { dashboardAPI } from '../services/api';
import './DashboardPage.css';

interface DashboardStats {
  total_rules: number;
  active_rules: number;
  draft_rules: number;
  error_rules: number;
  exabgp_status: string;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await dashboardAPI.getStats();
      setStats(response.data);
      setError('');
    } catch (err: any) {
      setError('Failed to fetch dashboard stats');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading"><div className="spinner"></div></div>;

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats?.total_rules || 0}</div>
          <div className="stat-label">Total Rules</div>
        </div>
        <div className="stat-card active">
          <div className="stat-value">{stats?.active_rules || 0}</div>
          <div className="stat-label">Active Rules</div>
        </div>
        <div className="stat-card draft">
          <div className="stat-value">{stats?.draft_rules || 0}</div>
          <div className="stat-label">Draft Rules</div>
        </div>
        <div className="stat-card error">
          <div className="stat-value">{stats?.error_rules || 0}</div>
          <div className="stat-label">Error Rules</div>
        </div>
      </div>

      <div className="health-card">
        <h3>System Health</h3>
        <div className="health-item">
          <span>ExaBGP Status:</span>
          <span className={`status ${stats?.exabgp_status === 'healthy' ? 'healthy' : 'unhealthy'}`}>
            {stats?.exabgp_status}
          </span>
        </div>
      </div>
    </div>
  );
}
