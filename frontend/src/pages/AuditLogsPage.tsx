import React, { useEffect, useState } from 'react';
import { auditAPI } from '../services/api';
import './AuditLogsPage.css';

interface AuditLog {
  id: string;
  rule_id: string;
  action: string;
  user: string;
  timestamp: string;
  details: any;
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);

  useEffect(() => {
    fetchLogs();
  }, [page]);

  const fetchLogs = async () => {
    try {
      const response = await auditAPI.getLogs({ page, per_page: 50 });
      setLogs(response.data.logs);
      setError('');
    } catch (err: any) {
      setError('Failed to fetch audit logs');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading"><div className="spinner"></div></div>;

  return (
    <div className="audit-logs-page">
      <h2>Audit Logs</h2>

      {error && <div className="alert alert-error">{error}</div>}

      {logs.length === 0 ? (
        <div className="empty-state">
          <p>No audit logs found</p>
        </div>
      ) : (
        <div className="logs-table">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Action</th>
                <th>User</th>
                <th>Rule ID</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{new Date(log.timestamp).toLocaleString()}</td>
                  <td><span className="action-badge">{log.action}</span></td>
                  <td>{log.user}</td>
                  <td className="rule-id">{log.rule_id.slice(0, 8)}...</td>
                  <td className="details">{JSON.stringify(log.details).slice(0, 50)}...</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
