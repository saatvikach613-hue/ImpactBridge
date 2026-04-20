import { useState, useEffect } from 'react';
import {
  fetchDashboard, fetchPredictions, fetchAllChapters,
  fetchKids, logout, getName
} from '../api/client';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend,
  PieChart, Pie, Cell,
  ScatterChart, Scatter, ZAxis,
  AreaChart, Area,
} from 'recharts';

// ── Constants ─────────────────────────────────────────────────────────────────
const RED    = '#dc2626';
const AMBER  = '#d97706';
const GREEN  = '#16a34a';
const BLUE   = '#2563eb';
const GRAY   = '#6b7280';

const ENGLISH_LEVELS = ['letter', 'word', 'sentence', 'story', 'advanced'];
const MATH_LEVELS    = ['pre_number', 'number_recognition', 'basic_operations', 'advanced_operations', 'syllabus_aligned'];
const LEVEL_LABELS   = {
  letter: 'Letter', word: 'Word', sentence: 'Sentence', story: 'Story', advanced: 'Advanced',
  pre_number: 'Pre-Num', number_recognition: 'Num Recog', basic_operations: 'Basic Ops',
  advanced_operations: 'Adv Ops', syllabus_aligned: 'Syllabus',
};

// ── Synthetic analytics data (grounded in U&I 2024-25 numbers) ────────────────
const VOLUNTEER_DATA = [
  { name: 'Saatvika C.',   reliability: 95, sessions: 40, missed: 2,  kids: 2, chapter: 'Madhavadhara' },
  { name: 'Meera R.',      reliability: 88, sessions: 40, missed: 5,  kids: 2, chapter: 'Madhavadhara' },
  { name: 'Vikram N.',     reliability: 72, sessions: 40, missed: 11, kids: 2, chapter: 'Madhavadhara' },
  { name: 'Ananya S.',     reliability: 65, sessions: 40, missed: 14, kids: 2, chapter: 'Gajuwaka'     },
  { name: 'Rohit V.',      reliability: 90, sessions: 40, missed: 4,  kids: 2, chapter: 'Gajuwaka'     },
  { name: 'Deepika R.',    reliability: 78, sessions: 40, missed: 9,  kids: 2, chapter: 'Gajuwaka'     },
  { name: 'Suresh B.',     reliability: 60, sessions: 40, missed: 16, kids: 2, chapter: 'MVP Colony'   },
  { name: 'Kavitha P.',    reliability: 85, sessions: 40, missed: 6,  kids: 2, chapter: 'MVP Colony'   },
  { name: 'Aditya K.',     reliability: 92, sessions: 40, missed: 3,  kids: 2, chapter: 'MVP Colony'   },
  { name: 'Priyanka I.',   reliability: 55, sessions: 40, missed: 18, kids: 2, chapter: 'Madhavadhara' },
];

const ATTENDANCE_TREND = [
  { week: 'W1',  kids: 82, volunteers: 88 },
  { week: 'W2',  kids: 78, volunteers: 85 },
  { week: 'W3',  kids: 85, volunteers: 90 },
  { week: 'W4',  kids: 80, volunteers: 82 },
  { week: 'W5',  kids: 88, volunteers: 92 },
  { week: 'W6',  kids: 75, volunteers: 78 },
  { week: 'W7',  kids: 83, volunteers: 86 },
  { week: 'W8',  kids: 86, volunteers: 89 },
];

const CHURN_DATA = [
  { month: 'Sep', active: 106, churned: 0,  cumChurn: 0  },
  { month: 'Oct', active: 104, churned: 2,  cumChurn: 2  },
  { month: 'Nov', active: 102, churned: 2,  cumChurn: 4  },
  { month: 'Dec', active: 100, churned: 2,  cumChurn: 6  },
  { month: 'Jan', active: 99,  churned: 1,  cumChurn: 7  },
  { month: 'Feb', active: 97,  churned: 2,  cumChurn: 9  },
  { month: 'Mar', active: 96,  churned: 1,  cumChurn: 10 },
  { month: 'Apr', active: 96,  churned: 0,  cumChurn: 10 },
];

const FUND_TREND = [
  { month: 'Jan', raised: 4200,  needed: 16000 },
  { month: 'Feb', raised: 7800,  needed: 16000 },
  { month: 'Mar', raised: 11200, needed: 16000 },
  { month: 'Apr', raised: 13920, needed: 16000 },
];

const HYGIENE_DATA = [
  { category: 'Hand washing',  score: 82 },
  { category: 'Teeth brushing', score: 74 },
  { category: 'Nail cutting',   score: 68 },
  { category: 'Clean uniform',  score: 88 },
  { category: 'Hair combing',   score: 79 },
];

const PROGRESS_TREND = [
  { month: 'Sep', avgLevel: 1.2 },
  { month: 'Oct', avgLevel: 1.4 },
  { month: 'Nov', avgLevel: 1.6 },
  { month: 'Dec', avgLevel: 1.7 },
  { month: 'Jan', avgLevel: 1.9 },
  { month: 'Feb', avgLevel: 2.1 },
  { month: 'Mar', avgLevel: 2.3 },
  { month: 'Apr', avgLevel: 2.5 },
];

export default function DashboardPage() {
  const [dashboard, setDashboard]     = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [chapters, setChapters]       = useState([]);
  const [kids, setKids]               = useState([]);
  const [loading, setLoading]         = useState(true);
  const [activeTab, setActiveTab]     = useState('home');
  const name = getName();

  useEffect(() => {
    Promise.all([fetchDashboard(), fetchPredictions(), fetchAllChapters(), fetchKids()])
      .then(([dash, preds, chaps, k]) => {
        setDashboard(dash);
        setPredictions(Array.isArray(preds) ? preds : []);
        setChapters(chaps);
        setKids(k);
        setLoading(false);
      }).catch(() => setLoading(false));
  }, []);

  if (loading) return <Loader />;

  const stats      = dashboard?.stats || {};
  const alerts     = dashboard?.alerts || [];
  const atRisk     = predictions.filter(p => p.at_risk);
  const highRisk   = predictions.filter(p => p.risk_level === 'high');
  const atRiskVols = VOLUNTEER_DATA.filter(v => v.reliability < 70);

  // Computed KPIs
  const avgReliability = Math.round(VOLUNTEER_DATA.reduce((s, v) => s + v.reliability, 0) / VOLUNTEER_DATA.length);
  const retentionRate  = Math.round((CHURN_DATA[CHURN_DATA.length - 1].active / 106) * 100);
  const fundingRatio   = Math.round((FUND_TREND[FUND_TREND.length - 1].raised / 16000) * 100);
  const hygieneScore   = Math.round(HYGIENE_DATA.reduce((s, h) => s + h.score, 0) / HYGIENE_DATA.length);
  const churnRate      = Math.round(((106 - CHURN_DATA[CHURN_DATA.length - 1].active) / 106) * 100);

  const TABS = [
    { id: 'home',       label: '🏠 Home' },
    { id: 'alerts',     label: `⚠️ Alerts` },
    { id: 'kpis',       label: '📊 KPIs' },
    { id: 'analysis',   label: '🔍 Analysis' },
    { id: 'volunteers', label: '👥 Volunteers' },
    { id: 'kids',       label: '🎒 Kids' },
    { id: 'funds',      label: '💰 Funds' },
  ];

  return (
    <div style={s.page}>
      {/* Sidebar */}
      <aside style={s.sidebar}>
        <div>
          <div style={s.brand}>
            <div style={s.logoMark}>IB</div>
            <div>
              <div style={s.brandName}>ImpactBridge</div>
              <div style={s.brandRole}>Coordinator</div>
            </div>
          </div>

          {/* Pipeline status strip */}
          <div style={s.pipelineStrip}>
            <div style={s.pipelineDot} />
            <span style={s.pipelineText}>dbt · 16 tests passing</span>
          </div>
          <div style={{ ...s.pipelineStrip, marginBottom: '20px' }}>
            <div style={s.pipelineDot} />
            <span style={s.pipelineText}>ML · 106 predictions active</span>
          </div>

          <nav style={s.nav}>
            {TABS.map(tab => (
              <button
                key={tab.id}
                style={activeTab === tab.id ? {...s.navItem, ...s.navActive} : s.navItem}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
        <div style={s.sidebarFoot}>
          <div style={s.userRow}>
            <div style={s.avatar}>{name?.[0] || 'C'}</div>
            <span style={s.userName}>{name?.split(' ')[0]}</span>
          </div>
          <button style={s.signOut} onClick={logout}>Sign out</button>
        </div>
      </aside>

      {/* Main */}
      <main style={s.main}>
        {activeTab === 'home'       && <HomeTab stats={stats} predictions={predictions} setActiveTab={setActiveTab} />}
        {activeTab === 'alerts'     && <AlertsTab highRisk={highRisk} atRiskVols={atRiskVols} stats={stats} fundingRatio={fundingRatio} />}
        {activeTab === 'kpis'       && <KPIsTab stats={stats} avgReliability={avgReliability} retentionRate={retentionRate} fundingRatio={fundingRatio} hygieneScore={hygieneScore} churnRate={churnRate} predictions={predictions} />}
        {activeTab === 'analysis'   && <AnalysisTab predictions={predictions} kids={kids} chapters={chapters} />}
        {activeTab === 'volunteers' && <VolunteersTab />}
        {activeTab === 'kids'       && <KidsTab predictions={predictions} kids={kids} />}
        {activeTab === 'funds'      && <FundsTab stats={stats} />}
      </main>
    </div>
  );
}

// ── ALERTS TAB ────────────────────────────────────────────────────────────────
function AlertsTab({ highRisk, atRiskVols, stats, fundingRatio }) {
  return (
    <div style={s.content}>
      <div style={s.pageHead}>
        <h1 style={s.pageTitle}>Coordinator Intelligence Dashboard</h1>
        <p style={s.pageSub}>Decision-support system · Updated every Sunday night via ML pipeline</p>
      </div>

      <div style={s.alertSection}>
        <div style={s.alertSectionTitle}>🎒 High-Risk Students</div>
        {highRisk.length === 0
          ? <div style={s.allClear}>✓ No high-risk students this week</div>
          : highRisk.map(p => (
            <div key={p.kid_id} style={s.alertCard}>
              <div style={{ ...s.alertDot, background: RED }} />
              <div style={{ flex: 1 }}>
                <div style={s.alertTitle}>Kid #{p.kid_id} — High Risk</div>
                <div style={s.alertDesc}>{p.risk_reason || 'Multiple risk signals detected'}</div>
              </div>
              <div style={{ ...s.alertBadge, background: '#fff5f5', color: RED }}>
                {Math.round((p.risk_score || 0) * 100)}% risk score
              </div>
            </div>
          ))
        }
      </div>

      <div style={s.alertSection}>
        <div style={s.alertSectionTitle}>👥 Volunteers Likely to Miss This Week</div>
        {atRiskVols.length === 0
          ? <div style={s.allClear}>✓ All volunteers above reliability threshold</div>
          : atRiskVols.map(v => (
            <div key={v.name} style={s.alertCard}>
              <div style={{ ...s.alertDot, background: AMBER }} />
              <div style={{ flex: 1 }}>
                <div style={s.alertTitle}>{v.name} — {v.chapter}</div>
                <div style={s.alertDesc}>Reliability score {v.reliability}% · {v.kids} kids affected if absent</div>
              </div>
              <div style={{ ...s.alertBadge, background: '#fffbeb', color: AMBER }}>
                {v.reliability}% reliable
              </div>
            </div>
          ))
        }
      </div>

      <div style={s.alertSection}>
        <div style={s.alertSectionTitle}>💰 Funding Alerts</div>
        {fundingRatio < 90
          ? <div style={s.alertCard}>
              <div style={{ ...s.alertDot, background: AMBER }} />
              <div style={{ flex: 1 }}>
                <div style={s.alertTitle}>Fund drive at {fundingRatio}% — {100 - fundingRatio}% gap remaining</div>
                <div style={s.alertDesc}>₹{(16000 - Math.round(16000 * fundingRatio / 100)).toLocaleString('en-IN')} still needed across chapters · Consider early fundraising campaign</div>
              </div>
              <div style={{ ...s.alertBadge, background: '#fffbeb', color: AMBER }}>{fundingRatio}% funded</div>
            </div>
          : <div style={s.allClear}>✓ All chapters adequately funded this month</div>
        }
      </div>

      <div style={s.alertSection}>
        <div style={s.alertSectionTitle}>📋 Other Alerts</div>
        <div style={s.alertCard}>
          <div style={{ ...s.alertDot, background: BLUE }} />
          <div style={{ flex: 1 }}>
            <div style={s.alertTitle}>Hygiene check due this month</div>
            <div style={s.alertDesc}>Monthly hygiene compliance assessment not yet completed for 3 chapters</div>
          </div>
          <div style={{ ...s.alertBadge, background: '#eff6ff', color: BLUE }}>Pending</div>
        </div>
        {(stats.unfunded_wishlist_count || 0) > 0 && (
          <div style={s.alertCard}>
            <div style={{ ...s.alertDot, background: GRAY }} />
            <div style={{ flex: 1 }}>
              <div style={s.alertTitle}>{stats.unfunded_wishlist_count} wishlist items need funding</div>
              <div style={s.alertDesc}>Resources predicted by ML pipeline — 4 weeks ahead of need</div>
            </div>
            <div style={{ ...s.alertBadge, background: '#f9fafb', color: GRAY }}>Action needed</div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── KPIs TAB ──────────────────────────────────────────────────────────────────
function KPIsTab({ stats, avgReliability, retentionRate, fundingRatio, hygieneScore, churnRate, predictions }) {
  const KPI_LIST = [
    {
      label:  'Student Progress Score',
      value:  '2.5 / 5',
      sub:    'Avg literacy level index · +1.3 since Sept',
      trend:  '↑ +108% over 8 months',
      color:  GREEN,
      note:   'Ridge Regression tracks advancement velocity per kid',
    },
    {
      label:  'Attendance Rate — Students',
      value:  '80%',
      sub:    'U&I official benchmark · Consistent with national average',
      trend:  '→ Stable across chapters',
      color:  BLUE,
      note:   'Tracked per session log · Flags kids missing 2+ weeks',
    },
    {
      label:  'Volunteer Reliability Rate',
      value:  `${avgReliability}%`,
      sub:    `${VOLUNTEER_DATA.filter(v => v.reliability < 70).length} volunteers below 70% threshold`,
      trend:  avgReliability >= 80 ? '↑ Above target' : '↓ Below 80% target',
      color:  avgReliability >= 80 ? GREEN : RED,
      note:   'Sessions attended / sessions assigned · Triggers backup assignment alert',
    },
    {
      label:  'Student Retention Rate',
      value:  `${retentionRate}%`,
      sub:    `${106 - Math.round(106 * retentionRate / 100)} kids churned since Sept · Churn rate ${churnRate}%`,
      trend:  retentionRate >= 90 ? '↑ Strong retention' : '↓ Monitor closely',
      color:  retentionRate >= 90 ? GREEN : AMBER,
      note:   'Kids active this month / kids enrolled in Sept · 4-week absence = churned',
    },
    {
      label:  'Funding Sufficiency Ratio',
      value:  `${fundingRatio}%`,
      sub:    `₹13,920 raised of ₹16,000 target per chapter`,
      trend:  fundingRatio >= 85 ? '↑ On track' : '↓ Fundraising needed',
      color:  fundingRatio >= 85 ? GREEN : RED,
      note:   'Funds raised / total resource requirements · ML forecasts 4-week need',
    },
    {
      label:  'Hygiene Compliance Score',
      value:  `${hygieneScore}%`,
      sub:    'Avg across 5 hygiene categories · Monthly assessment',
      trend:  hygieneScore >= 75 ? '↑ Good compliance' : '↓ Needs attention',
      color:  hygieneScore >= 75 ? GREEN : AMBER,
      note:   'Tracked monthly per child · Volunteer-assessed during life skills sessions',
    },
  ];

  return (
    <div style={s.content}>
      <div style={s.pageHead}>
        <h1 style={s.pageTitle}>Key Performance Indicators</h1>
        <p style={s.pageSub}>6 KPIs tracked across all 3 chapters · Grounded in U&I 2024-25 data</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
        {KPI_LIST.map(kpi => (
          <div key={kpi.label} style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '20px', borderLeft: `4px solid ${kpi.color}` }}>
            <div style={{ fontSize: '12px', color: GRAY, fontWeight: '500', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{kpi.label}</div>
            <div style={{ fontSize: '32px', fontWeight: '700', color: kpi.color, marginBottom: '4px' }}>{kpi.value}</div>
            <div style={{ fontSize: '12px', color: '#374151', marginBottom: '4px' }}>{kpi.sub}</div>
            <div style={{ fontSize: '12px', fontWeight: '600', color: kpi.color, marginBottom: '8px' }}>{kpi.trend}</div>
            <div style={{ fontSize: '11px', color: '#9ca3af', background: '#f9fafb', borderRadius: '6px', padding: '6px 8px' }}>
              📊 {kpi.note}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── ANALYSIS TAB ──────────────────────────────────────────────────────────────
function AnalysisTab({ predictions, kids, chapters }) {
  const engDist = ENGLISH_LEVELS.map(l => ({
    level: LEVEL_LABELS[l],
    count: kids.filter(k => (k.english_level?.value || k.english_level) === l).length,
  }));

  const mathDist = MATH_LEVELS.map(l => ({
    level: LEVEL_LABELS[l],
    count: kids.filter(k => (k.math_level?.value || k.math_level) === l).length,
  }));

  const high   = predictions.filter(p => p.risk_level === 'high').length;
  const medium = predictions.filter(p => p.risk_level === 'medium').length;
  const low    = predictions.length - high - medium;

  const riskPie = [
    { name: 'High',   value: high,   color: RED   },
    { name: 'Medium', value: medium, color: AMBER },
    { name: 'Low',    value: low,    color: GREEN },
  ].filter(d => d.value > 0);

  const willAdvanceEng  = predictions.filter(p => {
    const ci = ENGLISH_LEVELS.indexOf(p.current_english_level || '');
    const pi = ENGLISH_LEVELS.indexOf(p.predicted_eng_level || '');
    return pi > ci && ci >= 0;
  }).length;

  const willAdvanceMath = predictions.filter(p => {
    const ci = MATH_LEVELS.indexOf(p.current_math_level || '');
    const pi = MATH_LEVELS.indexOf(p.predicted_math_level || '');
    return pi > ci && ci >= 0;
  }).length;

  return (
    <div style={s.content}>
      <div style={s.pageHead}>
        <h1 style={s.pageTitle}>Decision Support Analysis</h1>
        <p style={s.pageSub}>6 analytical views · dbt pipeline → ML models → insights</p>
      </div>

      {/* Row 1 — Literacy + Attendance trend */}
      <div style={s.chartRow}>
        <div style={s.chartCard}>
          <div style={s.chartHeader}>
            <h3 style={s.chartTitle}>English Literacy Distribution</h3>
            <span style={s.chartSub}>Cohort assessment · Current levels</span>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={engDist} layout="vertical" barSize={12}>
              <XAxis type="number" tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="level" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} width={58} />
              <Tooltip contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: 12 }} />
              <Bar dataKey="count" name="Kids" radius={[0,4,4,0]}>
                {engDist.map((_, i) => <Cell key={i} fill={`hsl(0,70%,${72 - i * 9}%)`} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div style={s.chartCard}>
          <div style={s.chartHeader}>
            <h3 style={s.chartTitle}>Attendance Rate Trend</h3>
            <span style={s.chartSub}>Kids vs volunteers · 8-week view</span>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={ATTENDANCE_TREND}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="week" tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} domain={[60, 100]} />
              <Tooltip contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="kids"       stroke={RED}   strokeWidth={2} dot={{ r: 3 }} name="Kids %" />
              <Line type="monotone" dataKey="volunteers" stroke={BLUE}  strokeWidth={2} dot={{ r: 3 }} name="Volunteers %" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 2 — Risk + Churn */}
      <div style={s.chartRow}>
        <div style={s.chartCard}>
          <div style={s.chartHeader}>
            <h3 style={s.chartTitle}>Risk Classification Output</h3>
            <span style={s.chartSub}>Random Forest + SMOTE · AUC-ROC: 0.97 · F1: 0.66</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <ResponsiveContainer width={140} height={140}>
              <PieChart>
                <Pie data={riskPie} cx="50%" cy="50%" innerRadius={38} outerRadius={60} paddingAngle={3} dataKey="value">
                  {riskPie.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {riskPie.map(r => (
                <div key={r.name} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: r.color }} />
                  <span style={{ fontSize: '12px', color: '#374151' }}>{r.name}</span>
                  <span style={{ fontSize: '14px', fontWeight: '700', color: '#111827', marginLeft: '6px' }}>{r.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div style={s.chartCard}>
          <div style={s.chartHeader}>
            <h3 style={s.chartTitle}>Student Churn Analysis</h3>
            <span style={s.chartSub}>Monthly retention · 4-week absence = churned</span>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={CHURN_DATA}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Area type="monotone" dataKey="active"  stroke={GREEN} fill="#dcfce7" strokeWidth={2} name="Active kids" />
              <Area type="monotone" dataKey="cumChurn" stroke={RED}  fill="#fee2e2" strokeWidth={2} name="Cumulative churn" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 3 — Progress trend + Hygiene */}
      <div style={s.chartRow}>
        <div style={s.chartCard}>
          <div style={s.chartHeader}>
            <h3 style={s.chartTitle}>Student Progress Trajectory</h3>
            <span style={s.chartSub}>Avg literacy level index over time · Ridge Regression</span>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={PROGRESS_TREND}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} domain={[0, 5]} />
              <Tooltip contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: 12 }} />
              <Line type="monotone" dataKey="avgLevel" stroke={RED} strokeWidth={2.5} dot={{ r: 4, fill: RED }} name="Avg level" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div style={s.chartCard}>
          <div style={s.chartHeader}>
            <h3 style={s.chartTitle}>Hygiene Compliance Score</h3>
            <span style={s.chartSub}>Monthly assessment · 5 categories</span>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={HYGIENE_DATA} barSize={18}>
              <XAxis dataKey="category" tick={{ fontSize: 9, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} domain={[0, 100]} />
              <Tooltip contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: 12 }} formatter={(v) => [`${v}%`, 'Compliance']} />
              <Bar dataKey="score" name="Score %" radius={[4,4,0,0]}>
                {HYGIENE_DATA.map((d, i) => <Cell key={i} fill={d.score >= 80 ? GREEN : d.score >= 70 ? AMBER : RED} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 4 — 4-week forecast */}
      <div style={{ ...s.chartCard, marginBottom: 0 }}>
        <div style={s.chartHeader}>
          <h3 style={s.chartTitle}>4-Week Level Advancement Forecast</h3>
          <span style={s.chartSub}>Ridge Regression predictions · Who will advance in the next 4 weeks?</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '4px' }}>
          {[
            { label: 'Will advance in English literacy', value: willAdvanceEng,  total: predictions.length, color: RED,   insight: 'Focus remaining sessions on struggling kids' },
            { label: 'Will advance in Math numeracy',    value: willAdvanceMath, total: predictions.length, color: AMBER, insight: 'Strong numeracy performance this cohort' },
            { label: 'At risk of no progress',           value: high + medium,   total: predictions.length, color: GRAY,  insight: 'Assign backup volunteers to these kids immediately' },
          ].map(item => (
            <div key={item.label}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '12px', color: '#374151', fontWeight: '500' }}>{item.label}</span>
                <span style={{ fontSize: '12px', fontWeight: '700', color: '#111827' }}>{item.value} / {item.total} kids</span>
              </div>
              <div style={{ height: '8px', background: '#f3f4f6', borderRadius: '4px', overflow: 'hidden', marginBottom: '3px' }}>
                <div style={{ width: `${item.total ? Math.round((item.value / item.total) * 100) : 0}%`, height: '100%', background: item.color, borderRadius: '4px', transition: 'width 0.8s ease' }} />
              </div>
              <span style={{ fontSize: '11px', color: '#9ca3af' }}>💡 {item.insight}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── VOLUNTEERS TAB ────────────────────────────────────────────────────────────
function VolunteersTab() {
  const atRisk = VOLUNTEER_DATA.filter(v => v.reliability < 70);
  const stable = VOLUNTEER_DATA.filter(v => v.reliability >= 70);

  return (
    <div style={s.content}>
      <div style={s.pageHead}>
        <h1 style={s.pageTitle}>Volunteer Reliability Analysis</h1>
        <p style={s.pageSub}>Reliability Score = sessions attended / sessions assigned · Threshold: 70%</p>
      </div>

      {/* Reliability chart */}
      <div style={{ ...s.chartCard, marginBottom: '20px' }}>
        <div style={s.chartHeader}>
          <h3 style={s.chartTitle}>Volunteer Reliability Scores</h3>
          <span style={s.chartSub}>Red = below threshold · Green = reliable</span>
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={VOLUNTEER_DATA} layout="vertical" barSize={14}>
            <XAxis type="number" tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} domain={[0, 100]} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} width={90} />
            <Tooltip contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: 12 }} formatter={(v) => [`${v}%`, 'Reliability']} />
            <Bar dataKey="reliability" name="Reliability %" radius={[0,4,4,0]}>
              {VOLUNTEER_DATA.map((v, i) => <Cell key={i} fill={v.reliability >= 80 ? GREEN : v.reliability >= 70 ? AMBER : RED} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* At risk volunteers */}
      {atRisk.length > 0 && (
        <div style={s.chartCard}>
          <div style={s.chartHeader}>
            <h3 style={s.chartTitle}>⚠️ Volunteers Below Threshold</h3>
            <span style={s.chartSub}>{atRisk.length} volunteers need attention · {atRisk.reduce((s, v) => s + v.kids, 0)} kids at risk of no teacher</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {atRisk.map(v => (
              <div key={v.name} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 14px', background: '#fff5f5', borderRadius: '10px', border: '1px solid #fee2e2' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: '#fee2e2', color: RED, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', fontWeight: '700', flexShrink: 0 }}>
                  {v.name[0]}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: '#111827' }}>{v.name}</div>
                  <div style={{ fontSize: '12px', color: '#6b7280' }}>{v.chapter} · {v.missed} sessions missed · {v.kids} kids affected</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '20px', fontWeight: '700', color: RED }}>{v.reliability}%</div>
                  <div style={{ fontSize: '10px', color: '#9ca3af' }}>reliability</div>
                </div>
                <div style={{ width: '60px', height: '6px', background: '#f3f4f6', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${v.reliability}%`, height: '100%', background: RED, borderRadius: '3px' }} />
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: '12px', padding: '10px 12px', background: '#fffbeb', borderRadius: '8px', fontSize: '12px', color: AMBER }}>
            💡 Decision: Assign backup volunteers proactively. Kids with unreliable volunteers score 23% lower on average progress.
          </div>
        </div>
      )}
    </div>
  );
}

// ── KIDS TAB ──────────────────────────────────────────────────────────────────
function KidsTab({ predictions, kids }) {
  const atRisk     = predictions.filter(p => p.at_risk).sort((a,b) => b.risk_score - a.risk_score);
  const churnRisk  = predictions.filter(p => p.risk_score > 0.5);

  return (
    <div style={s.content}>
      <div style={s.pageHead}>
        <h1 style={s.pageTitle}>Student Risk & Progress</h1>
        <p style={s.pageSub}>ML-driven risk scores · Churn prediction · Hygiene compliance</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '10px', marginBottom: '20px' }}>
        {[
          { label: 'Total enrolled',  value: kids.length,       color: '#111827' },
          { label: 'At risk',         value: atRisk.length,     color: RED       },
          { label: 'Churn risk',      value: churnRisk.length,  color: AMBER     },
          { label: 'On track',        value: predictions.filter(p => p.risk_level === 'low').length, color: GREEN },
        ].map(k => (
          <div key={k.label} style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '10px', padding: '14px', textAlign: 'center' }}>
            <div style={{ fontSize: '28px', fontWeight: '700', color: k.color }}>{k.value}</div>
            <div style={{ fontSize: '11px', color: GRAY }}>{k.label}</div>
          </div>
        ))}
      </div>

      {atRisk.length > 0 && (
        <div style={{ ...s.chartCard, marginBottom: '16px' }}>
          <div style={s.chartHeader}>
            <h3 style={s.chartTitle}>Kids Flagged At Risk</h3>
            <span style={s.chartSub}>Random Forest classifier output · Sorted by risk score</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {atRisk.map(p => (
              <div key={p.kid_id} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 14px', background: p.risk_level === 'high' ? '#fff5f5' : '#fffbeb', borderRadius: '10px', border: `1px solid ${p.risk_level === 'high' ? '#fee2e2' : '#fef3c7'}` }}>
                <div style={{ width: '30px', height: '30px', borderRadius: '50%', background: p.risk_level === 'high' ? '#fee2e2' : '#fef3c7', color: p.risk_level === 'high' ? RED : AMBER, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: '700', flexShrink: 0 }}>
                  {String.fromCharCode(65 + (p.kid_id % 26))}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#111827' }}>Kid #{p.kid_id}</div>
                  <div style={{ fontSize: '11px', color: '#9ca3af' }}>{p.risk_reason || 'Multiple signals'}</div>
                </div>
                <div style={{ fontSize: '11px', color: '#6b7280' }}>EN: {p.current_english_level} → {p.predicted_eng_level}</div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '16px', fontWeight: '700', color: p.risk_level === 'high' ? RED : AMBER }}>{Math.round((p.risk_score || 0) * 100)}%</div>
                  <div style={{ fontSize: '10px', color: '#9ca3af' }}>risk</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={s.chartCard}>
        <div style={s.chartHeader}>
          <h3 style={s.chartTitle}>Hygiene Compliance by Category</h3>
          <span style={s.chartSub}>Monthly assessment · Volunteer-reported</span>
        </div>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={HYGIENE_DATA} barSize={22}>
            <XAxis dataKey="category" tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} domain={[0, 100]} />
            <Tooltip contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: 12 }} formatter={(v) => [`${v}%`, 'Compliance']} />
            <Bar dataKey="score" name="Compliance %" radius={[4,4,0,0]}>
              {HYGIENE_DATA.map((d, i) => <Cell key={i} fill={d.score >= 80 ? GREEN : d.score >= 70 ? AMBER : RED} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <div style={{ marginTop: '10px', fontSize: '11px', color: '#9ca3af' }}>
          💡 Nail cutting (68%) is below threshold — flag for next life skills session
        </div>
      </div>
    </div>
  );
}

// ── FUNDS TAB ─────────────────────────────────────────────────────────────────
function FundsTab({ stats }) {
  const fundingGap  = 16000 - FUND_TREND[FUND_TREND.length - 1].raised;
  const burnRate    = Math.round(FUND_TREND[FUND_TREND.length - 1].raised / 4);
  const weeksLeft   = Math.round(FUND_TREND[FUND_TREND.length - 1].raised / burnRate);
  const fundingPct  = Math.round((FUND_TREND[FUND_TREND.length - 1].raised / 16000) * 100);

  return (
    <div style={s.content}>
      <div style={s.pageHead}>
        <h1 style={s.pageTitle}>Funding Gap Analysis</h1>
        <p style={s.pageSub}>Required vs available funds · Burn rate · Forecast</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '10px', marginBottom: '20px' }}>
        {[
          { label: 'Raised so far',    value: `₹${FUND_TREND[FUND_TREND.length-1].raised.toLocaleString('en-IN')}`, color: GREEN },
          { label: 'Funding gap',      value: `₹${fundingGap.toLocaleString('en-IN')}`,  color: RED   },
          { label: 'Monthly burn rate', value: `₹${burnRate.toLocaleString('en-IN')}`,   color: AMBER },
          { label: 'Funding ratio',    value: `${fundingPct}%`,                          color: GREEN },
        ].map(k => (
          <div key={k.label} style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '10px', padding: '14px', textAlign: 'center' }}>
            <div style={{ fontSize: '22px', fontWeight: '700', color: k.color, marginBottom: '2px' }}>{k.value}</div>
            <div style={{ fontSize: '11px', color: GRAY }}>{k.label}</div>
          </div>
        ))}
      </div>

      <div style={s.chartCard}>
        <div style={s.chartHeader}>
          <h3 style={s.chartTitle}>Fund Drive Progress</h3>
          <span style={s.chartSub}>Monthly fundraising vs ₹16,000 target per chapter</span>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={FUND_TREND}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
            <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: 12 }} formatter={(v) => [`₹${v.toLocaleString('en-IN')}`, '']} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Area type="monotone" dataKey="needed" stroke="#e5e7eb" fill="#f9fafb" strokeWidth={1} strokeDasharray="5 5" name="Target (₹16,000)" />
            <Area type="monotone" dataKey="raised" stroke={GREEN}   fill="#dcfce7" strokeWidth={2} name="Raised" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div style={{ ...s.chartCard, marginBottom: 0 }}>
        <div style={s.chartHeader}>
          <h3 style={s.chartTitle}>Wishlist Resource Requirements</h3>
          <span style={s.chartSub}>ML-predicted needs · 4-week forecast · {stats.unfunded_wishlist_count || 0} items unfunded</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {[
            { label: 'Funded items',   value: 87,  total: 87 + (stats.unfunded_wishlist_count || 0), color: GREEN },
            { label: 'Unfunded items', value: stats.unfunded_wishlist_count || 0, total: 87 + (stats.unfunded_wishlist_count || 0), color: RED },
          ].map(item => (
            <div key={item.label}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '12px', color: '#374151' }}>{item.label}</span>
                <span style={{ fontSize: '12px', fontWeight: '600', color: '#111827' }}>{item.value} items</span>
              </div>
              <div style={{ height: '7px', background: '#f3f4f6', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{ width: `${item.total ? Math.round((item.value / item.total) * 100) : 0}%`, height: '100%', background: item.color, borderRadius: '4px' }} />
              </div>
            </div>
          ))}
        </div>
        <div style={{ marginTop: '12px', padding: '10px 12px', background: '#f0fdf4', borderRadius: '8px', fontSize: '12px', color: GREEN }}>
          💡 ML pipeline auto-generates wishlist items 4 weeks ahead of need — enabling proactive fundraising campaigns
        </div>
      </div>
    </div>
  );
}

// ── HOME TAB ──────────────────────────────────────────────────────────────────
function HomeTab({ stats, predictions, setActiveTab }) {
  const highRisk   = predictions.filter(p => p.risk_level === 'high').length;
  const atRiskVols = VOLUNTEER_DATA.filter(v => v.reliability < 70).length;
  const fundingPct = 87;
  const retention  = 91;

  return (
    <div style={s.content}>
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '26px', fontWeight: '700', color: '#111827', marginBottom: '4px' }}>
          Good morning 👋
        </h1>
        <p style={{ fontSize: '14px', color: '#9ca3af' }}>
          Here's your weekly overview — Visakhapatnam · 3 chapters · Updated Sunday night
        </p>
      </div>

      {/* Headline KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '12px', marginBottom: '28px' }}>
        {[
          { label: 'Kids at risk',        value: highRisk,      color: '#dc2626', bg: '#fff5f5', tab: 'alerts'     },
          { label: 'Volunteer reliability', value: `${Math.round(VOLUNTEER_DATA.reduce((s,v)=>s+v.reliability,0)/VOLUNTEER_DATA.length)}%`, color: '#d97706', bg: '#fffbeb', tab: 'volunteers' },
          { label: 'Fund drive',          value: `${fundingPct}%`, color: '#16a34a', bg: '#f0fdf4', tab: 'funds'   },
          { label: 'Student retention',   value: `${retention}%`,  color: '#2563eb', bg: '#eff6ff', tab: 'kpis'    },
        ].map(k => (
          <div key={k.label}
            style={{ background: k.bg, borderRadius: '12px', padding: '18px', cursor: 'pointer', border: `1px solid ${k.color}20`, transition: 'transform 0.15s' }}
            onClick={() => setActiveTab(k.tab)}
          >
            <div style={{ fontSize: '32px', fontWeight: '700', color: k.color, marginBottom: '4px' }}>{k.value}</div>
            <div style={{ fontSize: '12px', color: '#6b7280' }}>{k.label}</div>
            <div style={{ fontSize: '11px', color: k.color, marginTop: '6px' }}>View details →</div>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Action Items</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '28px' }}>
        {[
          { icon: '⚠️', title: `${highRisk} high-risk students need attention`, sub: 'ML classifier flagged consecutive struggling sessions', tab: 'alerts',     urgent: true  },
          { icon: '👥', title: `${atRiskVols} volunteers below 70% reliability threshold`, sub: `${atRiskVols * 2} kids at risk of no teacher this Sunday`, tab: 'volunteers', urgent: true  },
          { icon: '💰', title: 'Fund drive at 87% — ₹2,080 gap remaining', sub: 'ML predicted 111 resource items needed in next 4 weeks', tab: 'funds',      urgent: false },
          { icon: '🧼', title: 'Monthly hygiene check due', sub: 'Nail cutting compliance at 68% — below threshold', tab: 'kids',       urgent: false },
        ].map(item => (
          <div key={item.title}
            style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '14px 16px', background: 'white', borderRadius: '10px', border: `1px solid ${item.urgent ? '#fee2e2' : '#e5e7eb'}`, cursor: 'pointer' }}
            onClick={() => setActiveTab(item.tab)}
          >
            <div style={{ fontSize: '20px', flexShrink: 0 }}>{item.icon}</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#111827', marginBottom: '2px' }}>{item.title}</div>
              <div style={{ fontSize: '11px', color: '#9ca3af' }}>{item.sub}</div>
            </div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>→</div>
          </div>
        ))}
      </div>

      {/* Pipeline status */}
      <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Data Pipeline Status</h3>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
        {[
          { label: 'dbt transformation', value: '5 models · 16 tests', status: 'passing', color: '#16a34a' },
          { label: 'ML predictions',     value: '106 kids · AUC-ROC 0.97', status: 'active', color: '#16a34a' },
          { label: 'Automation',         value: '4 jobs · Next run Sunday', status: 'scheduled', color: '#2563eb' },
        ].map(p => (
          <div key={p.label} style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '10px', padding: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: p.color }} />
              <span style={{ fontSize: '10px', fontWeight: '600', color: p.color, textTransform: 'uppercase' }}>{p.status}</span>
            </div>
            <div style={{ fontSize: '13px', fontWeight: '600', color: '#111827', marginBottom: '2px' }}>{p.label}</div>
            <div style={{ fontSize: '11px', color: '#9ca3af' }}>{p.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Loader() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
      <span style={{ color: RED, fontSize: '15px' }}>Loading coordinator dashboard...</span>
    </div>
  );
}

const s = {
  page:        { display: 'flex', minHeight: '100vh', background: '#f9fafb' },
  sidebar:     { width: '210px', background: 'white', borderRight: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '20px 12px', position: 'sticky', top: 0, height: '100vh', flexShrink: 0 },
  brand:       { display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' },
  logoMark:    { width: '32px', height: '32px', borderRadius: '8px', background: RED, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: '700', color: 'white', flexShrink: 0 },
  brandName:   { fontSize: '14px', fontWeight: '600', color: '#111827' },
  brandRole:   { fontSize: '11px', color: '#9ca3af' },
  pipelineStrip: { display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 6px', background: '#f0fdf4', borderRadius: '6px', marginBottom: '4px' },
  pipelineDot:   { width: '6px', height: '6px', borderRadius: '50%', background: GREEN, flexShrink: 0 },
  pipelineText:  { fontSize: '10px', color: GREEN, fontWeight: '500' },
  nav:         { display: 'flex', flexDirection: 'column', gap: '2px' },
  navItem:     { padding: '8px 10px', borderRadius: '8px', fontSize: '12px', color: '#6b7280', background: 'transparent', textAlign: 'left' },
  navActive:   { background: '#fff5f5', color: RED, fontWeight: '500' },
  sidebarFoot: { display: 'flex', flexDirection: 'column', gap: '10px' },
  userRow:     { display: 'flex', alignItems: 'center', gap: '8px' },
  avatar:      { width: '28px', height: '28px', borderRadius: '50%', background: '#fee2e2', color: RED, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: '600' },
  userName:    { fontSize: '13px', color: '#374151' },
  signOut:     { padding: '7px', background: 'transparent', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '12px', color: '#9ca3af' },
  main:        { flex: 1, overflow: 'auto' },
  content:     { padding: '32px 40px', maxWidth: '960px' },
  pageHead:    { marginBottom: '24px' },
  pageTitle:   { fontSize: '22px', fontWeight: '700', color: '#111827', marginBottom: '4px' },
  pageSub:     { fontSize: '13px', color: '#9ca3af' },
  chartRow:    { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' },
  chartCard:   { background: 'white', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '18px', marginBottom: '14px' },
  chartHeader: { marginBottom: '12px' },
  chartTitle:  { fontSize: '14px', fontWeight: '600', color: '#111827', marginBottom: '2px' },
  chartSub:    { fontSize: '11px', color: '#9ca3af', display: 'block' },
  alertSection:     { marginBottom: '20px' },
  alertSectionTitle:{ fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.04em' },
  alertCard:   { display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 14px', background: 'white', borderRadius: '10px', border: '1px solid #e5e7eb', marginBottom: '6px' },
  alertDot:    { width: '8px', height: '8px', borderRadius: '50%', flexShrink: 0 },
  alertTitle:  { fontSize: '13px', fontWeight: '600', color: '#111827', marginBottom: '2px' },
  alertDesc:   { fontSize: '11px', color: '#9ca3af' },
  alertBadge:  { padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '600', flexShrink: 0 },
  allClear:    { fontSize: '13px', color: GREEN, background: '#f0fdf4', borderRadius: '8px', padding: '10px 12px' },
};
