import React from 'react';
import { PlusCircle, Sparkles, Film, CheckCircle2, Clock, ArrowRight, ShieldCheck, Cpu } from 'lucide-react';

export default function Dashboard({ setActiveTab, setScriptPreset, jobs }) {
  const completedCount = jobs.filter(j => j.status === 'succeeded').length;
  const runningCount = jobs.filter(j => j.status === 'running' || j.status === 'queued').length;

  const samplePresets = [
    {
      title: "AI in Modern Education",
      desc: "Abstract concepts translated into vibrant classroom and laptop interaction visuals.",
      script: "Technology is transforming the way students learn. Artificial intelligence makes education more personalised, adapting interactive lessons to every individual pace.",
      lang: "en"
    },
    {
      title: "Clean Energy Transition",
      desc: "Environmental vision with solar panels, wind turbines, and smart power grids.",
      script: "Renewable energy powers the sustainable cities of tomorrow. Wind turbines and solar infrastructure replace fossil fuels to safeguard our planet.",
      lang: "en"
    },
    {
      title: "Hindi Voiceover Demo (हिंदी)",
      desc: "Multilingual narration synthesized and synchronized for Indian educational content.",
      script: "प्रौद्योगिकी शिक्षा के भविष्य को पूरी तरह बदल रही है। आधुनिक कृत्रिम बुद्धिमत्ता हर छात्र के लिए व्यक्तिगत सीखने के अवसर पैदा करती है।",
      lang: "hi"
    },
    {
      title: "Tamil Voiceover Demo (தமிழ்)",
      desc: "Regional South Indian voiceover with timestamped scene cut transitions.",
      script: "தொழில்நுட்பம் மாணவர்களின் கற்றல் முறையை மாற்றுகிறது. நவீன செயற்கை நுண்ணறிவு அனைவருக்கும் சிறந்த கல்வி வாய்ப்பை உருவாக்குகிறது.",
      lang: "ta"
    }
  ];

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '36px 24px', width: '100%', boxSizing: 'border-box' }} className="animate-fade">
      {/* Hero Welcome Banner */}
      <div style={{
        backgroundColor: 'var(--bg-card)',
        borderRadius: 'var(--radius-lg)',
        padding: '36px 40px',
        border: '1px solid var(--border-light)',
        boxShadow: 'var(--shadow-sm)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #FFFFFF 0%, #FAF8FF 100%)',
        marginBottom: '32px'
      }}>
        <div>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '4px 12px',
            borderRadius: 'var(--radius-full)',
            backgroundColor: 'var(--primary-light)',
            color: 'var(--primary)',
            fontSize: '12px',
            fontWeight: 700,
            marginBottom: '12px'
          }}>
            <Sparkles size={14} /> IncuBrix PS3 Engine – Full Feature Edition
          </div>
          <h1 style={{ fontSize: '30px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '8px' }}>
            Transform Scripts & Voiceovers into Cinematic B-roll
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '15px', maxWidth: '640px', lineHeight: 1.6 }}>
            Meaning-based scene segmentation, verified commercial footage matching, multi-lingual narration (English, Hindi, Tamil), and native FFmpeg multi-aspect rendering.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('create')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            backgroundColor: 'var(--primary)',
            color: '#FFFFFF',
            padding: '14px 26px',
            borderRadius: 'var(--radius-md)',
            fontSize: '15px',
            fontWeight: 700,
            boxShadow: '0 4px 14px rgba(124, 110, 230, 0.4)',
            transition: 'all 0.2s ease',
            whiteSpace: 'nowrap'
          }}
          onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'var(--primary-hover)'}
          onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'var(--primary)'}
        >
          <PlusCircle size={20} />
          Create New Video
        </button>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '36px', width: '100%' }}>
        {[
          { label: 'Total Projects', val: jobs.length, icon: Film, color: 'var(--primary)', bg: 'var(--primary-light)' },
          { label: 'Completed Videos', val: completedCount, icon: CheckCircle2, color: 'var(--accent-mint)', bg: 'var(--accent-mint-light)' },
          { label: 'Processing Jobs', val: runningCount, icon: Clock, color: 'var(--accent-peach)', bg: 'var(--accent-peach-light)' },
          { label: 'Commercial Clearance', val: '100% Cleared', icon: ShieldCheck, color: 'var(--secondary-text)', bg: 'var(--secondary)' },
        ].map((m, idx) => {
          const Icon = m.icon;
          return (
            <div key={idx} style={{
              backgroundColor: 'var(--bg-card)',
              padding: '24px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-light)',
              boxShadow: 'var(--shadow-sm)',
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
              minWidth: 0,
              boxSizing: 'border-box'
            }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: m.bg,
                color: m.color,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                <Icon size={24} />
              </div>
              <div style={{ minWidth: 0, overflow: 'hidden' }}>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 600 }}>{m.label}</div>
                <div style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)', marginTop: '2px' }}>{m.val}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick-Start Presets */}
      <div style={{ marginBottom: '36px', width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>Quick Start Demonstration Presets</h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Click any sample to populate the studio and generate verified videos instantly.</p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', width: '100%' }}>
          {samplePresets.map((sample, idx) => (
            <div
              key={idx}
              onClick={() => {
                setScriptPreset(sample);
                setActiveTab('create');
              }}
              style={{
                backgroundColor: 'var(--bg-card)',
                padding: '22px 24px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-light)',
                boxShadow: 'var(--shadow-sm)',
                minWidth: 0,
                boxSizing: 'border-box',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                position: 'relative'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.borderColor = 'var(--primary-border)';
                e.currentTarget.style.boxShadow = 'var(--shadow-md)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-light)';
                e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>{sample.title}</span>
                <span style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: sample.lang === 'en' ? 'var(--secondary)' : 'var(--accent-peach-light)',
                  color: sample.lang === 'en' ? 'var(--secondary-text)' : 'var(--accent-peach)'
                }}>
                  {sample.lang.toUpperCase()} Narration
                </span>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '12px', lineHeight: 1.5 }}>
                {sample.desc}
              </p>
              <div style={{
                fontSize: '12px',
                fontFamily: 'var(--font-mono)',
                backgroundColor: 'var(--bg-subtle)',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-secondary)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                "{sample.script}"
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
