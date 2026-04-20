import { useState, useEffect, useRef } from 'react';
import { fetchWishlist, fetchFundDrives, makeDonation } from '../api/client';

const QUOTES = [
  "Education is the most powerful weapon which you can use to change the world. — Nelson Mandela",
  "Every child deserves a champion who will never give up on them. — Rita Pierson",
  "The function of education is to teach one to think intensively and to think critically. — Martin Luther King Jr.",
  "Education is not the filling of a pail, but the lighting of a fire. — W.B. Yeats",
  "One child, one teacher, one book, one pen can change the world. — Malala Yousafzai",
  "Children must be taught how to think, not what to think. — Margaret Mead",
  "It takes a village to raise a child. — African Proverb",
  "The best gift you can give a child is the gift of learning. — U&I",
];

export default function WishlistPage() {
  const [items, setItems]       = useState([]);
  const [drives, setDrives]     = useState([]);
  const [loading, setLoading]   = useState(true);
  const [donating, setDonating] = useState(null);
  const [success, setSuccess]   = useState(null);
  const [quoteIdx, setQuoteIdx] = useState(0);
  const [fade, setFade]         = useState(true);

  useEffect(() => {
    Promise.all([fetchWishlist(), fetchFundDrives()])
      .then(([w, d]) => { setItems(w); setDrives(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  // Rotating quotes
  useEffect(() => {
    const interval = setInterval(() => {
      setFade(false);
      setTimeout(() => {
        setQuoteIdx(i => (i + 1) % QUOTES.length);
        setFade(true);
      }, 500);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  async function handleDonate(item) {
    const name  = prompt('Your name:');
    const email = prompt("Your email (we'll send you an update when the item is used):");
    if (!name || !email) return;
    setDonating(item.id);
    try {
      await makeDonation({ wishlist_item_id: item.id, amount: item.amount_needed, donor_name: name, donor_email: email });
      setSuccess(item.id);
      setItems(prev => prev.map(i => i.id === item.id ? { ...i, status: 'funded' } : i));
    } catch { alert('Something went wrong. Please try again.'); }
    finally { setDonating(null); }
  }

  const open   = items.filter(i => i.status === 'open');
  const funded = items.filter(i => i.status !== 'open');
  const needed = open.reduce((sum, i) => sum + i.amount_needed, 0);

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
      <span style={{ color: '#dc2626', fontSize: '16px' }}>Loading...</span>
    </div>
  );

  return (
    <div style={{ minHeight: '100vh', background: 'white' }}>

      {/* Moving quote banner */}
      <div style={{
        background: '#111827', padding: '10px 24px',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        minHeight: '44px',
      }}>
        <p style={{
          fontSize: '13px', color: '#9ca3af',
          fontStyle: 'italic', textAlign: 'center',
          opacity: fade ? 1 : 0,
          transition: 'opacity 0.5s ease',
          margin: 0,
        }}>
          "{QUOTES[quoteIdx]}"
        </p>
      </div>

      {/* Hero */}
      <div style={{ background: '#dc2626', padding: '52px 24px' }}>
        <div style={{ maxWidth: '680px', margin: '0 auto' }}>
          <div style={{ display: 'inline-block', padding: '3px 10px', borderRadius: '9999px', background: '#b91c1c', color: 'white', fontSize: '11px', fontWeight: '600', marginBottom: '14px', letterSpacing: '0.04em' }}>
            U&I · Visakhapatnam
          </div>
          <h1 style={{ fontSize: '36px', fontWeight: '700', color: 'white', lineHeight: '1.2', marginBottom: '12px' }}>
            Fund what a child actually needs
          </h1>
          <p style={{ fontSize: '15px', color: 'rgba(255,255,255,0.8)', lineHeight: '1.6', marginBottom: '28px', maxWidth: '500px' }}>
            Every item here was predicted by our ML model for a specific child — 4 weeks ahead of actual need. You see exactly what you're funding and who it reaches.
          </p>
          <div style={{ display: 'flex', gap: '28px' }}>
            {[
              { n: open.length,    l: 'items need funding' },
              { n: `₹${needed.toLocaleString('en-IN')}`, l: 'total needed' },
              { n: funded.length,  l: 'already funded' },
              { n: '106',          l: 'kids in program' },
            ].map((stat, i) => (
              <div key={i}>
                <div style={{ fontSize: '24px', fontWeight: '700', color: 'white' }}>{stat.n}</div>
                <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.7)' }}>{stat.l}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '36px 24px' }}>

        {/* Fund drives */}
        {drives.map(d => (
          <div key={d.id} style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '20px', marginBottom: '28px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
              <div>
                <div style={{ fontSize: '15px', fontWeight: '600', color: '#111827', marginBottom: '3px' }}>{d.title}</div>
                <div style={{ fontSize: '12px', color: '#9ca3af' }}>{d.start_date} → {d.end_date}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '20px', fontWeight: '700', color: '#dc2626' }}>₹{d.raised_amount.toLocaleString('en-IN')}</span>
                <span style={{ fontSize: '13px', color: '#9ca3af' }}> / ₹{d.goal_amount.toLocaleString('en-IN')}</span>
              </div>
            </div>
            <div style={{ height: '6px', background: '#e5e7eb', borderRadius: '3px', overflow: 'hidden', marginBottom: '6px' }}>
              <div style={{ width: `${Math.min((d.raised_amount / d.goal_amount) * 100, 100)}%`, height: '100%', background: '#dc2626', borderRadius: '3px', transition: 'width 0.8s ease' }} />
            </div>
            <div style={{ fontSize: '12px', color: '#9ca3af', textAlign: 'right' }}>{Math.round((d.raised_amount / d.goal_amount) * 100)}% funded</div>
          </div>
        ))}

        {/* U&I impact strip */}
        <div style={{ background: '#111827', borderRadius: '12px', padding: '20px 24px', marginBottom: '28px', display: 'flex', gap: '32px', justifyContent: 'center' }}>
          {[
            { n: '2,00,508', l: 'Lives impacted' },
            { n: '62,484',   l: 'Volunteers nationally' },
            { n: '40',       l: 'Cities across India' },
            { n: '80%',      l: 'Avg student attendance' },
          ].map((s, i) => (
            <div key={i} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '20px', fontWeight: '700', color: '#dc2626' }}>{s.n}</div>
              <div style={{ fontSize: '11px', color: '#9ca3af' }}>{s.l}</div>
            </div>
          ))}
        </div>

        {/* Wishlist items */}
        <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '16px' }}>What kids need right now</h2>
        {open.length === 0
          ? <div style={{ textAlign: 'center', padding: '48px', color: '#d1d5db' }}>
              <div style={{ fontSize: '36px', marginBottom: '10px' }}>🎉</div>
              <p>Everything is funded!</p>
            </div>
          : <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '12px' }}>
              {open.map(item => <Item key={item.id} item={item} onDonate={handleDonate} donating={donating === item.id} justFunded={success === item.id} />)}
            </div>
        }

        {funded.length > 0 && (
          <>
            <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '16px', marginTop: '40px' }}>Already funded ✓</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '12px' }}>
              {funded.map(item => <Item key={item.id} item={item} isFunded />)}
            </div>
          </>
        )}
      </div>

      <div style={{ background: '#111827', padding: '28px 24px', marginTop: '48px' }}>
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <div style={{ fontSize: '15px', fontWeight: '600', color: 'white', marginBottom: '6px' }}>ImpactBridge</div>
          <p style={{ fontSize: '12px', color: '#6b7280' }}>Built for U&I — 62,484 volunteers · 2,00,508 lives impacted · 40 cities (2024-25)</p>
        </div>
      </div>
    </div>
  );
}

function Item({ item, onDonate, donating, justFunded, isFunded }) {
  const f = isFunded || item.status !== 'open';
  return (
    <div style={{ background: 'white', border: `1.5px solid ${justFunded ? '#dc2626' : '#e5e7eb'}`, borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px', opacity: f ? 0.6 : 1, transition: 'border-color 0.2s' }}>
      <div style={{ fontSize: '28px' }}>{icon(item.item_name)}</div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: '14px', fontWeight: '600', color: '#111827', marginBottom: '3px', lineHeight: '1.4' }}>{item.item_name}</div>
        {item.description && <div style={{ fontSize: '12px', color: '#9ca3af', lineHeight: '1.5' }}>{item.description}</div>}
        {item.ml_generated && <span style={{ display: 'inline-block', marginTop: '5px', padding: '1px 7px', borderRadius: '4px', fontSize: '10px', fontWeight: '500', background: '#fff5f5', color: '#dc2626' }}>ML predicted</span>}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '10px', borderTop: '1px solid #f3f4f6' }}>
        <span style={{ fontSize: '18px', fontWeight: '700', color: '#111827' }}>₹{item.amount_needed.toLocaleString('en-IN')}</span>
        {!f
          ? <button style={{ padding: '7px 14px', background: '#dc2626', color: 'white', borderRadius: '8px', fontSize: '13px', fontWeight: '500', opacity: donating ? 0.6 : 1 }} onClick={() => onDonate(item)} disabled={donating}>
              {donating ? '...' : justFunded ? '✓ Done' : 'Fund this'}
            </button>
          : <span style={{ padding: '5px 12px', background: '#f3f4f6', color: '#6b7280', borderRadius: '8px', fontSize: '12px', fontWeight: '500' }}>✓ Funded</span>
        }
      </div>
    </div>
  );
}

function icon(name = '') {
  const n = name.toLowerCase();
  if (n.includes('sketch') || n.includes('colour')) return '🎨';
  if (n.includes('story') || n.includes('book'))    return '📚';
  if (n.includes('math') || n.includes('number'))   return '🔢';
  if (n.includes('english') || n.includes('phonics')) return '📝';
  if (n.includes('activity') || n.includes('kit'))  return '🎯';
  if (n.includes('life'))                            return '🌱';
  if (n.includes('geometry') || n.includes('compass')) return '📐';
  return '📦';
}
