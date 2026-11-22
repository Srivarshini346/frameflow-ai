import React, { useEffect, useState } from 'react';
import { ShieldCheck, Cpu, Database, CheckCircle2, Award, FileText, Server, Lock } from 'lucide-react';
import { getAnalytics } from '../api/client';

export default function AnalyticsLicenceHub() {
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    getAnalytics().then(setAnalytics).catch(console.error);
  }, []);

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '36px 24px' }} className="animate-fade">
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '26px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '6px' }}>
          Architecture, Analytics & Licence Governance
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
          Technical audit of media licences, model adapters, and native pipeline execution.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '28px' }}>
        {/* Modular Providers Status */}
        <div style={{
          backgroundColor: 'var(--bg-card)',
          borderRadius: 'var(--radius-lg)',
          padding: '24px',
          border: '1px solid var(--border-light)',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Server size={18} color="var(--primary)" /> Modular Footage Provider Adapters
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[
              {
                name: 'Pexels Video API Adapter',
                type: 'REST API Adapter (1080p stream preference, landscape/portrait)',
                licence: 'Pexels Commercial License (No attribution required)',
                status: analytics?.providers?.find(p => p.name === 'Pexels')?.status || 
                  (analytics?.providers?.find(p => p.name === 'Pexels')?.is_available ? 'Active' : 'No key configured')
              },
              {
                name: 'Pixabay Video API Adapter',
                type: 'REST API Adapter (Large MP4 stream preference)',
                licence: 'Pixabay Content License (Commercial use cleared)',
                status: analytics?.providers?.find(p => p.name === 'Pixabay')?.status || 
                  (analytics?.providers?.find(p => p.name === 'Pixabay')?.is_available ? 'Active' : 'No key configured')
              },
              {
                name: 'Synthetic Mock Footage Engine',
                type: 'Local High-Speed Procedural',
                licence: 'Creative Commons Zero (CC0 1.0)',
                status: 'Active (Always Available Offline Fallback)'
              }
            ].map((p, idx) => (
              <div
                key={idx}
                style={{
                  padding: '14px 16px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--bg-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>{p.name}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    {p.type} • {p.licence}
                  </div>
                </div>
                <span style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: p.status.includes('Active') ? 'var(--accent-mint-light)' : 'var(--bg-card)',
                  color: p.status.includes('Active') ? 'var(--accent-mint)' : 'var(--text-secondary)',
                  border: '1px solid var(--border-medium)'
                }}>
                  {p.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Commercial Licensing Enforcement */}
        <div style={{
          backgroundColor: 'var(--bg-card)',
          borderRadius: 'var(--radius-lg)',
          padding: '24px',
          border: '1px solid var(--border-light)',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={18} color="var(--accent-mint)" /> Commercial Licensing Audit Policy
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            <div style={{ display: 'flex', gap: '10px' }}>
              <CheckCircle2 size={18} color="var(--accent-mint)" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong style={{ color: 'var(--text-primary)' }}>Zero Copyrighted Web Scraping:</strong> Only verified commercial-cleared feeds (Pexels, Pixabay, or CC0 synthetic archives) are permitted into the pipeline.
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <CheckCircle2 size={18} color="var(--accent-mint)" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong style={{ color: 'var(--text-primary)' }}>Attribution Recorded in Manifest:</strong> Every video generates a verifiable manifest.json tracking creator name, source URL, and exact licence text.
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <CheckCircle2 size={18} color="var(--accent-mint)" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong style={{ color: 'var(--text-primary)' }}>Duplicate Clip Prevention:</strong> The footage service maintains a project clip registry ensuring no single clip is reused across scenes within the same video.
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <CheckCircle2 size={18} color="var(--accent-mint)" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong style={{ color: 'var(--text-primary)' }}>HMAC-SHA256 Webhook Security:</strong> External systems receiving completion webhooks are secured with cryptographic signatures via X-FrameFlow-Signature headers.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* System Technical Specs */}
      <div style={{
        backgroundColor: 'var(--bg-card)',
        borderRadius: 'var(--radius-lg)',
        padding: '24px',
        border: '1px solid var(--border-light)',
        boxShadow: 'var(--shadow-sm)'
      }}>
        <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Cpu size={18} color="var(--primary)" /> Pipeline Execution Infrastructure
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', fontSize: '13px' }}>
          <div style={{ padding: '14px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--bg-subtle)' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '11px', textTransform: 'uppercase', fontWeight: 700 }}>Compositor</div>
            <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>FFmpeg 9.0 (Gyan)</div>
          </div>
          <div style={{ padding: '14px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--bg-subtle)' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '11px', textTransform: 'uppercase', fontWeight: 700 }}>Frame Rate & Audio</div>
            <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>30 FPS / AAC 192kbps</div>
          </div>
          <div style={{ padding: '14px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--bg-subtle)' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '11px', textTransform: 'uppercase', fontWeight: 700 }}>Ratios Supported</div>
            <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>16:9, 9:16, 1:1</div>
          </div>
          <div style={{ padding: '14px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--bg-subtle)' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '11px', textTransform: 'uppercase', fontWeight: 700 }}>Languages Tested</div>
            <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>EN, Hindi, Tamil</div>
          </div>
        </div>
      </div>
    </div>
  );
}
