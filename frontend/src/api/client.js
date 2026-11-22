const API_BASE = '/api/v1';

export async function createBrollJob(payload, idempotencyKey = null) {
  const headers = {
    'Content-Type': 'application/json',
  };
  if (idempotencyKey) {
    headers['Idempotency-Key'] = idempotencyKey;
  }

  const res = await fetch(`${API_BASE}/broll/jobs`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error?.message || `Job creation failed with status ${res.status}`);
  }
  return res.json();
}

export async function getJobStatus(jobId) {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch job status: ${res.status}`);
  }
  return res.json();
}

export async function getJobResult(jobId) {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/result`);
  if (!res.ok) {
    throw new Error(`Failed to fetch job result: ${res.status}`);
  }
  return res.json();
}

export async function replaceSceneClip(jobId, sceneNumber, replaceData) {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/scenes/${sceneNumber}/replace`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(replaceData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || `Scene replacement failed: ${res.status}`);
  }
  return res.json();
}

export async function listRecentJobs() {
  const res = await fetch(`${API_BASE}/jobs`);
  if (!res.ok) {
    return [];
  }
  return res.json();
}

export async function getAnalytics() {
  const res = await fetch(`${API_BASE}/analytics`);
  if (!res.ok) {
    return {};
  }
  return res.json();
}

export async function getHealthStatus() {
  const res = await fetch('/health');
  if (!res.ok) {
    return { status: 'down' };
  }
  return res.json();
}
