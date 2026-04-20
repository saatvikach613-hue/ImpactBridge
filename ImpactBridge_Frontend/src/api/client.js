const h = () => ({ 'Content-Type': 'application/json', ...(localStorage.getItem('token') ? { Authorization: `Bearer ${localStorage.getItem('token')}` } : {}) });

export async function login(email, password) {
  const res = await fetch('/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) });
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

export const fetchKids             = async () => (await fetch('/kids/', { headers: h() })).json();
export const fetchUpcomingSessions = async () => (await fetch('/sessions/upcoming', { headers: h() })).json();
export const submitSessionLogs     = async (id, logs) => { const r = await fetch('/sessions/log', { method: 'POST', headers: h(), body: JSON.stringify({ session_id: id, logs }) }); if (!r.ok) throw new Error('Failed'); return r.json(); };
export const fetchDashboard        = async () => (await fetch('/dashboard/', { headers: h() })).json();
export const fetchAllChapters      = async () => (await fetch('/dashboard/chapters', { headers: h() })).json();
export const fetchPredictions      = async () => (await fetch('/ml/predictions', { headers: h() })).json();
export const fetchWishlist         = async () => (await fetch('/wishlist', { headers: h() })).json();
export const fetchFundDrives       = async () => (await fetch('/fund-drives', { headers: h() })).json();
export const makeDonation          = async (data) => { const r = await fetch('/donate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); if (!r.ok) throw new Error('Failed'); return r.json(); };
export const fetchKidHistory      = async (id) => (await fetch(`/sessions/history/${id}`, { headers: h() })).json();
export const fetchKidSessionHistory = async (id, limit = 10) => (await fetch(`/sessions/history/${id}?limit=${limit}`, { headers: h() })).json();
