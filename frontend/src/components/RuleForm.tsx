import React, { useState } from 'react';
import './RuleForm.css';

interface RuleFormProps {
  initialData?: any;
  onSubmit: (data: any) => void;
  onPreview?: (data: any) => void;
  loading?: boolean;
}

export default function RuleForm({
  initialData,
  onSubmit,
  onPreview,
  loading = false,
}: RuleFormProps) {
  const [formData, setFormData] = useState(
    initialData || {
      name: '',
      description: '',
      source_ip: '',
      destination_ip: '',
      protocol: '',
      source_port: '',
      destination_port: '',
      action: 'discard',
      ttl_minutes: '60',
      enabled: true,
    }
  );

  const handleChange = (e: React.ChangeEvent<any>) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="rule-form">
      <div className="form-group">
        <label htmlFor="name">Rule Name *</label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          required
          placeholder="e.g., Block DDoS Source"
        />
      </div>

      <div className="form-group">
        <label htmlFor="description">Description</label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          placeholder="Describe the purpose of this rule"
          rows={3}
        />
      </div>

      <fieldset>
        <legend>Match Criteria</legend>

        <div className="form-group">
          <label htmlFor="source_ip">Source IP (CIDR)</label>
          <input
            type="text"
            id="source_ip"
            name="source_ip"
            value={formData.source_ip}
            onChange={handleChange}
            placeholder="e.g., 192.0.2.0/24"
          />
        </div>

        <div className="form-group">
          <label htmlFor="destination_ip">Destination IP (CIDR)</label>
          <input
            type="text"
            id="destination_ip"
            name="destination_ip"
            value={formData.destination_ip}
            onChange={handleChange}
            placeholder="e.g., 192.0.2.1/32"
          />
        </div>

        <div className="form-group">
          <label htmlFor="protocol">Protocol</label>
          <select
            id="protocol"
            name="protocol"
            value={formData.protocol}
            onChange={handleChange}
          >
            <option value="">Any</option>
            <option value="tcp">TCP</option>
            <option value="udp">UDP</option>
            <option value="icmp">ICMP</option>
          </select>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="source_port">Source Port(s)</label>
            <input
              type="text"
              id="source_port"
              name="source_port"
              value={formData.source_port}
              onChange={handleChange}
              placeholder="e.g., 80,443 or 1024-2048"
            />
          </div>

          <div className="form-group">
            <label htmlFor="destination_port">Destination Port(s)</label>
            <input
              type="text"
              id="destination_port"
              name="destination_port"
              value={formData.destination_port}
              onChange={handleChange}
              placeholder="e.g., 80,443 or 1024-2048"
            />
          </div>
        </div>
      </fieldset>

      <fieldset>
        <legend>Action</legend>

        <div className="form-group">
          <label htmlFor="action">Action</label>
          <select
            id="action"
            name="action"
            value={formData.action}
            onChange={handleChange}
          >
            <option value="discard">Discard (Drop)</option>
            <option value="accept">Accept (Allow)</option>
            <option value="rate-limit">Rate Limit</option>
          </select>
        </div>
      </fieldset>

      <fieldset>
        <legend>Options</legend>

        <div className="form-group">
          <label htmlFor="ttl_minutes">TTL (minutes)</label>
          <input
            type="number"
            id="ttl_minutes"
            name="ttl_minutes"
            value={formData.ttl_minutes}
            onChange={handleChange}
            min="1"
            max="1440"
            placeholder="60"
          />
        </div>

        <div className="form-group checkbox">
          <input
            type="checkbox"
            id="enabled"
            name="enabled"
            checked={formData.enabled}
            onChange={handleChange}
          />
          <label htmlFor="enabled">Enabled</label>
        </div>
      </fieldset>

      <div className="form-actions">
        <button
          type="submit"
          className="button button-primary"
          disabled={loading}
        >
          {loading ? 'Creating...' : 'Create Rule'}
        </button>
        {onPreview && (
          <button
            type="button"
            className="button button-secondary"
            onClick={() => onPreview(formData)}
            disabled={loading}
          >
            Preview Juniper Config
          </button>
        )}
      </div>
    </form>
  );
}
