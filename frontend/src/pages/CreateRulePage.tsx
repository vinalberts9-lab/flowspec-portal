import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { rulesAPI } from '../services/api';
import RuleForm from '../components/RuleForm';
import './CreateRulePage.css';

export default function CreateRulePage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [junipePreview, setJuniperPreview] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (formData: any) => {
    setLoading(true);
    setError('');

    try {
      const response = await rulesAPI.createRule(formData);
      alert('Rule created successfully!');
      navigate(`/rules/${response.data.id}/edit`);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create rule');
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async (formData: any) => {
    try {
      const response = await rulesAPI.previewJuniper(formData);
      setJuniperPreview(response.data.juniper_config);
    } catch (err: any) {
      setError('Failed to generate preview');
    }
  };

  return (
    <div className="create-rule-page">
      <h2>Create New Rule</h2>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="create-container">
        <div className="form-section">
          <RuleForm onSubmit={handleSubmit} onPreview={handlePreview} loading={loading} />
        </div>

        {juniperPreview && (
          <div className="preview-section">
            <h3>Juniper Configuration Preview</h3>
            <pre>{juniperPreview}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
