import { useState } from 'react';
import { login, getRole } from '../api/client';

export default function LoginPage() {
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(email, password);
      const role = getRole();
      if (role === 'coordinator') window.location.href = '/dashboard';
      else if (role === 'volunteer') window.location.href = '/session';
      else window.location.href = '/wishlist';
    } catch {
      setError('Incorrect email or password. Try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={s.page}>
      <div style={s.left}>
        <div style={s.brand}>
          <div style={s.logo}>IB</div>
          <h1 style={s.brandName}>ImpactBridge</h1>
          <p style={s.brandTagline}>Built for U&I — empowering 62,484 volunteers across 40 cities</p>
        </div>
        <div style={s.stats}>
          {[
            { n: '2,00,508', l: 'Lives impacted' },
            { n: '4,200',    l: 'Students in Teach' },
            { n: '80%',      l: 'Avg attendance' },
          ].map(stat => (
            <div key={stat.l} style={s.stat}>
              <span style={s.statNum}>{stat.n}</span>
              <span style={s.statLabel}>{stat.l}</span>
            </div>
          ))}
        </div>
        <p style={s.quote}>
          "Every child has something that unlocks them. This platform makes sure that insight never disappears."
        </p>
      </div>

      <div style={s.right}>
        <div style={s.card}>
          <h2 style={s.cardTitle}>Welcome back</h2>
          <p style={s.cardSub}>Sign in to your ImpactBridge account</p>

          {error && <div style={s.error}>{error}</div>}

          <form onSubmit={handleSubmit} style={s.form}>
            <div style={s.field}>
              <label style={s.label}>Email</label>
              <input
                style={s.input}
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
              />
            </div>
            <div style={s.field}>
              <label style={s.label}>Password</label>
              <input
                style={s.input}
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>
            <button style={{ ...s.btn, opacity: loading ? 0.7 : 1 }} disabled={loading}>
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div style={s.hints}>
            <p style={s.hintTitle}>Demo credentials</p>
            {[
              { role: 'Coordinator', email: 'coord_0_0@impactbridge.org', pass: 'coord123' },
              { role: 'Volunteer',   email: 'vol_0@impactbridge.org',     pass: 'vol123'   },
              { role: 'Donor',       email: 'donor_0@example.com',        pass: 'donor123' },
            ].map(h => (
              <div key={h.role} style={s.hint} onClick={() => { setEmail(h.email); setPassword(h.pass); }}>
                <span style={s.hintRole}>{h.role}</span>
                <span style={s.hintEmail}>{h.email}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

const s = {
  page:       { display: 'flex', minHeight: '100vh' },
  left: {
    flex: 1,
    background: 'var(--primary-700)',
    padding: '48px',
    display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
  },
  brand:      { display: 'flex', flexDirection: 'column', gap: '12px' },
  logo: {
    width: '48px', height: '48px', borderRadius: 'var(--radius-lg)',
    background: 'var(--primary-500)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: '18px', fontWeight: '700', color: 'white',
  },
  brandName:  { fontSize: '28px', fontWeight: '700', color: 'white' },
  brandTagline: { fontSize: '14px', color: 'var(--primary-100)', maxWidth: '300px', lineHeight: '1.5' },
  stats:      { display: 'flex', flexDirection: 'column', gap: '20px' },
  stat:       { display: 'flex', flexDirection: 'column', gap: '2px' },
  statNum:    { fontSize: '32px', fontWeight: '700', color: 'white' },
  statLabel:  { fontSize: '12px', color: 'var(--primary-100)', letterSpacing: '0.04em' },
  quote: {
    fontSize: '13px', color: 'var(--primary-100)',
    fontStyle: 'italic', lineHeight: '1.6',
    borderTop: '1px solid rgba(255,255,255,0.15)', paddingTop: '20px',
  },
  right: {
    width: '440px', background: 'var(--white)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    padding: '48px 40px',
  },
  card:       { width: '100%' },
  cardTitle:  { fontSize: '24px', fontWeight: '700', color: 'var(--gray-900)', marginBottom: '6px' },
  cardSub:    { fontSize: '14px', color: 'var(--gray-500)', marginBottom: '28px' },
  error: {
    background: 'var(--primary-100)', color: 'var(--primary-800)',
    padding: '10px 14px', borderRadius: 'var(--radius-md)',
    fontSize: '13px', marginBottom: '16px',
  },
  form:  { display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '28px' },
  field: { display: 'flex', flexDirection: 'column', gap: '5px' },
  label: { fontSize: '13px', fontWeight: '500', color: 'var(--gray-700)' },
  input: {
    padding: '10px 12px', border: '1.5px solid var(--gray-200)',
    borderRadius: 'var(--radius-md)', fontSize: '14px',
    color: 'var(--gray-900)', background: 'var(--white)',
  },
  btn: {
    padding: '11px', background: 'var(--primary-600)', color: 'white',
    borderRadius: 'var(--radius-md)', fontSize: '14px', fontWeight: '600',
    marginTop: '4px', border: 'none',
  },
  hints:     { borderTop: '1px solid var(--gray-200)', paddingTop: '20px' },
  hintTitle: { fontSize: '11px', fontWeight: '600', color: 'var(--gray-400)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '10px' },
  hint: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '8px 10px', borderRadius: 'var(--radius-md)',
    cursor: 'pointer', marginBottom: '4px', background: 'var(--gray-50)',
  },
  hintRole:  { fontSize: '13px', fontWeight: '500', color: 'var(--primary-600)' },
  hintEmail: { fontSize: '12px', color: 'var(--gray-400)' },
};
