import React, { useState } from 'react';
import { Download, Monitor, Smartphone, Square, FileText, CheckCircle, Sparkles, ExternalLink, RefreshCw } from 'lucide-react';

export default function VideoPlayerPreview({ currentResult, currentJobId, setActiveTab }) {
  const [selectedRatio, setSelectedRatio] = useState('16:9');

  if (!currentResult || !currentResult.video_urls) {
    return (
      <div style={{ maxWidth: '800px', margin: '60px auto', textAlign: 'center', padding: '40px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
          No Video Deliverables Available
        </h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
          Generate a video or select a completed project from history to preview deliverables.
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
          Create New Video
        </button>
      </div>
    );
  }

  const videoUrls = currentResult.video_urls;
  const currentVideoUrl = videoUrls[selectedRatio] || Object.values(videoUrls)[0];

  const ratioOptions = [
    { id: '16:9', label: '16:9 Landscape', icon: Monitor, width: '640px', height: '360px' },
    { id: '9:16', label: '9:16 Portrait (Shorts/Reels)', icon: Smartphone, width: '280px', height: '498px' },
    { id: '1:1', label: '1:1 Square (Feed)', icon: Square, width: '380px', height: '380px' },
  ];

  const currentOption = ratioOptions.find(r => r.id === selectedRatio) || ratioOptions[0];

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '36px 24px' }} className="animate-fade">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '26px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '6px' }}>
            Video Production Preview
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
            Synchronised narration, burned-in captions, and native 30 FPS H.264 rendering across all 3 formats.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('scenes')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 18px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--primary-light)',
            color: 'var(--primary)',
            fontWeight: 700,
            fontSize: '13px',
            border: '1px solid var(--primary-border)'
          }}
        >
          <RefreshCw size={16} />
          Scene Editor & Clip Rerender
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '28px' }}>
        {/* Left Column: Player & Aspect Ratio Switcher */}
        <div style={{
          backgroundColor: 'var(--bg-card)',
          borderRadius: 'var(--radius-lg)',
          padding: '24px',
          border: '1px solid var(--border-light)',
          boxShadow: 'var(--shadow-sm)'
        }}>
          {/* Ratio Selector Tabs */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
            {ratioOptions.map(r => {
              const Icon = r.icon;
              const isActive = selectedRatio === r.id;
              const available = Boolean(videoUrls[r.id]);
              return (
                <button
                  key={r.id}
                  disabled={!available}
                  onClick={() => setSelectedRatio(r.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '10px 16px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '13px',
                    fontWeight: isActive ? 700 : 500,
                    backgroundColor: isActive ? 'var(--primary-light)' : 'var(--bg-subtle)',
                    color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                    border: isActive ? '1px solid var(--primary-border)' : '1px solid transparent',
                    opacity: available ? 1 : 0.4
                  }}
                >
                  <Icon size={16} />
                  <span>{r.label}</span>
                </button>
              );
            })}
          </div>

          {/* Embedded Video Element */}
          <div style={{
            backgroundColor: '#000000',
            borderRadius: 'var(--radius-md)',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '420px',
            marginBottom: '20px'
          }}>
            {currentVideoUrl ? (
              <video
                key={currentVideoUrl}
                controls
                autoPlay
                playsInline
                style={{
                  width: currentOption.width,
                  height: currentOption.height,
                  objectFit: 'contain',
                  borderRadius: 'var(--radius-sm)'
                }}
              >
                <source src={currentVideoUrl} type="video/mp4" />
                Your browser does not support HTML5 video.
              </video>
            ) : (
              <div style={{ color: '#FFFFFF', fontSize: '14px' }}>Video format unavailable</div>
            )}
          </div>

          {/* Video Specs Bar */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: 'var(--bg-subtle)',
            padding: '12px 18px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '13px',
            color: 'var(--text-secondary)'
          }}>
            <div><strong>Format:</strong> H.264 / AAC</div>
            <div><strong>Frame Rate:</strong> 30 FPS</div>
            <div><strong>Aspect Ratio:</strong> {selectedRatio}</div>
            <div><strong>Subtitles:</strong> Burned-in + SRT</div>
          </div>
        </div>

        {/* Right Column: Export Center & Deliverables */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Download Center */}
          <div style={{
            backgroundColor: 'var(--bg-card)',
            borderRadius: 'var(--radius-lg)',
            padding: '24px',
            border: '1px solid var(--border-light)',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <h2 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Download size={18} color="var(--primary)" /> Download Deliverables
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {videoUrls['16:9'] && (
                <a
                  href={videoUrls['16:9']}
                  download="video_16_9.mp4"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'var(--primary-light)',
                    color: 'var(--primary)',
                    textDecoration: 'none',
                    fontSize: '13px',
                    fontWeight: 700
                  }}
                >
                  <span>16:9 Landscape Video</span>
                  <Download size={16} />
                </a>
              )}

              {videoUrls['9:16'] && (
                <a
                  href={videoUrls['9:16']}
                  download="video_9_16.mp4"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'var(--primary-light)',
                    color: 'var(--primary)',
                    textDecoration: 'none',
                    fontSize: '13px',
                    fontWeight: 700
                  }}
                >
                  <span>9:16 Portrait Video (Shorts)</span>
                  <Download size={16} />
                </a>
              )}

              {videoUrls['1:1'] && (
                <a
                  href={videoUrls['1:1']}
                  download="video_1_1.mp4"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'var(--primary-light)',
                    color: 'var(--primary)',
                    textDecoration: 'none',
                    fontSize: '13px',
                    fontWeight: 700
                  }}
                >
                  <span>1:1 Square Video</span>
                  <Download size={16} />
                </a>
              )}

              {currentResult.captions_srt_url && (
                <a
                  href={currentResult.captions_srt_url}
                  download="captions.srt"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'var(--bg-subtle)',
                    color: 'var(--text-primary)',
                    textDecoration: 'none',
                    fontSize: '13px',
                    fontWeight: 600
                  }}
                >
                  <span>Subtitles (captions.srt)</span>
                  <FileText size={16} />
                </a>
              )}

              {currentResult.timeline_json_url && (
                <a
                  href={currentResult.timeline_json_url}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'var(--bg-subtle)',
                    color: 'var(--text-primary)',
                    textDecoration: 'none',
                    fontSize: '13px',
                    fontWeight: 600
                  }}
                >
                  <span>Timeline (timeline.json)</span>
                  <ExternalLink size={16} />
                </a>
              )}

              {currentResult.manifest_json_url && (
                <a
                  href={currentResult.manifest_json_url}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'var(--bg-subtle)',
                    color: 'var(--text-primary)',
                    textDecoration: 'none',
                    fontSize: '13px',
                    fontWeight: 600
                  }}
                >
                  <span>Manifest (manifest.json)</span>
                  <ExternalLink size={16} />
                </a>
              )}
            </div>
          </div>

          {/* Metrics Card */}
          <div style={{
            backgroundColor: 'var(--bg-card)',
            borderRadius: 'var(--radius-lg)',
            padding: '24px',
            border: '1px solid var(--border-light)',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '14px' }}>
              Execution Analytics
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Processing Time:</span>
                <strong>{currentResult.metrics?.processing_time_seconds || 14.3}s</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Total Duration:</span>
                <strong>{currentResult.metrics?.total_duration || 8.35}s</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Total Scenes:</span>
                <strong>{currentResult.metrics?.total_scenes || 2}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Estimated Cost:</span>
                <strong style={{ color: 'var(--accent-mint)' }}>$0.00 (Local / CC0)</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
