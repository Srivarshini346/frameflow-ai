import React, { useEffect, useState } from 'react';
import { Film, Clock, CheckCircle2, AlertCircle, ArrowRight, Download, Calendar } from 'lucide-react';
import { listRecentJobs, getJobResult } from '../api/client';

export default function ProjectHistory({ setActiveTab, setCurrentJobId, setCurrentResult }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const data = await listRecentJobs();
      setJobs(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenJob = async (job) => {
    setCurrentJobId(job.job_id);
    if (job.status === 'succeeded') {
      const result = await getJobResult(job.job_id);
      setCurrentResult(result);
      setActiveTab('preview');
    } else {
      setActiveTab('workspace');
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '36px 24px' }} className="animate-fade">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '26px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '6px' }}>
            Project History & Outputs
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
            Review previous video generations, open deliverables, or re-enter editing workspaces.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('create')}
          style={{
            backgroundColor: 'var(--primary)',
            color: '#FFFFFF',
            padding: '10px 18px',
            borderRadius: 'var(--radius-md)',
            fontWeight: 700,
            fontSize: '13px'
          }}
        >
          New Project
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
          Loading project archive...
        </div>
      ) : jobs.length === 0 ? (
        <div style={{
          backgroundColor: 'var(--bg-card)',
          borderRadius: 'var(--radius-lg)',
          padding: '48px 24px',
          textAlign: 'center',
          border: '1px solid var(--border-light)'
        }}>
          <Film size={36} color="var(--primary)" style={{ margin: '0 auto 12px' }} />
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
            No Projects Yet
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '18px' }}>
            Create your first AI B-roll video to see it stored in project history.
          </p>
          <button
            onClick={() => setActiveTab('create')}
            style={{
              backgroundColor: 'var(--primary)',
              color: '#FFFFFF',
              padding: '10px 20px',
              borderRadius: 'var(--radius-md)',
              fontWeight: 700,
              fontSize: '13px'
            }}
          >
            Create Project
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {jobs.map((job) => {
            const isSuccess = job.status === 'succeeded';
            const isFailed = job.status === 'failed';
            return (
              <div
                key={job.job_id}
                style={{
                  backgroundColor: 'var(--bg-card)',
                  borderRadius: 'var(--radius-md)',
                  padding: '20px 24px',
                  border: '1px solid var(--border-light)',
                  boxShadow: 'var(--shadow-sm)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all 0.15s ease'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                    <span style={{ fontSize: '13px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {job.job_id}
                    </span>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-full)',
                      backgroundColor: isSuccess ? 'var(--accent-mint-light)' : isFailed ? 'var(--accent-coral-light)' : 'var(--primary-light)',
                      color: isSuccess ? 'var(--accent-mint)' : isFailed ? 'var(--accent-coral)' : 'var(--primary)'
                    }}>
                      {job.status.toUpperCase()}
                    </span>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Calendar size={13} /> {new Date(job.created_at).toLocaleString()}
                    </span>
                  </div>

                  <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                    Scenes: <strong>{job.scenes?.length || 0}</strong> • Progress: <strong>{job.progress}%</strong> • Stage: <strong>{job.stage}</strong>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    onClick={() => handleOpenJob(job)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 16px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: 'var(--primary-light)',
                      color: 'var(--primary)',
                      fontWeight: 700,
                      fontSize: '13px',
                      border: '1px solid var(--primary-border)'
                    }}
                  >
                    <span>{isSuccess ? 'Open Video' : 'View Status'}</span>
                    <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
