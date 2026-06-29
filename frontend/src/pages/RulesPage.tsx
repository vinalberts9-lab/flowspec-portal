import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { rulesAPI } from '../services/api';
import './RulesPage.css';

interface Rule {
  id: string;
  name: string;
  description: string;
  status: string;
  action: string;
  created_by: string;
  created_at: string;
  deployed_at: string | null;
}

export default function RulesPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    fetchRules();
  }, [statusFilter]);

  const fetchRules = async () => {
    try {
      const params = statusFilter !== 'all' ? { status: statusFilter } : {};
      const response = await rulesAPI.listRules(params);
      setRules(response.data.rules);
      setError('');
    } catch (err: any) {
      setError('Failed to fetch rules');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this rule?')) return;

    try {
      await rulesAPI.deleteRule(id);
      setRules(rules.filter((r) => r.id !== id));
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to delete rule');
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'active':
        return 'status-active';
      case 'draft':
        return 'status-draft';
      case 'error':
        return 'status-error';
      case 'withdrawn':
        return 'status-withdrawn';
      default:
        return '';
    }
  };

  if (loading) return <div className="loading"><div className="spinner"></div></div>;

  return (
    <div className="rules-page">
      <div className="page-header">
        <h2>FlowSpec Rules</h2>
        <Link to="/rules/create" className="button button-primary">
          ➕ Create Rule
        </Link>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="filters">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">All Status</option>
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="withdrawn">Withdrawn</option>
          <option value="error">Error</option>
        </select>
      </div>

      {rules.length === 0 ? (
        <div className="empty-state">
          <p>No rules found</p>
          <Link to="/rules/create" className="button button-primary">
            Create your first rule
          </Link>
        </div>
      ) : (
        <div className="rules-table">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Status</th>
                <th>Action</th>
                <th>Created By</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((rule) => (
                <tr key={rule.id}>
                  <td className="name-cell">{rule.name}</td>
                  <td>
                    <span className={`status-badge ${getStatusBadgeClass(rule.status)}`}>
                      {rule.status}
                    </span>
                  </td>
                  <td>{rule.action}</td>
                  <td>{rule.created_by}</td>
                  <td>{new Date(rule.created_at).toLocaleDateString()}</td>
                  <td className="actions-cell">
                    <Link to={`/rules/${rule.id}/edit`} className="action-link">
                      Edit
                    </Link>
                    <button
                      onClick={() => handleDelete(rule.id)}
                      className="action-link delete"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
