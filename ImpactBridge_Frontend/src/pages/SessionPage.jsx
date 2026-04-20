import { useState, useEffect } from 'react';
import { fetchKids, fetchUpcomingSessions, submitSessionLogs, logout, getName, fetchPredictions, fetchKidHistory, fetchKidSessionHistory } from '../api/client';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

const ENGLISH_LEVELS = ['letter', 'word', 'sentence', 'story', 'advanced'];
const MATH_LEVELS    = ['pre_number', 'number_recognition', 'basic_operations', 'advanced_operations', 'syllabus_aligned'];
const LEVEL_LABELS   = { letter: 'Letter', word: 'Word', sentence: 'Sentence', story: 'Story', advanced: 'Advanced', pre_number: 'Pre-Num', number_recognition: 'Num Recog', basic_operations: 'Basic Ops', advanced_operations: 'Adv Ops', syllabus_aligned: 'Syllabus' };
const RED = '#dc2626';

const RATINGS = [
  { value: 'struggling', emoji: '😕', label: 'Struggling', color: 'var(--primary-600)', bg: 'var(--primary-50)' },
  { value: 'okay',       emoji: '🙂', label: 'Okay',       color: 'var(--warning)',     bg: 'var(--warning-bg)' },
  { value: 'nailed_it',  emoji: '⭐', label: 'Nailed it',  color: 'var(--success)',     bg: 'var(--success-bg)' },
];

export default function SessionPage() {
  const [kids, setKids]             = useState([]);
  const [sessions, setSessions]     = useState([]);
  const [ratings, setRatings]       = useState({});
  const [sessionId, setSessionId]   = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [activeKid, setActiveKid]     = useState(null);
  const [view, setView]               = useState('log');
  const [loading, setLoading]       = useState(true);
  const [submitted, setSubmitted]   = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [histories, setHistories]   = useState({});
  const name = getName();

  const loadDashboardData = async () => {
    try {
      const [k, s, preds] = await Promise.all([fetchKids(), fetchUpcomingSessions(), fetchPredictions()]);
      setKids(k);
      setSessions(s);
      setPredictions(Array.isArray(preds) ? preds : []);
      if (s.length > 0) setSessionId(s[0].id);
      if (k.length > 0 && !activeKid) setActiveKid(k[0].id);

      // Fetch histories for assigned kids atomozically
      for (const kid of k) {
        fetchKidHistory(kid.id)
          .then(h => {
             setHistories(prev => ({ ...prev, [kid.id]: Array.isArray(h) ? h : [] }));
          })
          .catch(err => {
             console.error("Failed to fetch history for kid", kid.id, err);
             setHistories(prev => ({ ...prev, [kid.id]: [] }));
          });
      }
      setLoading(false);
    } catch (err) {
      console.error("Dashboard load failed", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

async function handleSubmit() {
  const logs = kids.filter(k => ratings[k.id]).map(k => ({
    kid_id: k.id, rating: ratings[k.id], subject: 'english', chapter_covered: 0,
  }));
  if (!logs.length) return;
  setSubmitting(true);
  try {
    await submitSessionLogs(sessionId, logs);
    // Wait 2 seconds for DB to commit before refreshing
    setTimeout(() => {
      Promise.all(kids.map(kid => fetchKidSessionHistory(kid.id, 12)))
        .then(results => {
          const h = {};
          kids.forEach((kid, i) => { h[kid.id] = results[i]; });
          setHistories(h);
        });
      fetchPredictions().then(p => setPredictions(Array.isArray(p) ? p : []));
    }, 2000);
    setSubmitted(true);
  } catch { alert('Failed to submit. Please try again.'); }
  finally { setSubmitting(false); }
}

  const ratedCount = Object.values(ratings).filter(Boolean).length;
  const allRated   = kids.length > 0 && ratedCount === kids.length;

  if (loading)   return <Loader />;
  if (submitted) return <SuccessScreen kids={kids} ratings={ratings} onReset={() => {
    setSubmitted(false);
    const init = {};
    kids.forEach(k => { init[k.id] = null; });
    setRatings(init);
  }} />;

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f9fafb' }}>
      {/* Sidebar */}
      <aside style={{ width: '196px', background: 'white', borderRight: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '20px 12px', position: 'sticky', top: 0, height: '100vh', flexShrink: 0 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '28px' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: '#dc2626', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: '700', color: 'white' }}>IB</div>
            <div>
              <div style={{ fontSize: '14px', fontWeight: '600', color: '#111827' }}>ImpactBridge</div>
              <div style={{ fontSize: '11px', color: '#9ca3af' }}>Volunteer</div>
            </div>
          </div>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            {[
              { id: 'log',      label: '📋 Log Session' },
              { id: 'progress', label: '📈 Progress' },
              { id: 'analysis', label: '🔍 Analysis' },
            ].map(tab => (
              <button key={tab.id}
                style={{ padding: '8px 12px', borderRadius: '8px', fontSize: '13px', background: view === tab.id ? '#fff5f5' : 'transparent', color: view === tab.id ? '#dc2626' : '#6b7280', textAlign: 'left', fontWeight: view === tab.id ? '500' : '400' }}
                onClick={() => setView(tab.id)}>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#fee2e2', color: '#dc2626', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: '600' }}>{name?.[0] || 'V'}</div>
            <span style={{ fontSize: '13px', color: '#374151' }}>{name?.split(' ')[0]}</span>
          </div>
          <button style={{ padding: '7px', background: 'transparent', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '12px', color: '#9ca3af' }} onClick={logout}>Sign out</button>
        </div>
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, overflow: 'auto' }}>
      <div style={{ background: '#dc2626', overflow: 'hidden', whiteSpace: 'nowrap' }}>
        <style>
          {`
            @keyframes marquee {
              0% { transform: translateX(100%); }
              100% { transform: translateX(-100%); }
            }
          `}
        </style>
        <div style={{ display: 'inline-block', padding: '10px 0', animation: 'marquee 25s linear infinite' }}>
          <p style={{ fontSize: '12px', color: 'white', fontStyle: 'italic', margin: 0, letterSpacing: '0.12em', display: 'inline-block', paddingRight: '100px', fontWeight: 'bold' }}>
            ✦ LEARN · LEAD · SUCCEED ✦
          </p>
          <p style={{ fontSize: '12px', color: 'white', fontStyle: 'italic', margin: 0, letterSpacing: '0.12em', display: 'inline-block', paddingRight: '100px', fontWeight: 'bold' }}>
            ✦ LEARN · LEAD · SUCCEED ✦
          </p>
          <p style={{ fontSize: '12px', color: 'white', fontStyle: 'italic', margin: 0, letterSpacing: '0.12em', display: 'inline-block', paddingRight: '100px', fontWeight: 'bold' }}>
            ✦ LEARN · LEAD · SUCCEED ✦
          </p>
        </div>
      </div>
      <header style={s.header}>
        <div style={s.headerLeft}>
          <div style={s.headerLogo}>IB</div>
          <div>
            <div style={s.headerTitle}>Today's session</div>
            <div style={s.headerSub}>{sessions[0] ? `${sessions[0].session_date}` : 'No session found'}</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button style={view === 'log' ? {...s.viewBtn, background: RED, color: 'white', border: `1px solid ${RED}`} : s.viewBtn} onClick={() => setView('log')}>Log Session</button>
          <button style={view === 'progress' ? {...s.viewBtn, background: RED, color: 'white', border: `1px solid ${RED}`} : s.viewBtn} onClick={() => setView('progress')}>Progress</button>
          <button 
            style={view === 'analysis' ? {...s.viewBtn, background: RED, color: 'white', border: `1px solid ${RED}`} : s.viewBtn} 
            onClick={() => setView('analysis')}
          >
            Analysis
          </button>
          <button style={s.logoutBtn} onClick={logout}>Sign out</button>
        </div>
      </header>

      {view === 'log' && <>
      <div style={s.progressBar}>
        <div style={{ ...s.progressFill, width: `${kids.length ? (ratedCount / kids.length) * 100 : 0}%` }} />
      </div>

      <div style={s.intro}>
        <p style={s.introText}>Hi <strong>{name?.split(' ')[0]}</strong> — tap how each kid did today</p>
        <span style={s.progressText}>{ratedCount}/{kids.length}</span>
      </div>

      <div style={s.kidList}>
        {kids.map(kid => (
          <KidCard key={kid.id} kid={kid} rating={ratings[kid.id]} onRate={v => setRatings(p => ({ ...p, [kid.id]: v }))} />
        ))}
      </div>

      <div style={{ padding: '20px 32px', marginTop: '12px' }}>
        <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: '#fee2e2', color: '#dc2626', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', fontWeight: '700' }}>C</div>
            <div>
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#111827' }}>Chapter Coordinator</div>
              <div style={{ fontSize: '11px', color: '#9ca3af' }}>Visakhapatnam · coord_0_0@impactbridge.org</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <a href="mailto:coord_0_0@impactbridge.org" style={{ padding: '7px 14px', background: '#fff5f5', color: '#dc2626', borderRadius: '8px', fontSize: '12px', fontWeight: '500', border: '1px solid #fee2e2', textDecoration: 'none' }}>
              📧 Email coordinator
            </a>
            <a href="https://wa.me/919100000000" target="_blank" rel="noreferrer" style={{ padding: '7px 14px', background: '#f0fdf4', color: '#16a34a', borderRadius: '8px', fontSize: '12px', fontWeight: '500', border: '1px solid #dcfce7', textDecoration: 'none' }}>
              💬 WhatsApp
            </a>
          </div>
        </div>
      </div>

      <div style={s.footer}>
        {!allRated && <p style={s.footerHint}>{kids.length - ratedCount} kid{kids.length - ratedCount !== 1 ? 's' : ''} left</p>}
        <button
          style={{ ...s.submitBtn, opacity: allRated && !submitting ? 1 : 0.45 }}
          onClick={handleSubmit}
          disabled={!allRated || submitting}
        >
          {submitting ? 'Submitting...' : 'Submit session'}
        </button>
      </div>
      </>}

      {view === 'progress' && (
        <div style={{ padding: '24px 32px' }}>
          {/* Kid selector */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', overflowX: 'auto' }}>
            {kids.map(kid => (
              <button key={kid.id}
                style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '7px 12px', borderRadius: '20px', background: activeKid === kid.id ? '#fff5f5' : 'white', border: activeKid === kid.id ? `1px solid ${RED}` : '1px solid #e5e7eb', flexShrink: 0 }}
                onClick={() => setActiveKid(kid.id)}>
                <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: `hsl(${kid.id * 47 % 360},55%,88%)`, color: `hsl(${kid.id * 47 % 360},55%,30%)`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: '700' }}>
                  {kid.name?.[0]}
                </div>
                <span style={{ fontSize: '12px', fontWeight: '500', color: '#374151' }}>{kid.name}</span>
              </button>
            ))}
          </div>

          {kids.filter(k => k.id === activeKid).map(kid => {
            const pred = predictions.find(p => p.kid_id === kid.id);
            const engLevel  = kid.english_level?.value || kid.english_level || 'letter';
            const mathLevel = kid.math_level?.value || kid.math_level || 'pre_number';
            const engIdx    = ENGLISH_LEVELS.indexOf(engLevel);
            const mathIdx   = MATH_LEVELS.indexOf(mathLevel);
            const predEngIdx  = ENGLISH_LEVELS.indexOf(pred?.predicted_eng_level || '');
            const predMathIdx = MATH_LEVELS.indexOf(pred?.predicted_math_level || '');

            return (
              <div key={kid.id} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

                {/* Kid header */}
                <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '14px', display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                  <div style={{ width: '44px', height: '44px', borderRadius: '50%', background: `hsl(${kid.id * 47 % 360},55%,88%)`, color: `hsl(${kid.id * 47 % 360},55%,30%)`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px', fontWeight: '700', flexShrink: 0 }}>
                    {kid.name?.[0]}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '16px', fontWeight: '700', color: '#111827' }}>{kid.name}</div>
                    <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '2px' }}>Age {kid.age} · {kid.learning_style} learner</div>
                    {kid.unlock_note && <div style={{ fontSize: '11px', color: RED, background: '#fff5f5', borderRadius: '4px', padding: '3px 8px', display: 'inline-block', marginTop: '4px' }}>💡 {kid.unlock_note}</div>}
                  </div>
                  {pred && (
                    <div style={{ padding: '4px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '600', background: pred.risk_level === 'high' ? '#fff5f5' : pred.risk_level === 'medium' ? '#fffbeb' : '#f0fdf4', color: pred.risk_level === 'high' ? RED : pred.risk_level === 'medium' ? '#d97706' : '#16a34a' }}>
                      {pred.risk_level} risk · {Math.round((pred.risk_score || 0) * 100)}%
                    </div>
                  )}
                </div>

                {/* English journey */}
                <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '16px' }}>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#111827', marginBottom: '14px' }}>📖 English Literacy Journey</div>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '4px' }}>
                    {ENGLISH_LEVELS.map((level, i) => {
                      const isPast      = i < engIdx;
                      const isCurrent   = i === engIdx;
                      const isPredicted = i === predEngIdx && predEngIdx > engIdx;
                      return (
                        <div key={level} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '5px' }}>
                          <div style={{ width: '34px', height: '34px', borderRadius: '50%', background: isCurrent ? RED : isPast ? '#fee2e2' : isPredicted ? '#fef3c7' : '#f3f4f6', border: isCurrent ? `2px solid ${RED}` : isPredicted ? '2px dashed #d97706' : '2px solid transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', color: isCurrent ? 'white' : isPast ? RED : isPredicted ? '#d97706' : '#9ca3af', fontWeight: isCurrent ? '700' : '400' }}>
                            {isCurrent ? '📍' : isPast ? '✓' : isPredicted ? '🎯' : i + 1}
                          </div>
                          <span style={{ fontSize: '9px', color: isCurrent ? RED : isPredicted ? '#d97706' : '#9ca3af', fontWeight: isCurrent || isPredicted ? '600' : '400', textAlign: 'center' }}>{LEVEL_LABELS[level]}</span>
                          {isCurrent   && <span style={{ fontSize: '8px', color: RED,      fontWeight: '600' }}>NOW</span>}
                          {isPredicted && <span style={{ fontSize: '8px', color: '#d97706', fontWeight: '600' }}>4WK</span>}
                        </div>
                      );
                    })}
                  </div>
                  <div style={{ marginTop: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontSize: '11px', color: '#9ca3af' }}>Progress through English levels</span>
                      <span style={{ fontSize: '11px', fontWeight: '600', color: '#374151' }}>{Math.round((engIdx / (ENGLISH_LEVELS.length - 1)) * 100)}%</span>
                    </div>
                    <div style={{ height: '6px', background: '#f3f4f6', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.round((engIdx / (ENGLISH_LEVELS.length - 1)) * 100)}%`, height: '100%', background: RED, borderRadius: '3px' }} />
                    </div>
                  </div>
                </div>

                {/* Math journey */}
                <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '16px' }}>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#111827', marginBottom: '14px' }}>🔢 Math Numeracy Journey</div>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '4px' }}>
                    {MATH_LEVELS.map((level, i) => {
                      const isPast      = i < mathIdx;
                      const isCurrent   = i === mathIdx;
                      const isPredicted = i === predMathIdx && predMathIdx > mathIdx;
                      return (
                        <div key={level} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '5px' }}>
                          <div style={{ width: '34px', height: '34px', borderRadius: '50%', background: isCurrent ? '#d97706' : isPast ? '#fef3c7' : isPredicted ? '#dcfce7' : '#f3f4f6', border: isCurrent ? '2px solid #d97706' : isPredicted ? '2px dashed #16a34a' : '2px solid transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', color: isCurrent ? 'white' : isPast ? '#d97706' : isPredicted ? '#16a34a' : '#9ca3af', fontWeight: isCurrent ? '700' : '400' }}>
                            {isCurrent ? '📍' : isPast ? '✓' : isPredicted ? '🎯' : i + 1}
                          </div>
                          <span style={{ fontSize: '9px', color: isCurrent ? '#d97706' : isPredicted ? '#16a34a' : '#9ca3af', fontWeight: isCurrent || isPredicted ? '600' : '400', textAlign: 'center' }}>{LEVEL_LABELS[level]}</span>
                          {isCurrent   && <span style={{ fontSize: '8px', color: '#d97706', fontWeight: '600' }}>NOW</span>}
                          {isPredicted && <span style={{ fontSize: '8px', color: '#16a34a', fontWeight: '600' }}>4WK</span>}
                        </div>
                      );
                    })}
                  </div>
                  <div style={{ marginTop: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontSize: '11px', color: '#9ca3af' }}>Progress through Math levels</span>
                      <span style={{ fontSize: '11px', fontWeight: '600', color: '#374151' }}>{Math.round((mathIdx / (MATH_LEVELS.length - 1)) * 100)}%</span>
                    </div>
                    <div style={{ height: '6px', background: '#f3f4f6', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.round((mathIdx / (MATH_LEVELS.length - 1)) * 100)}%`, height: '100%', background: '#d97706', borderRadius: '3px' }} />
                    </div>
                  </div>
                </div>

                {/* ML prediction card */}
                {pred && (
                  <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '14px' }}>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: '#111827', marginBottom: '10px' }}>🤖 ML Predictions — Next 4 Weeks</div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                      {[
                        { label: 'Predicted English Level', value: LEVEL_LABELS[pred.predicted_eng_level] || pred.predicted_eng_level || '—', color: RED },
                        { label: 'Predicted Math Level',    value: LEVEL_LABELS[pred.predicted_math_level] || pred.predicted_math_level || '—', color: '#d97706' },
                      ].map(item => (
                        <div key={item.label} style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '10px' }}>
                          <div style={{ fontSize: '10px', color: '#9ca3af', marginBottom: '4px' }}>{item.label}</div>
                          <div style={{ fontSize: '15px', fontWeight: '700', color: item.color }}>{item.value}</div>
                        </div>
                      ))}
                    </div>
                    {pred.risk_reason && (
                      <div style={{ marginTop: '8px', padding: '7px 10px', background: '#fff5f5', borderRadius: '6px', fontSize: '11px', color: '#9ca3af' }}>
                        ⚠️ {pred.risk_reason}
                      </div>
                    )}
                  </div>
                )}

              </div>
            );
          })}
        </div>
      )}
      {view === 'analysis' && (
        <div style={{ padding: '32px 40px' }}>
          <div style={{ marginBottom: '24px' }}>
            <h1 style={{ fontSize: '22px', fontWeight: '700', color: '#111827', marginBottom: '4px' }}>Student Analysis</h1>
            <p style={{ fontSize: '13px', color: '#9ca3af' }}>ML-driven performance history and risk alerts for your assigned kids</p>
          </div>

          {kids.map(kid => {
            // --- STRICT SANDBOX: All calculations scoped PER KID ---
            const kidId = kid.id;
            const kidPred = Array.isArray(predictions) ? predictions.find(p => p.kid_id === kidId) : null;
            const kidHistory = histories[kidId] || [];
            const kidLiveRating = ratings[kidId];
            const kidLastLog = [...kidHistory].sort((a,b)=>new Date(a.logged_at)-new Date(b.logged_at)).slice(-1)[0] || null;
            
            // Priority: Current Live Choice > Last Saved Entry
            const currentStatus = kidLiveRating || kidLastLog?.rating;
            
            // Build sandbox chart data
            const kidChart = [...kidHistory];
            if (kidLiveRating) {
              kidChart.push({
                logged_at: 'LIVE',
                rating: kidLiveRating,
                rating_num: kidLiveRating === 'struggling' ? 1 : kidLiveRating === 'okay' ? 2 : 3
              });
            }

            // Determine isolated risk: ONLY trigger if the LATEST saved log is 'struggling'
            // This ensures risk is removed as soon as a successful session is submitted.
            const lastSavedRating = (kidLastLog?.rating || '').toString().toLowerCase();
            const kidIsAtRisk = (lastSavedRating === 'struggling') || (kidPred?.risk_level === 'high' && lastSavedRating !== 'nailed_it');

            return (
              <div key={kid.id} style={{ 
                background: 'white', 
                border: `1px solid ${kidHistory.slice(-1)[0]?.rating_num === 1 ? '#dc2626' : '#e5e7eb'}`, 
                borderRadius: '12px', 
                padding: '16px 20px', 
                marginBottom: '14px', 
                boxShadow: kidHistory.slice(-1)[0]?.rating_num === 1 ? '0 0 0 3px #fee2e2' : 'none' 
              }}>
                
                {/* Kid header with Risk Status */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
                  <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: `hsl(${kidId * 47 % 360},55%,88%)`, color: `hsl(${kidId * 47 % 360},55%,30%)`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px', fontWeight: '700' }}>
                    {kid.name?.[0]}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{ fontSize: '20px', fontWeight: '700', color: '#111827' }}>{kid.name}</span>
                      {kidIsAtRisk && (
                        <span style={{ background: '#dc2626', color: 'white', padding: '2px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: '800', letterSpacing: '0.05em' }}>
                          ⚠️ UNDERPERFORMING
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: '13px', color: '#9ca3af' }}>Age {kid.age} · {kid.learning_style} learner</div>
                  </div>
                  {kidPred && (
                    <div style={{ padding: '8px 16px', borderRadius: '20px', fontSize: '13px', fontWeight: '600', background: kidIsAtRisk ? '#fff5f5' : kidPred.risk_level === 'medium' ? '#fffbeb' : '#f0fdf4', color: kidIsAtRisk ? '#dc2626' : kidPred.risk_level === 'medium' ? '#d97706' : '#16a34a', border: '1px solid currentColor' }}>
                      {kidIsAtRisk ? 'NEEDS ATTENTION' : (kidPred.risk_level?.toUpperCase() + ' RISK')}
                    </div>
                  )}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1.2fr', gap: '32px' }}>
                  
                  {/* Progress Line Graph */}
                  <div>
                    <div style={{ fontSize: '14px', fontWeight: '600', color: '#111827', marginBottom: '16px' }}>🏆 Learning Progress (Last 10 Sessions)</div>
                    <div style={{ height: '220px', width: '100%', background: '#f9fafb', borderRadius: '12px', padding: '16px' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={kidChart}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                          <XAxis dataKey="logged_at" fontSize={10} tickMargin={10} axisLine={false} tickLine={false} />
                          <YAxis domain={[0, 4]} ticks={[1, 2, 3]} axisLine={false} tickLine={false} fontSize={10} tickFormatter={(val) => val === 1 ? '😟' : val === 2 ? '🙂' : val === 3 ? '⭐' : ''} />
                          <Tooltip 
                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                            formatter={(value) => [value === 1 ? 'Struggling' : value === 2 ? 'Okay' : 'Nailed it', 'Performance']}
                          />
                          <Line type="monotone" dataKey="rating_num" stroke={kidIsAtRisk ? '#dc2626' : '#10b981'} strokeWidth={3} dot={{ r: 4, fill: kidIsAtRisk ? '#dc2626' : '#10b981', strokeWidth: 2, stroke: 'white' }} activeDot={{ r: 6 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Enhanced Risk Message / Prediction */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    
                    {kidIsAtRisk ? (
                      <div style={{ flex: 1, background: '#fff5f5', border: '2px solid #fee2e2', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 8px rgba(220, 38, 38, 0.05)' }}>
                        <div style={{ fontSize: '16px', fontWeight: '900', color: '#dc2626', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span>⚠️</span> RISK ALERT
                        </div>
                        <p style={{ fontSize: '14px', color: '#dc2626', lineHeight: '1.6', fontWeight: '500' }}>
                          <b>{kid.name}</b> is currently struggling in their sessions.
                          <br/><br/>
                          <span style={{ fontSize: '13px', opacity: 0.9 }}>
                            <b>Recommended Strategy:</b> Use tactile learning tools and decrease session duration to 20 mins to rebuild confidence.
                          </span>
                        </p>
                      </div>
                    ) : (
                      <div style={{ flex: 1, background: '#f0fdf4', border: '1px solid #dcfce7', borderRadius: '12px', padding: '16px' }}>
                        <div style={{ fontSize: '13px', fontWeight: '700', color: '#16a34a', marginBottom: '8px' }}>✅ STABLE TREND</div>
                        <p style={{ fontSize: '12px', color: '#16a34a', lineHeight: '1.5' }}>Consistent performance observed over the last few sessions.</p>
                      </div>
                    )}

                    {kidPred && (
                      <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '16px' }}>
                        <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>AI Prediction (4 Weeks)</div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                          <div style={{ background: 'white', padding: '8px', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
                            <div style={{ fontSize: '10px', color: '#9ca3af' }}>English</div>
                            <div style={{ fontSize: '13px', fontWeight: '700', color: RED }}>{LEVEL_LABELS[kidPred.predicted_eng_level] || '...'}</div>
                          </div>
                          <div style={{ background: 'white', padding: '8px', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
                            <div style={{ fontSize: '10px', color: '#9ca3af' }}>Math</div>
                            <div style={{ fontSize: '13px', fontWeight: '700', color: '#d97706' }}>{LEVEL_LABELS[kidPred.predicted_math_level] || '...'}</div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                </div>

                {kid.unlock_note ? (
                  <div style={{ marginTop: '20px', padding: '12px 16px', background: '#fffbeb', border: '1px solid #fef3c7', borderRadius: '10px', fontSize: '13px', color: '#92400e' }}>
                    💡 <strong>Instructional Tip:</strong> {kid.unlock_note}
                  </div>
                ) : pred?.risk_reason ? (
                  <div style={{ marginTop: '20px', padding: '12px 16px', background: '#f3f4f6', border: '1px solid #e5e7eb', borderRadius: '10px', fontSize: '12px', color: '#6b7280' }}>
                    🤖 <strong>ML Insight:</strong> {pred.risk_reason}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      )}
      </main>
    </div>
  );
}

function KidCard({ kid, rating, onRate }) {
  const selected = RATINGS.find(r => r.value === rating);
  return (
    <div style={{ ...s.kidCard, ...(selected ? { borderColor: selected.color } : {}) }}>
      <div style={s.kidTop}>
        <div style={{ ...s.kidAv, background: `hsl(${(kid.id * 47) % 360}, 55%, 88%)`, color: `hsl(${(kid.id * 47) % 360}, 55%, 30%)` }}>
          {kid.name?.[0] || '?'}
        </div>
        <div style={s.kidInfo}>
          <div style={s.kidName}>{kid.name}</div>
          <div style={s.kidLevel}>EN: <Chip label={LEVEL_LABELS[kid.english_level] || kid.english_level} /> · Math: <Chip label={LEVEL_LABELS[kid.math_level] || kid.math_level} /></div>
          {kid.unlock_note && <div style={s.unlock}>💡 {kid.unlock_note}</div>}
        </div>
        {selected && <div style={{ ...s.ratedBadge, background: selected.bg, color: selected.color }}>{selected.emoji} {selected.label}</div>}
      </div>

      <div style={s.ratingRow}>
        {RATINGS.map(r => (
          <button
            key={r.value}
            style={{ ...s.ratingBtn, ...(rating === r.value ? { background: r.bg, borderColor: r.color } : {}) }}
            onClick={() => onRate(r.value)}
          >
            <span style={{ fontSize: '20px' }}>{r.emoji}</span>
            <span style={s.ratingLabel}>{r.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function SuccessScreen({ kids, ratings, onReset }) {
  const counts = {
    nailed_it:  Object.values(ratings).filter(r => r === 'nailed_it').length,
    okay:       Object.values(ratings).filter(r => r === 'okay').length,
    struggling: Object.values(ratings).filter(r => r === 'struggling').length,
  };
  return (
    <div style={s.successPage}>
      <div style={s.successCard}>
        <div style={s.successIcon}>✓</div>
        <h2 style={{ fontSize: '22px', fontWeight: '700', color: 'var(--gray-900)', marginBottom: '6px' }}>Session logged</h2>
        <p style={{ fontSize: '14px', color: 'var(--gray-400)', marginBottom: '24px' }}>You logged {kids.length} kids. Great work.</p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '24px', marginBottom: '28px' }}>
          {[['⭐', counts.nailed_it, 'var(--success)'], ['🙂', counts.okay, 'var(--warning)'], ['😕', counts.struggling, 'var(--primary-600)']].map(([e, n, c], i) => (
            <div key={i} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '22px' }}>{e}</div>
              <div style={{ fontSize: '24px', fontWeight: '700', color: c }}>{n}</div>
            </div>
          ))}
        </div>
        <button style={s.submitBtn} onClick={onReset}>Log another</button>
      </div>
    </div>
  );
}

function Chip({ label }) {
  return (
    <span style={{ display: 'inline-block', padding: '1px 6px', borderRadius: 'var(--radius-sm)', fontSize: '11px', fontWeight: '500', background: 'var(--primary-50)', color: 'var(--primary-700)', margin: '0 1px' }}>
      {label || '—'}
    </span>
  );
}

function Loader() {
  return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}><span style={{ color: 'var(--primary-600)', fontSize: '16px' }}>Loading your kids...</span></div>;
}

const s = {
  page: { minHeight: '100vh', background: '#f9fafb', paddingBottom: '90px' },
  header: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 32px', background: 'white', borderBottom: '1px solid #e5e7eb' },
  headerLeft:  { display: 'flex', alignItems: 'center', gap: '10px' },
  headerLogo:  { width: '30px', height: '30px', borderRadius: 'var(--radius-md)', background: 'var(--primary-600)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: '700', color: 'white' },
  headerTitle: { fontSize: '14px', fontWeight: '600', color: 'var(--gray-900)' },
  headerSub:   { fontSize: '11px', color: 'var(--gray-400)' },
  viewBtn:   { padding: '5px 10px', borderRadius: '6px', background: 'transparent', border: '1px solid #e5e7eb', color: '#6b7280', fontSize: '12px' },
  logoutBtn:   { padding: '5px 10px', borderRadius: 'var(--radius-md)', background: 'transparent', border: '1px solid var(--gray-200)', color: 'var(--gray-400)', fontSize: '12px' },
  progressBar: { height: '2px', background: 'var(--gray-100)' },
  progressFill:{ height: '100%', background: 'var(--primary-600)', transition: 'width 0.4s ease' },
  intro:       { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px' },
  introText:   { fontSize: '13px', color: 'var(--gray-700)' },
  progressText:{ fontSize: '12px', fontWeight: '600', color: 'var(--primary-600)' },
  kidList: { display: 'flex', flexDirection: 'column', gap: '10px', padding: '0 40px' },
  kidCard:     { background: 'var(--white)', border: '1.5px solid var(--gray-200)', borderRadius: 'var(--radius-lg)', padding: '14px', transition: 'border-color 0.2s' },
  kidTop:      { display: 'flex', alignItems: 'flex-start', gap: '10px', marginBottom: '12px' },
  kidAv:       { width: '36px', height: '36px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', fontWeight: '700', flexShrink: 0 },
  kidInfo:     { flex: 1 },
  kidName:     { fontSize: '15px', fontWeight: '600', color: 'var(--gray-900)', marginBottom: '2px' },
  kidLevel:    { fontSize: '11px', color: 'var(--gray-400)', marginBottom: '3px' },
  unlock:      { fontSize: '11px', color: 'var(--primary-600)', background: 'var(--primary-50)', borderRadius: 'var(--radius-sm)', padding: '2px 6px', display: 'inline-block' },
  ratedBadge:  { padding: '3px 8px', borderRadius: 'var(--radius-full)', fontSize: '11px', fontWeight: '600', flexShrink: 0 },
  ratingRow:   { display: 'flex', gap: '6px' },
  ratingBtn:   { flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px', padding: '9px 6px', border: '1.5px solid var(--gray-200)', borderRadius: 'var(--radius-md)', background: 'var(--gray-50)', transition: 'all 0.15s' },
  ratingLabel: { fontSize: '10px', fontWeight: '500', color: 'var(--gray-400)' },
  footer:      { position: 'fixed', bottom: 0, left: '50%', transform: 'translateX(-50%)', width: '100%', maxWidth: '860px', padding: '12px 16px', background: 'var(--white)', borderTop: '1px solid var(--gray-200)' },
  footerHint:  { fontSize: '12px', color: 'var(--gray-400)', textAlign: 'center', marginBottom: '6px' },
  submitBtn:   { width: '100%', padding: '12px', background: 'var(--primary-600)', color: 'white', borderRadius: 'var(--radius-md)', fontSize: '14px', fontWeight: '600', transition: 'opacity 0.15s' },
  successPage: { display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', padding: '24px', background: 'var(--gray-50)' },
  successCard: { background: 'var(--white)', borderRadius: 'var(--radius-xl)', padding: '36px 28px', textAlign: 'center', maxWidth: '320px', width: '100%', border: '1px solid var(--gray-200)' },
  successIcon: { width: '56px', height: '56px', borderRadius: '50%', background: 'var(--primary-600)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px', fontWeight: '700', margin: '0 auto 16px' },
};
