import React, { useState, useRef, useEffect } from 'react';
import {
  Play, Pause, SkipBack, SkipForward, Volume2, Maximize2, RotateCcw,
  Sparkles, Wand2, Subtitles, Layers, Scissors, Copy, Trash2,
  Download, Film, Music, Type, CheckCircle2, ShieldCheck, RefreshCw,
  Search, Plus, Eye, Monitor, Smartphone, Square, Sliders, ChevronRight
} from 'lucide-react';
import { replaceSceneClip, getJobResult } from '../api/client';

export default function MultiTrackStudio({ currentJob, currentResult, currentJobId, setCurrentJob, setCurrentResult, setActiveTab }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [selectedRatio, setSelectedRatio] = useState('16:9');
  const [activeSceneIndex, setActiveSceneIndex] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [aiAssistantTab, setAiAssistantTab] = useState('assistant'); // 'assistant' or 'properties'
  const [isRerendering, setIsRerendering] = useState(false);
  const [notification, setNotification] = useState(null);
  const [customVisualQuery, setCustomVisualQuery] = useState('');

  const videoRef = useRef(null);
  const timelineRef = useRef(null);

  const scenes = currentJob?.scenes || [];
  const totalDuration = scenes.length > 0 ? scenes[scenes.length - 1].end_time : 10.0;
  const activeScene = scenes[activeSceneIndex] || scenes[0];

  const videoUrls = currentResult?.video_urls || {};
  const currentVideoUrl = videoUrls[selectedRatio] || Object.values(videoUrls)[0] || '';

  // Synchronize playback time
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const t = videoRef.current.currentTime;
      setCurrentTime(t);

      // Find active scene based on time
      const scIdx = scenes.findIndex(s => t >= s.start_time && t <= s.end_time);
      if (scIdx !== -1 && scIdx !== activeSceneIndex) {
        setActiveSceneIndex(scIdx);
      }
    }
  };

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const seekTo = (time) => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.max(0, Math.min(time, totalDuration));
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleTimelineClick = (e) => {
    if (!timelineRef.current) return;
    const rect = timelineRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const fraction = Math.max(0, Math.min(clickX / rect.width, 1));
    const targetTime = fraction * totalDuration;
    seekTo(targetTime);
  };

  const handleReplaceCurrentClip = async () => {
    if (!currentJobId || !activeScene) return;
    setIsRerendering(true);
    setNotification({ type: 'info', message: `Replacing footage and incrementally rerendering Scene ${activeScene.scene_number}...` });

    try {
      const updatedJob = await replaceSceneClip(currentJobId, activeScene.scene_number, {
        custom_query: customVisualQuery || activeScene.search_query || undefined
      });
      setCurrentJob(updatedJob);
      const updatedRes = await getJobResult(currentJobId);
      setCurrentResult(updatedRes);
      setNotification({ type: 'success', message: `Scene ${activeScene.scene_number} footage updated and video re-composited!` });
      setCustomVisualQuery('');
    } catch (err) {
      setNotification({ type: 'error', message: `Replacement failed: ${err.message}` });
    } finally {
      setIsRerendering(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const millis = Math.floor((seconds - Math.floor(seconds)) * 10);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${millis}`;
  };

  // Resolution dimensions for aspect ratios
  const ratioDimensions = {
    '16:9': { w: '580px', h: '326px', label: '1920 × 1080' },
    '9:16': { w: '220px', h: '390px', label: '1080 × 1920' },
    '1:1': { w: '320px', h: '320px', label: '1080 × 1080' }
  };
  const activeDim = ratioDimensions[selectedRatio] || ratioDimensions['16:9'];

  return (
    <div style={{ backgroundColor: 'var(--bg-main)', minHeight: 'calc(100vh - 70px)', display: 'flex', flexDirection: 'column' }}>
      {/* Studio Header Sub-bar */}
      <div style={{
        backgroundColor: '#FFFFFF',
        borderBottom: '1px solid var(--border-light)',
        padding: '10px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: 'var(--shadow-sm)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              backgroundColor: 'var(--primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FFFFFF'
            }}>
              <Film size={16} />
            </div>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 800, color: 'var(--text-primary)' }}>
                FrameFlow AI Studio
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                {currentJob?.request?.script_text ? `Project: "${currentJob.request.script_text.slice(0, 32)}..."` : "Active Project Timeline"}
              </div>
            </div>
          </div>

          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            backgroundColor: 'var(--primary-light)',
            color: 'var(--primary)',
            padding: '3px 10px',
            borderRadius: 'var(--radius-full)',
            fontSize: '11px',
            fontWeight: 700
          }}>
            <Sparkles size={12} /> AI Powered B-roll Engine
          </div>
        </div>

        {/* Aspect Ratio Switcher + Export Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ display: 'flex', backgroundColor: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)', padding: '3px' }}>
            {[
              { id: '16:9', icon: Monitor, label: '16:9' },
              { id: '9:16', icon: Smartphone, label: '9:16' },
              { id: '1:1', icon: Square, label: '1:1' }
            ].map(r => {
              const Icon = r.icon;
              const active = selectedRatio === r.id;
              return (
                <button
                  key={r.id}
                  onClick={() => setSelectedRatio(r.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '5px 10px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: active ? 700 : 500,
                    backgroundColor: active ? '#FFFFFF' : 'transparent',
                    color: active ? 'var(--primary)' : 'var(--text-secondary)',
                    boxShadow: active ? '0 1px 3px rgba(0,0,0,0.06)' : 'none'
                  }}
                >
                  <Icon size={14} />
                  <span>{r.label}</span>
                </button>
              );
            })}
          </div>

          <button
            onClick={() => setActiveTab('preview')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'var(--primary)',
              color: '#FFFFFF',
              padding: '8px 16px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '13px',
              fontWeight: 700,
              boxShadow: '0 4px 12px rgba(124, 110, 230, 0.35)'
            }}
          >
            <Download size={15} />
            Export Video
          </button>
        </div>
      </div>

      {notification && (
        <div style={{
          backgroundColor: notification.type === 'error' ? 'var(--accent-coral-light)' : 'var(--accent-mint-light)',
          color: notification.type === 'error' ? 'var(--accent-coral)' : 'var(--accent-mint)',
          padding: '8px 24px',
          fontSize: '12px',
          fontWeight: 600,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid var(--border-light)'
        }}>
          <span>{notification.message}</span>
          <button onClick={() => setNotification(null)} style={{ background: 'none', color: 'inherit', fontWeight: 800 }}>✕</button>
        </div>
      )}

      {/* Main 3-Column Studio Workspace */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '260px 1fr 340px', gap: '1px', backgroundColor: 'var(--border-light)', minHeight: '480px' }}>
        
        {/* Left Column: Media & Scene Library */}
        <div style={{ backgroundColor: '#FFFFFF', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '13px', fontWeight: 800, color: 'var(--text-primary)' }}>Media Library</span>
            <button
              onClick={() => setActiveTab('create')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '11px',
                color: 'var(--primary)',
                background: 'none',
                fontWeight: 700
              }}
            >
              <Plus size={14} /> New Script
            </button>
          </div>

          {/* Search bar */}
          <div style={{ position: 'relative' }}>
            <Search size={14} color="var(--text-muted)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
            <input
              type="text"
              placeholder="Filter scenes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '7px 10px 7px 30px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-medium)',
                fontSize: '12px',
                outline: 'none',
                backgroundColor: 'var(--bg-subtle)'
              }}
            />
          </div>

          {/* Scene Thumbnails List */}
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {scenes
              .filter(s => !searchQuery || s.narration_text.toLowerCase().includes(searchQuery.toLowerCase()))
              .map((sc, idx) => {
                const isSelected = activeSceneIndex === idx;
                const ft = sc.selected_footage;
                return (
                  <div
                    key={sc.scene_number}
                    onClick={() => {
                      setActiveSceneIndex(idx);
                      seekTo(sc.start_time);
                    }}
                    style={{
                      border: `2px solid ${isSelected ? 'var(--primary)' : 'var(--border-light)'}`,
                      borderRadius: 'var(--radius-sm)',
                      padding: '8px',
                      backgroundColor: isSelected ? 'var(--primary-light)' : '#FFFFFF',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{
                      height: '84px',
                      borderRadius: '4px',
                      backgroundColor: '#000000',
                      overflow: 'hidden',
                      marginBottom: '6px',
                      position: 'relative',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      {sc.thumbnail_url ? (
                        <img src={sc.thumbnail_url} alt={`Scene ${sc.scene_number}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      ) : ft?.download_url ? (
                        <video src={ft.download_url} muted loop style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      ) : (
                        <Film size={24} color="#888" />
                      )}
                      <span style={{
                        position: 'absolute',
                        top: '4px',
                        left: '4px',
                        backgroundColor: 'rgba(0,0,0,0.7)',
                        color: '#FFFFFF',
                        fontSize: '10px',
                        fontWeight: 700,
                        padding: '1px 5px',
                        borderRadius: '3px'
                      }}>
                        Scene {sc.scene_number}
                      </span>
                      <span style={{
                        position: 'absolute',
                        bottom: '4px',
                        right: '4px',
                        backgroundColor: 'rgba(0,0,0,0.7)',
                        color: '#FFFFFF',
                        fontSize: '9px',
                        fontFamily: 'var(--font-mono)',
                        padding: '1px 4px',
                        borderRadius: '3px'
                      }}>
                        {sc.duration}s
                      </span>
                    </div>

                    <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      "{sc.narration_text}"
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--accent-mint)', fontWeight: 600, marginTop: '2px' }}>
                      ✓ {Math.round((sc.relevance_score || 0.95) * 100)}% Match • {ft?.provider || 'Mock'}
                    </div>
                  </div>
                );
              })}
          </div>
        </div>

        {/* Center Column: Video Stage & Floating Controls */}
        <div style={{ backgroundColor: '#FAF9F6', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '20px', position: 'relative' }}>
          
          {/* Top Quick Actions Bar (Split, Duplicate, Delete, Subtitles) */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            backgroundColor: '#FFFFFF',
            padding: '6px 14px',
            borderRadius: 'var(--radius-full)',
            border: '1px solid var(--border-light)',
            boxShadow: 'var(--shadow-sm)',
            marginBottom: '16px'
          }}>
            <button style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: 'var(--text-secondary)', background: 'none' }}>
              <Scissors size={14} /> Split
            </button>
            <div style={{ width: '1px', height: '14px', backgroundColor: 'var(--border-medium)' }} />
            <button style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: 'var(--text-secondary)', background: 'none' }}>
              <Copy size={14} /> Duplicate
            </button>
            <div style={{ width: '1px', height: '14px', backgroundColor: 'var(--border-medium)' }} />
            <button style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: 'var(--text-secondary)', background: 'none' }}>
              <Type size={14} /> Captions
            </button>
            <div style={{ width: '1px', height: '14px', backgroundColor: 'var(--border-medium)' }} />
            <button
              onClick={() => handleReplaceCurrentClip()}
              disabled={isRerendering}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '12px',
                color: 'var(--primary)',
                fontWeight: 700,
                background: 'none'
              }}
            >
              <RefreshCw size={13} className={isRerendering ? "animate-spin" : ""} /> Rerender Clip
            </button>
          </div>

          {/* Video Preview Canvas */}
          <div style={{
            position: 'relative',
            width: activeDim.w,
            height: activeDim.h,
            backgroundColor: '#000000',
            borderRadius: 'var(--radius-md)',
            boxShadow: 'var(--shadow-lg)',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {currentVideoUrl ? (
              <video
                ref={videoRef}
                src={currentVideoUrl}
                onTimeUpdate={handleTimeUpdate}
                onEnded={() => setIsPlaying(false)}
                playsInline
                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              />
            ) : (
              <div style={{ color: '#FFFFFF', fontSize: '13px' }}>Rendering preview...</div>
            )}

            {/* Resolution Tag */}
            <span style={{
              position: 'absolute',
              top: '12px',
              right: '12px',
              backgroundColor: 'rgba(26, 33, 56, 0.75)',
              color: '#FFFFFF',
              fontSize: '11px',
              fontWeight: 700,
              padding: '3px 8px',
              borderRadius: 'var(--radius-full)',
              backdropFilter: 'blur(4px)'
            }}>
              {activeDim.label}
            </span>

            {/* Native Video Player (Captions burned-in directly into MP4 via FFmpeg, no duplicate overlay) */}
          </div>

          {/* Transport / Scrubber Controls Bar */}
          <div style={{
            marginTop: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
            backgroundColor: '#FFFFFF',
            padding: '8px 20px',
            borderRadius: 'var(--radius-full)',
            border: '1px solid var(--border-light)',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <button onClick={() => seekTo(0)} style={{ background: 'none', color: 'var(--text-secondary)' }}>
              <SkipBack size={16} />
            </button>

            <button
              onClick={togglePlay}
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                backgroundColor: 'var(--primary)',
                color: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 8px rgba(124, 110, 230, 0.4)'
              }}
            >
              {isPlaying ? <Pause size={18} /> : <Play size={18} style={{ marginLeft: '2px' }} />}
            </button>

            <button onClick={() => seekTo(totalDuration)} style={{ background: 'none', color: 'var(--text-secondary)' }}>
              <SkipForward size={16} />
            </button>

            <div style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', fontWeight: 600 }}>
              {formatTime(currentTime)} / {formatTime(totalDuration)}
            </div>
          </div>
        </div>

        {/* Right Column: AI Assistant & Inspector */}
        <div style={{ backgroundColor: '#FFFFFF', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Tabs: AI Assistant / Scene Inspector */}
          <div style={{ display: 'flex', borderBottom: '1px solid var(--border-light)', paddingBottom: '8px', gap: '10px' }}>
            <button
              onClick={() => setAiAssistantTab('assistant')}
              style={{
                fontSize: '13px',
                fontWeight: aiAssistantTab === 'assistant' ? 800 : 500,
                color: aiAssistantTab === 'assistant' ? 'var(--primary)' : 'var(--text-secondary)',
                borderBottom: aiAssistantTab === 'assistant' ? '2px solid var(--primary)' : 'none',
                paddingBottom: '4px',
                background: 'none'
              }}
            >
              AI Assistant
            </button>
            <button
              onClick={() => setAiAssistantTab('properties')}
              style={{
                fontSize: '13px',
                fontWeight: aiAssistantTab === 'properties' ? 800 : 500,
                color: aiAssistantTab === 'properties' ? 'var(--primary)' : 'var(--text-secondary)',
                borderBottom: aiAssistantTab === 'properties' ? '2px solid var(--primary)' : 'none',
                paddingBottom: '4px',
                background: 'none'
              }}
            >
              Scene Inspector
            </button>
          </div>

          {aiAssistantTab === 'assistant' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600 }}>
                Automated AI Video Operations
              </div>

              {[
                { title: 'Auto Edit (Meaning Splitting)', desc: 'Preserves clause boundaries & meaning', icon: Wand2, color: 'var(--primary)' },
                { title: 'Smart Transitions & Pacing', desc: 'Syllable-aligned audio sync (30 FPS)', icon: Sparkles, color: 'var(--accent-mint)' },
                { title: 'Auto Captions & Subtitles', desc: 'Burned-in H.264 subtitles & SRT', icon: Subtitles, color: '#E11D48' },
                { title: 'Commercial Licence Guard', desc: '100% verified CC0 & commercial usage', icon: ShieldCheck, color: 'var(--secondary-text)' },
              ].map((aiItem, i) => {
                const Icon = aiItem.icon;
                return (
                  <div
                    key={i}
                    style={{
                      padding: '12px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: 'var(--bg-subtle)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px'
                    }}
                  >
                    <div style={{
                      width: '34px',
                      height: '34px',
                      borderRadius: '8px',
                      backgroundColor: '#FFFFFF',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: aiItem.color,
                      boxShadow: '0 1px 3px rgba(0,0,0,0.06)'
                    }}>
                      <Icon size={18} />
                    </div>
                    <div>
                      <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)' }}>{aiItem.title}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{aiItem.desc}</div>
                    </div>
                  </div>
                );
              })}

              <button
                onClick={() => setActiveTab('quality')}
                style={{
                  marginTop: '10px',
                  backgroundColor: 'var(--primary)',
                  color: '#FFFFFF',
                  padding: '10px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '12px',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  boxShadow: '0 3px 10px rgba(124, 110, 230, 0.3)'
                }}
              >
                <Sparkles size={14} /> Open Quality Report
              </button>
            </div>
          ) : (
            /* Scene Properties Inspector */
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ fontSize: '12px', fontWeight: 800, color: 'var(--text-primary)' }}>
                Scene {activeScene?.scene_number || 1} Configuration
              </div>

              <div>
                <label style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Narration Phrase
                </label>
                <div style={{
                  padding: '8px 10px',
                  backgroundColor: 'var(--bg-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '12px',
                  color: 'var(--text-primary)',
                  lineHeight: 1.5
                }}>
                  "{activeScene?.narration_text}"
                </div>
              </div>

              <div>
                <label style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Visual Intent Description
                </label>
                <div style={{
                  padding: '8px 10px',
                  backgroundColor: 'var(--bg-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '11px',
                  color: 'var(--text-secondary)'
                }}>
                  {activeScene?.visual_description}
                </div>
              </div>

              <div>
                <label style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                  Replace Footage with New Concept
                </label>
                <input
                  type="text"
                  placeholder="e.g. futuristic classroom with robotics"
                  value={customVisualQuery}
                  onChange={(e) => setCustomVisualQuery(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-medium)',
                    fontSize: '12px',
                    outline: 'none',
                    marginBottom: '8px'
                  }}
                />
                <button
                  onClick={handleReplaceCurrentClip}
                  disabled={isRerendering}
                  style={{
                    width: '100%',
                    backgroundColor: 'var(--primary)',
                    color: '#FFFFFF',
                    padding: '8px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '12px',
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px'
                  }}
                >
                  <RefreshCw size={13} className={isRerendering ? "animate-spin" : ""} />
                  {isRerendering ? "Rerendering Clip..." : "Apply & Rerender Clip"}
                </button>
              </div>

              <div style={{ padding: '10px', backgroundColor: 'var(--accent-mint-light)', borderRadius: 'var(--radius-sm)', fontSize: '11px' }}>
                <div style={{ fontWeight: 700, color: 'var(--accent-mint)' }}>Commercial Licence Verified</div>
                <div style={{ color: 'var(--text-secondary)', marginTop: '2px' }}>
                  Source: {activeScene?.selected_footage?.provider || 'MockProvider'} (CC0 / Cleared)
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Multi-Track Timeline (Inspired by Image 1) */}
      <div style={{
        backgroundColor: '#FFFFFF',
        borderTop: '1px solid var(--border-light)',
        padding: '12px 24px 20px',
        boxShadow: '0 -2px 10px rgba(0,0,0,0.03)'
      }}>
        {/* Timeline Header Bar */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ fontSize: '12px', fontWeight: 800, color: 'var(--text-primary)' }}>Timeline Tracks</span>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{scenes.length} Meaning-Based Clips</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', color: 'var(--text-muted)' }}>
            <span>Zoom</span>
            <input type="range" min="1" max="3" step="0.2" defaultValue="1" style={{ width: '80px', accentColor: 'var(--primary)' }} />
          </div>
        </div>

        {/* Timecode Ruler & Ticks */}
        <div style={{ position: 'relative', height: '20px', borderBottom: '1px solid var(--border-light)', marginBottom: '8px', display: 'flex', justifyContent: 'space-between', fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
          {Array.from({ length: 9 }).map((_, idx) => {
            const t = (totalDuration / 8) * idx;
            return (
              <span key={idx} style={{ position: 'relative' }}>
                | {formatTime(t)}
              </span>
            );
          })}
        </div>

        {/* Interactive Multi-Track Canvas */}
        <div
          ref={timelineRef}
          onClick={handleTimelineClick}
          style={{ position: 'relative', display: 'flex', flexDirection: 'column', gap: '8px', cursor: 'pointer' }}
        >
          {/* Vertical Playhead Cursor */}
          <div style={{
            position: 'absolute',
            top: 0,
            bottom: 0,
            left: `${(currentTime / Math.max(0.1, totalDuration)) * 100}%`,
            width: '2px',
            backgroundColor: '#7C6EE6',
            zIndex: 30,
            pointerEvents: 'none'
          }}>
            <div style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: '#7C6EE6',
              transform: 'translateX(-4px)',
              marginTop: '-5px'
            }} />
          </div>

          {/* Track 1: Video B-roll Clips (Purple & Blue Blocks) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ width: '50px', fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Film size={12} /> Video
            </span>
            <div style={{ flex: 1, height: '38px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px', display: 'flex', overflow: 'hidden', padding: '2px', gap: '3px' }}>
              {scenes.map((sc, idx) => {
                const fraction = sc.duration / totalDuration;
                const colors = ['#8B7FE8', '#5E9AE8', '#42B8B0', '#7E6EE0'];
                const blockBg = colors[idx % colors.length];
                const isSelected = activeSceneIndex === idx;

                return (
                  <div
                    key={sc.scene_number}
                    onClick={(e) => {
                      e.stopPropagation();
                      setActiveSceneIndex(idx);
                      seekTo(sc.start_time);
                    }}
                    style={{
                      flex: fraction,
                      height: '100%',
                      backgroundColor: blockBg,
                      borderRadius: '4px',
                      padding: '4px 8px',
                      color: '#FFFFFF',
                      fontSize: '11px',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      boxShadow: isSelected ? '0 0 0 2px #1A2138' : 'none',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden'
                    }}
                  >
                    <span>Scene {sc.scene_number} ({sc.duration}s)</span>
                    <span style={{ fontSize: '9px', opacity: 0.85 }}>{sc.selected_footage?.provider || 'B-roll'}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Track 2: Audio Voiceover Narration Track (Pink / Coral) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ width: '50px', fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Music size={12} /> Audio
            </span>
            <div style={{ flex: 1, height: '28px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px', padding: '2px' }}>
              <div style={{
                width: '100%',
                height: '100%',
                backgroundColor: '#F472B6',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                padding: '0 10px',
                color: '#FFFFFF',
                fontSize: '10px',
                fontWeight: 700
              }}>
                Narration Track ({currentJob?.request?.voice_config?.language?.toUpperCase() || 'EN'} Voiceover)
              </div>
            </div>
          </div>

          {/* Track 3: Subtitles / Captions Track (Mint / Sky Blue) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ width: '50px', fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Type size={12} /> Text
            </span>
            <div style={{ flex: 1, height: '24px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px', display: 'flex', gap: '3px', padding: '2px' }}>
              {scenes.map((sc) => {
                const fraction = sc.duration / totalDuration;
                return (
                  <div
                    key={sc.scene_number}
                    style={{
                      flex: fraction,
                      height: '100%',
                      backgroundColor: '#38BDF8',
                      borderRadius: '3px',
                      padding: '0 6px',
                      color: '#FFFFFF',
                      fontSize: '9px',
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden'
                    }}
                  >
                    Subtitles Sc {sc.scene_number}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
