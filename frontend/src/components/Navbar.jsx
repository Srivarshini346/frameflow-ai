import React from 'react';
import { Video, Layers, Clock, Sliders, Award, FileText, CheckCircle2, AlertCircle } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, health }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Layers },
    { id: 'create', label: 'Create Studio', icon: Video },
    { id: 'timeline', label: 'Timeline Studio', icon: Sliders },
    { id: 'workspace', label: 'Processing', icon: Clock },
    { id: 'preview', label: 'Export Center', icon: Video },
    { id: 'history', label: 'History', icon: FileText },
    { id: 'analytics', label: 'Licences & Tech', icon: Award },
    { id: 'quality', label: 'Quality Report', icon: CheckCircle2 },
  ];

  const isHealthy = health?.status === 'healthy';

  return (
    <header style={{
      backgroundColor: 'var(--bg-card)',
      borderBottom: '1px solid var(--border-light)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      boxShadow: 'var(--shadow-sm)'
    }}>
      <div style={{
        maxWidth: '1440px',
        margin: '0 auto',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '70px'
      }}>
        {/* Brand identity */}
        <div 
          onClick={() => setActiveTab('dashboard')}
          style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
        >
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFFFFF',
            boxShadow: '0 4px 10px rgba(124, 110, 230, 0.35)'
          }}>
            <Video size={22} />
          </div>
          <div>
            <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
              FrameFlow <span style={{ color: 'var(--primary)' }}>AI</span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 500, marginTop: '-2px' }}>
              Intelligent B-roll Studio
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 14px',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '13px',
                  fontWeight: isActive ? 600 : 500,
                  color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                  backgroundColor: isActive ? 'var(--primary-light)' : 'transparent',
                  transition: 'all 0.15s ease',
                  border: isActive ? '1px solid var(--primary-border)' : '1px solid transparent'
                }}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* System Health Pill with Tooltip */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            title={
              health?.details ||
              (health?.providers_summary?.pexels_configured || health?.providers_summary?.pixabay_configured
                ? "All systems operational (Pexels / Pixabay stock footage active)"
                : "No PEXELS_API_KEY: using gradient fallback. Set keys in .env to enable real stock footage.")
            }
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: 'var(--radius-full)',
              backgroundColor: isHealthy ? 'var(--accent-mint-light)' : 'var(--accent-coral-light)',
              color: isHealthy ? 'var(--accent-mint)' : 'var(--accent-coral)',
              fontSize: '12px',
              fontWeight: 600,
              border: `1px solid ${isHealthy ? '#BCECDA' : '#FCD0D0'}`,
              cursor: 'help'
            }}
          >
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: isHealthy ? 'var(--accent-mint)' : 'var(--accent-coral)',
              display: 'inline-block'
            }} />
            <span>
              {isHealthy 
                ? (health?.providers_summary?.pexels_configured || health?.providers_summary?.pixabay_configured
                    ? 'All systems operational (Pexels active)'
                    : 'Engine Online (Procedural Fallback)')
                : 'Degraded'
              }
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
