import React, { useState } from 'react';
import { Upload, Type, Mic, Sliders, ShieldAlert, Sparkles, Check, Film, FileAudio } from 'lucide-react';
import { createBrollJob } from '../api/client';

export default function CreateStudio({ scriptPreset, setActiveTab, setCurrentJobId }) {
  const [scriptText, setScriptText] = useState(
    scriptPreset?.script || "Technology is transforming the modern classroom. Artificial intelligence creates personalised learning for students."
  );
  const [inputMode, setInputMode] = useState('script'); // 'script' or 'audio'
  const [audioFile, setAudioFile] = useState(null);
  const [audioBase64, setAudioBase64] = useState(null);
  
  // Voice settings
  const [language, setLanguage] = useState(scriptPreset?.lang || 'en');
  const [speechRate, setSpeechRate] = useState(1.0);
  const [pitch, setPitch] = useState(0.0);

  // Aspect Ratios (all selected by default)
  const [aspectRatios, setAspectRatios] = useState(['16:9', '9:16', '1:1']);
  
  // Visual & Prompts
  const [visualStyle, setVisualStyle] = useState('cinematic');
  const [styleInstructions, setStyleInstructions] = useState('bright lighting, clean modern aesthetic, 4k');
  const [avoidKeywords, setAvoidKeywords] = useState('cartoon, dark, scary, violence, blurry');
  
  // Captions
  const [burnCaptions, setBurnCaptions] = useState(true);
  const [fontSize, setFontSize] = useState(32);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRatioToggle = (ratio) => {
    if (aspectRatios.includes(ratio)) {
      if (aspectRatios.length === 1) return; // Keep at least one
      setAspectRatios(aspectRatios.filter(r => r !== ratio));
    } else {
      setAspectRatios([...aspectRatios, ratio]);
    }
  };

  const handleAudioUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setAudioFile(file);
    const reader = new FileReader();
    reader.onload = (uploadEvent) => {
      const b64 = uploadEvent.target?.result?.toString().split(',')[1];
      setAudioBase64(b64);
    };
    reader.readAsDataURL(file);
  };

  const handleGenerate = async () => {
    setError(null);
    setLoading(true);

    try {
      const payload = {
        script_text: inputMode === 'script' ? scriptText : (scriptText || "Audio Voiceover Story"),
        audio_base64: inputMode === 'audio' ? audioBase64 : null,
        audio_filename: audioFile?.name || null,
        voice_config: {
          language,
          speech_rate: parseFloat(speechRate),
          pitch: parseFloat(pitch)
        },
        aspect_ratios: aspectRatios,
        style: visualStyle,
        style_instructions: styleInstructions,
        avoid_instructions: avoidKeywords.split(',').map(s => s.trim()).filter(Boolean),
        caption_config: {
          enabled: true,
          burned_in: burnCaptions,
          font_size: parseInt(fontSize)
        }
      };

      const idempotencyKey = `idemp_${Date.now()}_${Math.random().toString(36).substring(7)}`;
      const job = await createBrollJob(payload, idempotencyKey);
      setCurrentJobId(job.job_id);
      setActiveTab('workspace');
    } catch (err) {
      setError(err.message || "Failed to start generation job");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '36px 24px' }} className="animate-fade">
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '26px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '6px' }}>
          Video Production Studio
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
          Configure narration, style guidelines, aspect ratios, and captions to produce your AI B-roll video.
        </p>
      </div>

      {error && (
        <div style={{
          backgroundColor: 'var(--accent-coral-light)',
          border: '1px solid #FCD0D0',
          color: 'var(--accent-coral)',
          padding: '14px 18px',
          borderRadius: 'var(--radius-md)',
          marginBottom: '24px',
          fontSize: '14px',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <ShieldAlert size={18} />
          {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '28px' }}>
        {/* Left Column: Script / Audio */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Input Mode Selector */}
          <div style={{
            backgroundColor: 'var(--bg-card)',
            padding: '24px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-light)',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '18px' }}>
              <button
                onClick={() => setInputMode('script')}
                style={{
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '10px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '13px',
                  fontWeight: 600,
                  backgroundColor: inputMode === 'script' ? 'var(--primary-light)' : 'var(--bg-subtle)',
                  color: inputMode === 'script' ? 'var(--primary)' : 'var(--text-secondary)',
                  border: inputMode === 'script' ? '1px solid var(--primary-border)' : '1px solid transparent'
                }}
              >
                <Type size={16} /> Enter Text Script
              </button>
              <button
                onClick={() => setInputMode('audio')}
                style={{
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '10px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '13px',
                  fontWeight: 600,
                  backgroundColor: inputMode === 'audio' ? 'var(--primary-light)' : 'var(--bg-subtle)',
                  color: inputMode === 'audio' ? 'var(--primary)' : 'var(--text-secondary)',
                  border: inputMode === 'audio' ? '1px solid var(--primary-border)' : '1px solid transparent'
                }}
              >
                <Upload size={16} /> Upload Audio File
              </button>
            </div>

            {inputMode === 'script' ? (
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
                  Narration Script
                </label>
                <textarea
                  value={scriptText}
                  onChange={(e) => setScriptText(e.target.value)}
                  rows={6}
                  placeholder="Enter your script here. Our engine will intelligently parse sentences and match meaning-based B-roll..."
                  style={{
                    width: '100%',
                    padding: '14px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-medium)',
                    backgroundColor: 'var(--bg-card)',
                    fontSize: '14px',
                    color: 'var(--text-primary)',
                    lineHeight: 1.6,
                    resize: 'vertical',
                    outline: 'none'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'var(--primary)'}
                  onBlur={(e) => e.target.style.borderColor = 'var(--border-medium)'}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-muted)', marginTop: '6px' }}>
                  <span>{scriptText.split(/\s+/).filter(Boolean).length} words</span>
                  <span>{scriptText.length} characters</span>
                </div>
              </div>
            ) : (
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
                  Upload Voiceover Audio (MP3, WAV, M4A)
                </label>
                <div style={{
                  border: '2px dashed var(--border-medium)',
                  borderRadius: 'var(--radius-md)',
                  padding: '32px 20px',
                  textAlign: 'center',
                  backgroundColor: 'var(--bg-subtle)',
                  cursor: 'pointer',
                  position: 'relative'
                }}>
                  <input
                    type="file"
                    accept=".mp3,.wav,.m4a,.aac"
                    onChange={handleAudioUpload}
                    style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer', width: '100%', height: '100%' }}
                  />
                  <FileAudio size={36} color="var(--primary)" style={{ margin: '0 auto 10px' }} />
                  <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {audioFile ? audioFile.name : "Click or drag audio file here"}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {audioFile ? `${(audioFile.size / (1024 * 1024)).toFixed(2)} MB` : "Supports MP3, WAV, M4A up to 25MB"}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Voice Configuration */}
          <div style={{
            backgroundColor: 'var(--bg-card)',
            padding: '24px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-light)',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Mic size={18} color="var(--primary)" /> Voice & Multilingual Narration
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '18px' }}>
              {[
                { id: 'en', label: 'English (US/UK)' },
                { id: 'hi', label: 'Hindi (हिंदी)' },
                { id: 'ta', label: 'Tamil (தமிழ்)' },
              ].map(item => (
                <button
                  key={item.id}
                  onClick={() => setLanguage(item.id)}
                  style={{
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '13px',
                    fontWeight: 600,
                    backgroundColor: language === item.id ? 'var(--primary-light)' : 'var(--bg-subtle)',
                    color: language === item.id ? 'var(--primary)' : 'var(--text-secondary)',
                    border: language === item.id ? '1px solid var(--primary-border)' : '1px solid transparent'
                  }}
                >
                  {item.label}
                </button>
              ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  <span>Speech Rate</span>
                  <span style={{ color: 'var(--primary)' }}>{speechRate}x</span>
                </label>
                <input
                  type="range"
                  min="0.8"
                  max="1.4"
                  step="0.05"
                  value={speechRate}
                  onChange={(e) => setSpeechRate(e.target.value)}
                  style={{ width: '100%', accentColor: 'var(--primary)' }}
                />
              </div>

              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  <span>Pitch Adjustment</span>
                  <span style={{ color: 'var(--primary)' }}>{pitch > 0 ? `+${pitch}` : pitch}</span>
                </label>
                <input
                  type="range"
                  min="-3.0"
                  max="3.0"
                  step="0.5"
                  value={pitch}
                  onChange={(e) => setPitch(e.target.value)}
                  style={{ width: '100%', accentColor: 'var(--primary)' }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Aspect Ratios, Visual Styles & Captions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Target Formats (16:9, 9:16, 1:1) */}
          <div style={{
            backgroundColor: 'var(--bg-card)',
            padding: '24px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-light)',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Film size={18} color="var(--primary)" /> Target Aspect Ratios
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[
                { id: '16:9', title: '16:9 Landscape', desc: 'YouTube, Web, Desktop (1920x1080)' },
                { id: '9:16', title: '9:16 Portrait', desc: 'Instagram Reels, YouTube Shorts, TikTok (1080x1920)' },
                { id: '1:1', title: '1:1 Square', desc: 'Instagram Feeds, LinkedIn (1080x1080)' },
              ].map(ar => {
                const selected = aspectRatios.includes(ar.id);
                return (
                  <div
                    key={ar.id}
                    onClick={() => handleRatioToggle(ar.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '12px 14px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: selected ? 'var(--primary-light)' : 'var(--bg-subtle)',
                      border: selected ? '1px solid var(--primary-border)' : '1px solid transparent',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: 700, color: selected ? 'var(--primary)' : 'var(--text-primary)' }}>
                        {ar.title}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                        {ar.desc}
                      </div>
                    </div>
                    <div style={{
                      width: '20px',
                      height: '20px',
                      borderRadius: '4px',
                      backgroundColor: selected ? 'var(--primary)' : '#FFFFFF',
                      border: `1px solid ${selected ? 'var(--primary)' : 'var(--border-medium)'}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#FFFFFF'
                    }}>
                      {selected && <Check size={14} />}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Style & Avoid Instructions */}
          <div style={{
            backgroundColor: 'var(--bg-card)',
            padding: '24px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-light)',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <h2 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sliders size={18} color="var(--primary)" /> Visual Directives & Captions
            </h2>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Visual Style
              </label>
              <select
                value={visualStyle}
                onChange={(e) => setVisualStyle(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-medium)',
                  backgroundColor: 'var(--bg-card)',
                  fontSize: '13px',
                  color: 'var(--text-primary)',
                  outline: 'none'
                }}
              >
                <option value="cinematic">Cinematic 4K</option>
                <option value="realistic">Realistic / Modern</option>
                <option value="minimalist">Minimalist / Clean</option>
                <option value="dynamic">Dynamic High Energy</option>
                <option value="documentary">Documentary</option>
              </select>
            </div>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Avoid Keywords (Negative Prompts)
              </label>
              <input
                type="text"
                value={avoidKeywords}
                onChange={(e) => setAvoidKeywords(e.target.value)}
                placeholder="e.g. cartoon, dark, blurry"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-medium)',
                  backgroundColor: 'var(--bg-card)',
                  fontSize: '13px',
                  color: 'var(--text-primary)',
                  outline: 'none'
                }}
              />
            </div>

            {/* Captions Toggle */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '6px' }}>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>Burn-in Subtitles</div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Burn captions into output MP4</div>
              </div>
              <input
                type="checkbox"
                checked={burnCaptions}
                onChange={(e) => setBurnCaptions(e.target.checked)}
                style={{ width: '18px', height: '18px', accentColor: 'var(--primary)', cursor: 'pointer' }}
              />
            </div>
          </div>

          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              backgroundColor: 'var(--primary)',
              color: '#FFFFFF',
              padding: '16px',
              borderRadius: 'var(--radius-md)',
              fontSize: '16px',
              fontWeight: 800,
              boxShadow: '0 4px 16px rgba(124, 110, 230, 0.45)',
              transition: 'all 0.2s ease',
              opacity: loading ? 0.7 : 1,
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
            onMouseOver={(e) => !loading && (e.currentTarget.style.backgroundColor = 'var(--primary-hover)')}
            onMouseOut={(e) => !loading && (e.currentTarget.style.backgroundColor = 'var(--primary)')}
          >
            <Sparkles size={20} />
            {loading ? "Initializing Engine..." : "Generate AI B-roll Video"}
          </button>
        </div>
      </div>
    </div>
  );
}
