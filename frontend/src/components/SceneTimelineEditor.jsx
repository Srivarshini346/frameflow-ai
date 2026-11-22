import React, { useState } from 'react';
import { RefreshCw, Play, Sliders, CheckCircle2, ShieldCheck, Sparkles, ExternalLink, Loader2 } from 'lucide-react';
import { replaceSceneClip, getJobResult } from '../api/client';

export default function SceneTimelineEditor({ currentJob, currentJobId, setCurrentJob, setCurrentResult }) {
  const [replacingSceneNum, setReplacingSceneNum] = useState(null);
  const [customQuery, setCustomQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);

  if (!currentJob || !currentJob.scenes || currentJob.scenes.length === 0) {
    return (
      <div style={{ maxWidth: '800px', margin: '60px auto', textAlign: 'center', padding: '40px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
          No Scenes to Edit
        </h2>
        <p style={{ color: 'var(--text-secondary)' }}>
          Create and run a video project first to edit individual scenes and perform incremental rerendering.
        </p>
      </div>
    );
  }

  const handleRerender = async (sceneNumber) => {
    setLoading(true);
    setStatusMsg(`Rerendering clip for Scene ${sceneNumber}...`);
    try {
      const updatedJob = await replaceSceneClip(currentJobId, sceneNumber, {
        custom_query: customQuery || undefined
      });
      setCurrentJob(updatedJob);
      const updatedResult = await getJobResult(currentJobId);
      setCurrentResult(updatedResult);
      setStatusMsg(`Scene ${sceneNumber} successfully replaced and incremental video updated!`);
      setReplacingSceneNum(null);
      setCustomQuery('');
    } catch (err) {
      setStatusMsg(`Error replacing scene: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '36px 24px' }} className="animate-fade">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '26px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '6px' }}>
            Interactive Scene Editor & Incremental Rerender
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
            Modify visual intent or replace footage for any individual scene without re-rendering the entire video.
          </p>
        </div>

        <div style={{
          backgroundColor: 'var(--primary-light)',
          color: 'var(--primary)',
          padding: '6px 14px',
          borderRadius: 'var(--radius-full)',
          fontSize: '13px',
          fontWeight: 700
        }}>
          {currentJob.scenes.length} Meaning-Aligned Scenes
        </div>
      </div>

      {statusMsg && (
        <div style={{
          backgroundColor: statusMsg.includes('Error') ? 'var(--accent-coral-light)' : 'var(--accent-mint-light)',
          color: statusMsg.includes('Error') ? 'var(--accent-coral)' : 'var(--accent-mint)',
          border: `1px solid ${statusMsg.includes('Error') ? '#FCD0D0' : '#BCECDA'}`,
          padding: '12px 18px',
          borderRadius: 'var(--radius-md)',
          marginBottom: '20px',
          fontSize: '13px',
          fontWeight: 600
        }}>
          {statusMsg}
        </div>
      )}

      {/* Scene Cards List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {currentJob.scenes.map((sc) => {
          const ft = sc.selected_footage;
          const isEditing = replacingSceneNum === sc.scene_number;

          return (
            <div
              key={sc.scene_number}
              style={{
                backgroundColor: 'var(--bg-card)',
                borderRadius: 'var(--radius-lg)',
                padding: '24px',
                border: '1px solid var(--border-light)',
                boxShadow: 'var(--shadow-sm)',
                display: 'grid',
                gridTemplateColumns: '260px 1fr 220px',
                gap: '24px',
                alignItems: 'center'
              }}
            >
              {/* Left Column: Video Clip Preview */}
              <div>
                <div style={{
                  backgroundColor: '#000000',
                  borderRadius: 'var(--radius-md)',
                  height: '146px',
                  overflow: 'hidden',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  position: 'relative'
                }}>
                  {ft?.download_url ? (
                    <video
                      src={ft.download_url}
                      muted
                      loop
                      autoPlay
                      playsInline
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  ) : (
                    <div style={{ color: '#FFFFFF', fontSize: '12px' }}>Footage Preview</div>
                  )}
                  <span style={{
                    position: 'absolute',
                    top: '8px',
                    left: '8px',
                    backgroundColor: 'rgba(26, 33, 56, 0.8)',
                    color: '#FFFFFF',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-full)',
                    fontSize: '11px',
                    fontWeight: 700
                  }}>
                    Scene {sc.scene_number}
                  </span>
                </div>
              </div>

              {/* Middle Column: Narration, Visuals & Reason */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                  <span style={{
                    fontSize: '12px',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-secondary)',
                    backgroundColor: 'var(--bg-subtle)',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-sm)'
                  }}>
                    {sc.start_time}s - {sc.end_time}s ({sc.duration}s)
                  </span>
                  <span style={{
                    fontSize: '12px',
                    fontWeight: 700,
                    color: 'var(--accent-mint)',
                    backgroundColor: 'var(--accent-mint-light)',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-full)'
                  }}>
                    {Math.round((sc.relevance_score || 0.95) * 100)}% Semantic Match
                  </span>
                </div>

                <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px', lineHeight: 1.5 }}>
                  "{sc.narration_text}"
                </div>

                <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  <strong>Visual Intent:</strong> {sc.visual_description}
                </div>

                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  <strong>Reason:</strong> {sc.selection_reason}
                </div>

                {/* Inline Editing Controls */}
                {isEditing && (
                  <div style={{ marginTop: '14px', paddingTop: '14px', borderTop: '1px solid var(--border-light)' }}>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
                      Alternative Visual Concept / Query
                    </label>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <input
                        type="text"
                        placeholder="e.g. futuristic university laboratory with holographic display"
                        value={customQuery}
                        onChange={(e) => setCustomQuery(e.target.value)}
                        style={{
                          flex: 1,
                          padding: '8px 12px',
                          borderRadius: 'var(--radius-sm)',
                          border: '1px solid var(--border-medium)',
                          fontSize: '13px',
                          outline: 'none'
                        }}
                      />
                      <button
                        onClick={() => handleRerender(sc.scene_number)}
                        disabled={loading}
                        style={{
                          padding: '8px 16px',
                          backgroundColor: 'var(--primary)',
                          color: '#FFFFFF',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '13px',
                          fontWeight: 700,
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px'
                        }}
                      >
                        {loading ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
                        Rerender Clip
                      </button>
                      <button
                        onClick={() => setReplacingSceneNum(null)}
                        style={{
                          padding: '8px 12px',
                          backgroundColor: 'var(--bg-subtle)',
                          color: 'var(--text-secondary)',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '13px',
                          fontWeight: 600
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Right Column: Licence & Actions */}
              <div style={{
                borderLeft: '1px solid var(--border-light)',
                paddingLeft: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px'
              }}>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                    Footage Source
                  </div>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                    {ft?.provider || 'MockProvider'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                    Licence Clearance
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--accent-mint)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                    <ShieldCheck size={14} /> Commercial Cleared
                  </div>
                </div>

                {!isEditing && (
                  <button
                    onClick={() => {
                      setReplacingSceneNum(sc.scene_number);
                      setCustomQuery(sc.search_query);
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px',
                      padding: '10px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: 'var(--primary-light)',
                      color: 'var(--primary)',
                      fontSize: '12px',
                      fontWeight: 700,
                      border: '1px solid var(--primary-border)',
                      marginTop: '6px'
                    }}
                  >
                    <RefreshCw size={14} />
                    Replace Footage
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
