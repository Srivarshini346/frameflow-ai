import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar.jsx';
import Dashboard from './components/Dashboard.jsx';
import CreateStudio from './components/CreateStudio.jsx';
import ProcessingWorkspace from './components/ProcessingWorkspace.jsx';
import VideoPlayerPreview from './components/VideoPlayerPreview.jsx';
import SceneTimelineEditor from './components/SceneTimelineEditor.jsx';
import MultiTrackStudio from './components/MultiTrackStudio.jsx';
import ProjectHistory from './components/ProjectHistory.jsx';
import AnalyticsLicenceHub from './components/AnalyticsLicenceHub.jsx';
import QualityEvaluationReport from './components/QualityEvaluationReport.jsx';

import { getHealthStatus, listRecentJobs, getJobResult, getJobStatus } from './api/client.js';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [health, setHealth] = useState(null);
  const [jobs, setJobs] = useState([]);
  
  // Active workflow state
  const [currentJobId, setCurrentJobId] = useState(null);
  const [currentJob, setCurrentJob] = useState(null);
  const [currentResult, setCurrentResult] = useState(null);
  const [scriptPreset, setScriptPreset] = useState(null);

  useEffect(() => {
    // Initial health and jobs fetch
    getHealthStatus().then(setHealth).catch(console.error);
    refreshJobs();

    const interval = setInterval(() => {
      getHealthStatus().then(setHealth).catch(console.error);
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const refreshJobs = async () => {
    try {
      const data = await listRecentJobs();
      setJobs(data);
      // Auto-load latest succeeded job if no current result
      if (!currentJobId && data.length > 0) {
        const latestSuccess = data.find(j => j.status === 'succeeded');
        if (latestSuccess) {
          loadResultForJob(latestSuccess.job_id);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadResultForJob = async (jobId) => {
    try {
      setCurrentJobId(jobId);
      const jobData = await getJobStatus(jobId);
      setCurrentJob(jobData);
      if (jobData.status === 'succeeded') {
        const resData = await getJobResult(jobId);
        setCurrentResult(resData);
      }
    } catch (err) {
      console.error("Error loading job result:", err);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} health={health} />

      <main style={{ flex: 1, paddingBottom: '60px' }}>
        {activeTab === 'dashboard' && (
          <Dashboard
            setActiveTab={setActiveTab}
            setScriptPreset={setScriptPreset}
            jobs={jobs}
          />
        )}

        {activeTab === 'create' && (
          <CreateStudio
            scriptPreset={scriptPreset}
            setActiveTab={setActiveTab}
            setCurrentJobId={(id) => {
              setCurrentJobId(id);
              refreshJobs();
            }}
          />
        )}

        {activeTab === 'workspace' && (
          <ProcessingWorkspace
            currentJobId={currentJobId}
            setActiveTab={setActiveTab}
            loadResultForJob={loadResultForJob}
          />
        )}

        {activeTab === 'timeline' && (
          <MultiTrackStudio
            currentJob={currentJob}
            currentResult={currentResult}
            currentJobId={currentJobId}
            setCurrentJob={setCurrentJob}
            setCurrentResult={setCurrentResult}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'preview' && (
          <VideoPlayerPreview
            currentResult={currentResult}
            currentJobId={currentJobId}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'scenes' && (
          <SceneTimelineEditor
            currentJob={currentJob}
            currentJobId={currentJobId}
            setCurrentJob={setCurrentJob}
            setCurrentResult={setCurrentResult}
          />
        )}

        {activeTab === 'history' && (
          <ProjectHistory
            setActiveTab={setActiveTab}
            setCurrentJobId={setCurrentJobId}
            setCurrentResult={setCurrentResult}
          />
        )}

        {activeTab === 'analytics' && <AnalyticsLicenceHub />}

        {activeTab === 'quality' && <QualityEvaluationReport currentJob={currentJob} />}
      </main>

      <footer style={{
        borderTop: '1px solid var(--border-light)',
        padding: '20px 24px',
        backgroundColor: 'var(--bg-card)',
        textAlign: 'center',
        fontSize: '12px',
        color: 'var(--text-muted)'
      }}>
        <div>
          FrameFlow AI – Intelligent B-roll Studio • IncuBrix PS3 Technical Assessment
        </div>
        <div style={{ marginTop: '4px' }}>
          FFmpeg 9.0 • Python 3.11 FastAPI • Pure Light Theme • 100% Commercial Clearance
        </div>
      </footer>
    </div>
  );
}
