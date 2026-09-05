import { useState, useEffect, useCallback } from 'react';
import { fetchAutomationHealth, fetchAdoption, fetchAutomationLogs, triggerAutomation } from '../api/client';

// ── Automation tab ────────────────────────────────────────────────────────────
// Answers three questions a coordinator (or an ops reviewer) actually asks:
//   1. Did the scheduled jobs run, and did they succeed?        → Health
//   2. Is anyone using what they produce, and did it help?      → Adoption
//   3. What exactly went out, to whom?                          → Audit log

const RED   = '#dc2626';
const AMBER = '#d97706';
const GREEN = '#16a34a';
const GRAY  = '#6b7280';

const JOB_LABEL = {
  rsvp_reminders:    'RSVP reminders',
  unconfirmed_alert: 'Unconfirmed volunteer alert',
  ml_pipeline:       'ML pipeline',
  at_risk_digest:    'At-risk digest',
};
const JOB_TRIGGER = {
  rsvp_reminders:    'rsvp-reminders',
  unconfirmed_alert: 'unconfirmed-check',
  ml_pipeline:       'ml-pipeline',
  at_risk_digest:    'at-risk-digest',
};

const statusColor = (st) => (st === 'success' ? GREEN : st === 'failed' ? RED : st === 'running' ? AMBER : GRAY);
const pct = (v) => (v === null || v === undefined ? '—' : `${Math.round(v * 100)}%`);
const ago = (iso) => {
  if (!iso) return 'never';
  const mins = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 48) return `${hrs} h ago`;
  return `${Math.round(hrs / 24)} d ago`;
};

export default function AutomationTab() {
  const [health, setHealth]     = useState(null);
  const [adoption, setAdoption] = useState(null);
  const [logs, setLogs]         = useState([]);
  const [busy, setBusy]         = useState(null);
  const [err, setErr]           = useState(null);

  const load = useCallback(() => {
    setErr(null);
    Promise.all([fetchAutomationHealth(), fetchAdoption(), fetchAutomationLogs(15)])
      .then(([h, a, l]) => { setHealth(h); setAdoption(a); setLogs(Array.isArray(l) ? l : []); })
      .catch((e) => setErr(e.message || 'Could not load automation data'));
  }, []);

  useEffect(() => { load(); }, [load]);

  const runNow = async (jobId) => {
    setBusy(jobId);
    try {
      await triggerAutomation(JOB_TRIGGER[jobId]);
      setTimeout(load, 2500); // give the background task a moment to write its run row
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(null);
    }
  };

  const overall = health?.overall || 'loading';
  const overallColor = overall === 'healthy' ? GREEN : overall === 'degraded' ? RED : GRAY;

  return (
    <div style={t.content}>
      <div style={t.pageHead}>
        <h1 style={t.pageTitle}>Automation</h1>
        <p style={t.pageSub}>
          Four scheduled jobs replace the manual WhatsApp-and-spreadsheet routine. This page shows whether they ran, whether people used the result, and exactly what went out.
        </p>
      </div>

      {err && <div style={t.errBox}>{err}</div>}

      {/* ── Health ─────────────────────────────────────────────────────── */}
      <div style={t.card}>
        <div style={t.cardHead}>
          <div>
            <div style={t.cardTitle}>Job health</div>
            <span style={t.cardSub}>Last 30 days · runs recorded by the backend, whether fired by the in-app scheduler, GitHub Actions cron, or manually</span>
          </div>
          <span style={{ ...t.pill, background: overallColor + '1a', color: overallColor }}>{overall}</span>
        </div>

        {!health ? <div style={t.muted}>Loading…</div> : (
          <table style={t.table}>
            <thead>
              <tr>
                {['Job', 'Schedule', 'Last run', 'Result', '30-day success', ''].map(h => <th key={h} style={t.th}>{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {health.jobs.map(j => (
                <tr key={j.job_id}>
                  <td style={t.td}>
                    <div style={t.jobName}>{JOB_LABEL[j.job_id] || j.job_id}</div>
                    <div style={t.jobReplaces}>replaces: {j.replaces}</div>
                  </td>
                  <td style={t.td}>{j.when}</td>
                  <td style={t.td}>
                    <div>{ago(j.last_run_at)}</div>
                    {j.triggered_by && <div style={t.tiny}>via {j.triggered_by}</div>}
                  </td>
                  <td style={t.td}>
                    <span style={{ ...t.dot, background: statusColor(j.last_status) }} />
                    {j.last_status.replace('_', ' ')}
                    {j.last_summary && <div style={t.tiny}>{j.last_summary}</div>}
                    {j.last_error && <div style={{ ...t.tiny, color: RED }}>{j.last_error}</div>}
                  </td>
                  <td style={t.td}>{pct(j.success_rate_30d)} <span style={t.tiny}>({j.runs_30d} runs)</span></td>
                  <td style={t.td}>
                    <button style={t.runBtn} disabled={busy === j.job_id} onClick={() => runNow(j.job_id)}>
                      {busy === j.job_id ? 'Starting…' : 'Run now'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* ── Adoption ───────────────────────────────────────────────────── */}
      <div style={t.card}>
        <div style={t.cardHead}>
          <div>
            <div style={t.cardTitle}>Adoption &amp; impact</div>
            <span style={t.cardSub}>
              Past {adoption?.window_weeks ?? 8} weeks · {adoption?.sessions_in_window ?? '—'} sessions · baselines from pre-ImpactBridge operations at U&amp;I Vizag
            </span>
          </div>
        </div>

        {!adoption ? <div style={t.muted}>Loading…</div> : (
          <div style={t.kpiGrid}>
            <Kpi
              label="Session sheet completion"
              value={pct(adoption.log_completion_rate)}
              sub={adoption.log_completion_delta_pts === null ? 'no sessions yet'
                : `${adoption.log_completion_delta_pts >= 0 ? '+' : ''}${adoption.log_completion_delta_pts} pts vs ${Math.round(adoption.log_completion_baseline * 100)}% baseline`}
              color={adoption.log_completion_rate === null ? GRAY : adoption.log_completion_rate >= adoption.log_completion_baseline ? GREEN : AMBER}
            />
            <Kpi
              label="RSVP response rate"
              value={pct(adoption.rsvp_response_rate)}
              sub={`${adoption.rsvps_responded} of ${adoption.rsvps_total} answered the one-tap email`}
              color={adoption.rsvp_response_rate === null ? GRAY : adoption.rsvp_response_rate >= 0.7 ? GREEN : AMBER}
            />
            <Kpi
              label="Volunteer time saved"
              value={`${Math.round(adoption.volunteer_minutes_saved_est / 60)} h`}
              sub={`${adoption.actual_logs} volunteer sessions logged × (15 min → 30 s), estimate`}
              color={GREEN}
            />
            <Kpi
              label="Coordinator messages avoided"
              value={adoption.coordinator_manual_msgs_avoided_est}
              sub="≈5 manual WhatsApp confirmations per week, estimate"
              color={GREEN}
            />
            <Kpi
              label="Automated emails sent"
              value={adoption.automated_emails_sent}
              sub="from the audit log, this window"
              color={GRAY}
            />
            <Kpi
              label="Confirmed attendance"
              value={pct(adoption.rsvp_confirmed_rate)}
              sub={`${adoption.rsvps_confirmed} confirmed ahead of Sunday`}
              color={GRAY}
            />
          </div>
        )}
      </div>

      {/* ── Audit log ──────────────────────────────────────────────────── */}
      <div style={t.card}>
        <div style={t.cardHead}>
          <div>
            <div style={t.cardTitle}>Recent automated emails</div>
            <span style={t.cardSub}>Every email the system sends is logged. "sent_dev" means it was printed to the console because no SendGrid key is configured.</span>
          </div>
          <button style={t.refresh} onClick={load}>Refresh</button>
        </div>
        {logs.length === 0 ? <div style={t.muted}>No emails logged yet. Run a job above to see entries appear here.</div> : (
          <table style={t.table}>
            <thead><tr>{['When', 'Type', 'To', 'Subject', 'Status'].map(h => <th key={h} style={t.th}>{h}</th>)}</tr></thead>
            <tbody>
              {logs.map(l => (
                <tr key={l.id}>
                  <td style={t.td}>{ago(l.created_at)}</td>
                  <td style={t.td}>{l.type.replace(/_/g, ' ')}</td>
                  <td style={t.td}>{l.recipient}</td>
                  <td style={{ ...t.td, maxWidth: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{l.subject}</td>
                  <td style={t.td}>
                    <span style={{ ...t.dot, background: l.status.startsWith('sent') ? GREEN : RED }} />{l.status}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function Kpi({ label, value, sub, color }) {
  return (
    <div style={t.kpi}>
      <div style={t.kpiLabel}>{label}</div>
      <div style={{ ...t.kpiValue, color }}>{value}</div>
      <div style={t.kpiSub}>{sub}</div>
    </div>
  );
}

const t = {
  content:   { padding: '32px 40px', maxWidth: '1040px' },
  pageHead:  { marginBottom: '24px' },
  pageTitle: { fontSize: '22px', fontWeight: '700', color: '#111827', marginBottom: '4px' },
  pageSub:   { fontSize: '13px', color: '#6b7280', maxWidth: 720 },
  card:      { background: 'white', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '18px', marginBottom: '14px' },
  cardHead:  { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, marginBottom: '12px' },
  cardTitle: { fontSize: '14px', fontWeight: '600', color: '#111827', marginBottom: '2px' },
  cardSub:   { fontSize: '11px', color: '#9ca3af', display: 'block' },
  pill:      { padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '600', textTransform: 'capitalize', flexShrink: 0 },
  table:     { width: '100%', borderCollapse: 'collapse', fontSize: '12px' },
  th:        { textAlign: 'left', padding: '8px 6px', borderBottom: '1px solid #e5e7eb', color: '#9ca3af', fontWeight: '500', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em' },
  td:        { padding: '10px 6px', borderBottom: '1px solid #f3f4f6', color: '#374151', verticalAlign: 'top' },
  jobName:   { fontWeight: '600', color: '#111827' },
  jobReplaces: { fontSize: '11px', color: '#9ca3af', marginTop: 2 },
  tiny:      { fontSize: '11px', color: '#9ca3af', marginTop: 2 },
  dot:       { display: 'inline-block', width: 8, height: 8, borderRadius: '50%', marginRight: 6 },
  runBtn:    { padding: '5px 10px', fontSize: '11px', borderRadius: '6px', border: '1px solid #e5e7eb', background: 'white', color: '#374151', cursor: 'pointer' },
  refresh:   { padding: '5px 10px', fontSize: '11px', borderRadius: '6px', border: '1px solid #e5e7eb', background: 'white', color: '#374151', cursor: 'pointer' },
  kpiGrid:   { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' },
  kpi:       { border: '1px solid #f3f4f6', borderRadius: '10px', padding: '12px 14px', background: '#fafafa' },
  kpiLabel:  { fontSize: '11px', color: '#6b7280', marginBottom: 4 },
  kpiValue:  { fontSize: '22px', fontWeight: '700', lineHeight: 1.1 },
  kpiSub:    { fontSize: '11px', color: '#9ca3af', marginTop: 4 },
  muted:     { fontSize: '12px', color: '#9ca3af', padding: '8px 0' },
  errBox:    { background: '#fef2f2', color: RED, border: '1px solid #fecaca', borderRadius: 8, padding: '10px 12px', fontSize: 12, marginBottom: 14 },
};
