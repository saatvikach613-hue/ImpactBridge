import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { respondToRsvp } from '../api/client';

// ── One-tap RSVP ──────────────────────────────────────────────────────────────
// Volunteers land here from the Thursday reminder email:
//   /rsvp/:sessionId/:volunteerId?token=…&response=confirmed|declined
// No login. The signed token is what authorises the response.
// If the email link already carried a response, we submit immediately;
// otherwise we show two big buttons.

export default function RsvpPage() {
  const { sessionId, volunteerId } = useParams();
  const [params] = useSearchParams();
  const token    = params.get('token') || '';
  const preset   = params.get('response');

  const [state, setState] = useState(preset ? 'submitting' : 'choose'); // choose | submitting | done | error
  const [status, setStatus] = useState(preset || null);
  const [message, setMessage] = useState('');

  const submit = async (choice) => {
    setStatus(choice);
    setState('submitting');
    try {
      await respondToRsvp(sessionId, volunteerId, choice, token);
      setState('done');
    } catch (e) {
      setMessage(e.message);
      setState('error');
    }
  };

  useEffect(() => {
    if (preset === 'confirmed' || preset === 'declined') submit(preset);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div style={r.page}>
      <div style={r.card}>
        <div style={r.brand}><span style={r.logo}>IB</span> ImpactBridge · U&amp;I</div>

        {state === 'choose' && (
          <>
            <h1 style={r.h1}>Will you be at this Sunday's session?</h1>
            <p style={r.p}>Your students are counting on you. If you can't make it, letting us know now gives the coordinator time to arrange cover.</p>
            <div style={r.row}>
              <button style={{ ...r.btn, ...r.yes }} onClick={() => submit('confirmed')}>✓ I'll be there</button>
              <button style={{ ...r.btn, ...r.no }}  onClick={() => submit('declined')}>✗ Can't make it</button>
            </div>
          </>
        )}

        {state === 'submitting' && <p style={r.p}>Saving your response…</p>}

        {state === 'done' && status === 'confirmed' && (
          <>
            <h1 style={r.h1}>You're confirmed. Thank you!</h1>
            <p style={r.p}>See you Sunday. You can close this page.</p>
          </>
        )}
        {state === 'done' && status === 'declined' && (
          <>
            <h1 style={r.h1}>Got it, thanks for letting us know early.</h1>
            <p style={r.p}>Your coordinator has been notified and will arrange cover for your students.</p>
          </>
        )}

        {state === 'error' && (
          <>
            <h1 style={r.h1}>We couldn't record that.</h1>
            <p style={r.p}>{message}</p>
            <p style={r.small}>If the link is old or was forwarded, ask your coordinator to resend the reminder.</p>
          </>
        )}
      </div>
    </div>
  );
}

const r = {
  page:  { minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f9fafb', padding: 20 },
  card:  { width: '100%', maxWidth: 440, background: 'white', border: '1px solid #e5e7eb', borderRadius: 16, padding: '28px 26px' },
  brand: { display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: '#6b7280', marginBottom: 18 },
  logo:  { display: 'inline-flex', width: 26, height: 26, borderRadius: 7, background: '#dc2626', color: 'white', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700 },
  h1:    { fontSize: 20, fontWeight: 700, color: '#111827', marginBottom: 8, lineHeight: 1.25 },
  p:     { fontSize: 14, color: '#374151', lineHeight: 1.5, marginBottom: 16 },
  small: { fontSize: 12, color: '#9ca3af' },
  row:   { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 },
  btn:   { padding: '14px 12px', borderRadius: 10, fontSize: 15, fontWeight: 600, border: 'none', cursor: 'pointer' },
  yes:   { background: '#16a34a', color: 'white' },
  no:    { background: '#f3f4f6', color: '#374151' },
};
