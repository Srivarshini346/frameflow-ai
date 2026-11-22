import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle2, AlertCircle, ArrowRight, Video, FileText, Music, Sparkles } from 'lucide-react';
import { getJobStatus } from '../api/client';

export default function ProcessingWorkspace({ currentJobId, setActiveTab, loadResultForJob }) {
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!currentJobId) return;

    let isMounted = true;
    const poll = async () => {
      try {
        const data = await getJobStatus(currentJobId);
        if (isMounted) {
          setJob(data);
          if (data.status === 'succeeded') {
            loadResultForJob(currentJobId);
          }
        }
      } catch (err) {
        if (isMounted) setError(err.message);
      }
    };

    poll();
    const interval = setInterval(poll, 1500);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [currentJobId]);

  if (!currentJobId) {
    return (
      <div style={{ maxWidth: '800px', margin: '60px auto', textAlign: 'center', padding: '40px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
          No Active Processing Job
        </h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
          Create a new video project in the studio to start the processing pipeline.
        </p>
        <button
          onClick={() => setActiveTab('create')}
          style={{
            backgroundColor: 'var(--primary)',
            color: '#FFFFFF',
            padding: '12px 24px',
            borderRadius: 'var(--radius-md)',
            fontWeight: 700,
          }}
        >
          Go to Create Studio
        </button>
      </div>
    );
  }

  const stages = [
    { key: 'validating', label: '1. Validating Narration & Inputs', icon: FileText },
    { key: 'synthesizing_speech', label: '2. Synthesizing / Transcribing Audio', icon: Music },
    { key: 'segmenting_scenes', label: '3. Meaning-Based Scene Segmentation', icon: Sparkles },
    { key: 'sourcing_footage', label: '4. Footage Discovery & Deduplication', icon: Video },
    { key: 'rendering_videos', label: '5. FFmpeg Multi-Aspect Compositing', icon: Video },
    { key: 'completed', label: '6. Finalizing Deliverables & Manifest', icon: CheckCircle2 }
  ];

  const isComplete = job?.status === 'succeeded';
  const isFailed = job?.status === 'failed';

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '36px 24px' }} className="animate-fade">
      <div style={{
        backgroundColor: 'var(--bg-card)',
        borderRadius: 'var(--radius-lg)',
        padding: '36px',
        border: '1px solid var(--border-light)',
        boxShadow: 'var(--shadow-md)',
        marginBottom: '28px'
      }}>
        {/* Job Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
          <div>
            <div style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              JOB ID: {currentJobId}
            </div>
            <h1 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)', marginTop: '4px' }}>
              {isComplete ? "Video Generation Succeeded!" : isFailed ? "Generation Failed" : "Processing Video Engine Pipeline"}
            </h1>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: 'var(--radius-full)',
            backgroundColor: isComplete ? 'var(--accent-mint-light)' : isFailed ? 'var(--accent-coral-light)' : 'var(--primary-light)',
            color: isComplete ? 'var(--accent-mint)' : isFailed ? 'var(--accent-coral)' : 'var(--primary)',
            fontWeight: 700,
            fontSize: '13px'
          }}>
            {!isComplete && !isFailed && <Loader2 size={16} className="animate-spin" />}
            {isComplete && <CheckCircle2 size={16} />}
            {isFailed && <AlertCircle size={16} />}
            <span style={{ textTransform: 'capitalize' }}>{job?.status || 'Queued'}</span>
          </div>
        </div>

        {/* Progress Bar */}
        <div style={{ marginBottom: '28px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px' }}>
            <span>Stage: <strong style={{ color: 'var(--text-primary)' }}>{job?.stage || 'Queued'}</strong></span>
            <span style={{ color: 'var(--primary)' }}>{job?.progress || 0}%</span>
          </div>
          <div style={{
            width: '100%',
            height: '10px',
            backgroundColor: 'var(--bg-subtle)',
            borderRadius: 'var(--radius-full)',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${job?.progress || 0}%`,
              height: '100%',
              backgroundColor: isComplete ? 'var(--accent-mint)' : isFailed ? 'var(--accent-coral)' : 'var(--primary)',
              transition: 'width 0.4s ease',
              borderRadius: 'var(--radius-full)'
            }} />
          </div>
        </div>

        {/* Stages Checklist */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px', marginBottom: '28px' }}>
          {stages.map((st, i) => {
            const Icon = st.icon;
            const completed = (job?.progress || 0) >= (i + 1) * 16.6 || isComplete;
            return (
              <div
                key={st.key}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: completed ? 'var(--primary-light)' : 'var(--bg-subtle)',
                  border: `1px solid ${completed ? 'var(--primary-border)' : 'transparent'}`,
                  color: completed ? 'var(--primary)' : 'var(--text-secondary)',
                  fontSize: '13px',
                  fontWeight: completed ? 700 : 500
                }}
              >
                <Icon size={18} />
                <span>{st.label}</span>
              </div>
            );
          })}
        </div>

        {/* Completion Call to Action */}
        {isComplete && (
          <div style={{
            backgroundColor: 'var(--accent-mint-light)',
            padding: '20px 24px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid #BCECDA',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                All 6 Deliverables Generated Successfully!
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                16:9, 9:16, 1:1 MP4 videos, SRT subtitles, timeline.json and manifest.json are ready.
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => setActiveTab('preview')}
                style={{
                  padding: '10px 18px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: '#FFFFFF',
                  color: 'var(--text-primary)',
                  fontWeight: 600,
                  fontSize: '13px',
                  border: '1px solid var(--border-medium)'
                }}
              >
                Export Files
              </button>
              <button
                onClick={() => setActiveTab('timeline')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 20px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--primary)',
                  color: '#FFFFFF',
                  fontWeight: 700,
                  fontSize: '13px',
                  boxShadow: '0 4px 12px rgba(124, 110, 230, 0.35)'
                }}
              >
                <span>Open Timeline Studio</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {isFailed && (
          <div style={{
            backgroundColor: 'var(--accent-coral-light)',
            padding: '18px 22px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid #FCD0D0',
            color: 'var(--accent-coral)'
          }}>
            <div style={{ fontWeight: 700, marginBottom: '4px' }}>Processing Error:</div>
            <div style={{ fontSize: '13px', fontFamily: 'var(--font-mono)' }}>{job?.error || "Unknown error occurred"}</div>
          </div>
        )}
      </div>

      {/* Real-time Generated Scenes Preview */}
      {job?.scenes && job.scenes.length > 0 && (
        <div>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '14px' }}>
            Generated Scenes ({job.scenes.length})
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {job.scenes.map((sc) => (
              <div
                key={sc.scene_number}
                style={{
                  backgroundColor: 'var(--bg-card)',
                  padding: '16px 20px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-light)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      backgroundColor: 'var(--primary-light)',
                      color: 'var(--primary)',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-full)'
                    }}>
                      Scene {sc.scene_number}
                    </span>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {sc.start_time}s - {sc.end_time}s ({sc.duration}s)
                    </span>
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    "{sc.narration_text}"
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    <strong>Visual:</strong> {sc.visual_description}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span style={{
                    fontSize: '12px',
                    fontWeight: 700,
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-full)',
                    backgroundColor: 'var(--accent-mint-light)',
                    color: 'var(--accent-mint)'
                  }}>
                    {Math.round((sc.relevance_score || 0.95) * 100)}% Match
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
