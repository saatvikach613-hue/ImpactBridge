// API client
// ==========
// All calls go through `api()` so the backend base URL is set in ONE place.
//
// - Local dev:  REACT_APP_API_URL is empty, CRA's "proxy" in package.json
//               forwards relative calls to http://localhost:8000.
// - Production: REACT_APP_API_URL is set in Vercel to the deployed backend.

// Deployed backend. Used automatically when the app is NOT running on localhost
// and REACT_APP_API_URL wasn't provided at build time, so a missing Vercel env var
// can't silently break the live demo (requests would otherwise hit Vercel itself).
const DEFAULT_PROD_API = 'https://impactbridge-22jw.onrender.com';

const isLocalhost = typeof window !== 'undefined'
  && /^(localhost|127\.0\.0\.1)$/.test(window.location.hostname);

function resolveApiBase() {
  const configured = (process.env.REACT_APP_API_URL || '').trim().replace(/\/$/, '');
  if (isLocalhost) return configured; // '' → CRA dev proxy to :8000
  // Guard against a misconfigured value that points back at the frontend itself
  // (e.g. the Vercel URL pasted by mistake) — that would 405 on every API call.
  const pointsAtSelf = !configured
    || configured === '/'
    || configured.includes(window.location.host);
  return pointsAtSelf ? DEFAULT_PROD_API : configured;
}

const API_BASE = resolveApiBase();

const api = (path) => `${API_BASE}${path}`;

const h = () => ({
  'Content-Type': 'application/json',
  ...(localStorage.getItem('token') ? { Authorization: `Bearer ${localStorage.getItem('token')}` } : {}),
});

async function getJson(path) {
  const res = await fetch(api(path), { headers: h() });
  if (res.status === 401) { logout(); return; }
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

export async function login(email, password) {
  const res = await fetch(api('/auth/login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error('Invalid credentials');
  const data = await res.json();
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('role', data.role);
  localStorage.setItem('name', data.full_name);
  localStorage.setItem('chapter_id', data.chapter_id);
  return data;
}

export const logout   = () => { localStorage.clear(); window.location.href = '/login'; };
export const getRole  = () => localStorage.getItem('role');
export const getName  = () => localStorage.getItem('name');

// ── Kids & sessions ──────────────────────────────────────────────────────────
export const fetchKids             = () => getJson('/kids/');
export const fetchUpcomingSessions = () => getJson('/sessions/upcoming');
export const fetchKidHistory       = (id) => getJson(`/sessions/history/${id}`);
export const fetchKidSessionHistory = (id, limit = 10) => getJson(`/sessions/history/${id}?limit=${limit}`);

export const submitSessionLogs = async (id, logs) => {
  const r = await fetch(api('/sessions/log'), {
    method: 'POST', headers: h(), body: JSON.stringify({ session_id: id, logs }),
  });
  if (!r.ok) throw new Error('Failed');
  return r.json();
};

// ── Dashboard & ML ───────────────────────────────────────────────────────────
export const fetchDashboard   = () => getJson('/dashboard/');
export const fetchAllChapters = () => getJson('/dashboard/chapters');
export const fetchAdoption    = () => getJson('/dashboard/adoption');
export const fetchAnalytics   = () => getJson('/dashboard/analytics');
export const fetchPredictions = () => getJson('/ml/predictions');

// ── Automation (coordinator only) ────────────────────────────────────────────
export const fetchAutomationHealth = () => getJson('/automation/health');
export const fetchAutomationLogs   = (limit = 20) => getJson(`/automation/logs?limit=${limit}`);
export const triggerAutomation = async (job) => {
  const r = await fetch(api(`/automation/trigger/${job}`), { method: 'POST', headers: h() });
  if (!r.ok) throw new Error('Trigger failed');
  return r.json();
};

// ── Donor portal (public) ────────────────────────────────────────────────────
export const fetchWishlist   = () => getJson('/wishlist');
export const fetchFundDrives = () => getJson('/fund-drives');
export const makeDonation = async (data) => {
  const r = await fetch(api('/donate'), {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error('Failed');
  return r.json();
};

// ── One-tap RSVP from email (public, token-protected) ────────────────────────
export const respondToRsvp = async (sessionId, volunteerId, status, token) => {
  const r = await fetch(api(`/sessions/${sessionId}/rsvp/${volunteerId}/respond`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, token }),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || 'Could not record your response');
  }
  return r.json();
};
