import { useRef, useMemo } from 'react';
import { motion, useInView } from 'framer-motion';
import { JOBS, MARKET_INSIGHTS } from '../data/mockData';
import { Target, Rocket, Layers } from 'lucide-react';

/* ─── Command Center Card ─── */
function InsightCard({ title, icon: Icon, children, delay = 0 }) {
  return (
    <motion.div
      initial={{ y: 30, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, delay }}
      className="glass-light rounded-2xl p-6 hover:shadow-lg hover:shadow-cyan-100/50 transition-all duration-300"
    >
      <div className="flex items-center gap-2.5 mb-4">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-500 to-teal-500 flex items-center justify-center text-white">
          <Icon className="w-4 h-4" strokeWidth={2} />
        </div>
        <h3 className="font-semibold text-slate-700 text-sm">{title}</h3>
      </div>
      {children}
    </motion.div>
  );
}

/* ─── Depth Label ─── */
function DepthLabel({ label, depth }) {
  const colors = {
    shallow: 'text-cyan-300',
    mid: 'text-teal-400',
    deep: 'text-indigo-400',
    abyss: 'text-purple-400',
  };
  const glows = {
    shallow: 'rgba(0,255,213,0.15)',
    mid: 'rgba(0,200,180,0.12)',
    deep: 'rgba(99,102,241,0.12)',
    abyss: 'rgba(168,85,247,0.12)',
  };
  return (
    <div className="flex items-center gap-3 py-6 max-w-3xl mx-auto px-4">
      <div className="flex-1 h-px" style={{ background: `linear-gradient(to right, transparent, ${glows[depth]}, transparent)` }} />
      <span className={`text-xs font-semibold uppercase tracking-[0.2em] ${colors[depth]}`}>{label}</span>
      <div className="flex-1 h-px" style={{ background: `linear-gradient(to left, transparent, ${glows[depth]}, transparent)` }} />
    </div>
  );
}

/* ─── Job Row (card + connector + center dot) ─── */
function JobRow({ job, side, onSelect }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-60px' });

  const palette = {
    shallow: { accent: '#00ffd5', border: 'rgba(0,255,213,0.18)', bg: 'rgba(0,30,50,0.5)', glow: 'rgba(0,255,213,0.12)', hoverGlow: '0 0 40px rgba(0,255,213,0.25)' },
    mid:     { accent: '#00c8b4', border: 'rgba(0,200,180,0.15)', bg: 'rgba(0,20,40,0.55)', glow: 'rgba(0,200,180,0.10)', hoverGlow: '0 0 40px rgba(0,200,180,0.22)' },
    deep:    { accent: '#818cf8', border: 'rgba(99,102,241,0.15)', bg: 'rgba(10,10,30,0.6)', glow: 'rgba(99,102,241,0.10)', hoverGlow: '0 0 40px rgba(99,102,241,0.22)' },
    abyss:   { accent: '#a855f7', border: 'rgba(168,85,247,0.15)', bg: 'rgba(5,5,20,0.7)', glow: 'rgba(168,85,247,0.10)', hoverGlow: '0 0 40px rgba(168,85,247,0.22)' },
  };
  const c = palette[job.depth] || palette.shallow;

  return (
    <div ref={ref} className="grid items-center max-w-4xl mx-auto" style={{ gridTemplateColumns: '1fr 14px 1fr' }}>
      {/* LEFT COLUMN */}
      {side === 'left' ? (
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={isInView ? { opacity: 1, x: 0 } : {}}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="flex items-center justify-end"
        >
          {/* Card */}
          <motion.button
            whileHover={{ scale: 1.03, boxShadow: c.hoverGlow }}
            onClick={() => onSelect(job)}
            className="w-60 md:w-72 p-5 rounded-2xl text-left transition-all duration-300 cursor-pointer backdrop-blur-xl shrink-0"
            style={{ background: c.bg, border: `1px solid ${c.border}`, boxShadow: `0 0 24px ${c.glow}` }}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded-md" style={{ color: c.accent, background: `${c.accent}15` }}>
                {job.matchRate}% match
              </span>
              <span className="text-[10px] uppercase tracking-widest text-white/25 font-medium">{job.matchType}</span>
            </div>
            <h3 className="text-base font-semibold text-white/90 mb-1 leading-snug">{job.title}</h3>
            <p className="text-sm text-white/40 font-medium">{job.company}</p>
          </motion.button>
          {/* Horizontal connector line */}
          <div className="h-px flex-1 min-w-4" style={{ background: `linear-gradient(to right, transparent, ${c.accent}60)` }} />
        </motion.div>
      ) : (
        <div />
      )}

      {/* CENTER DOT — sits exactly on the fishing line */}
      <motion.div
        initial={{ scale: 0 }}
        animate={isInView ? { scale: 1 } : {}}
        transition={{ duration: 0.4, delay: 0.3 }}
        className="flex items-center justify-center"
      >
        <div
          className="w-3.5 h-3.5 rounded-full"
          style={{ background: c.accent, boxShadow: `0 0 12px ${c.accent}80, 0 0 24px ${c.accent}30` }}
        />
      </motion.div>

      {/* RIGHT COLUMN */}
      {side === 'right' ? (
        <motion.div
          initial={{ opacity: 0, x: 50 }}
          animate={isInView ? { opacity: 1, x: 0 } : {}}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="flex items-center justify-start"
        >
          {/* Horizontal connector line */}
          <div className="h-px flex-1 min-w-4" style={{ background: `linear-gradient(to left, transparent, ${c.accent}60)` }} />
          {/* Card */}
          <motion.button
            whileHover={{ scale: 1.03, boxShadow: c.hoverGlow }}
            onClick={() => onSelect(job)}
            className="w-60 md:w-72 p-5 rounded-2xl text-left transition-all duration-300 cursor-pointer backdrop-blur-xl shrink-0"
            style={{ background: c.bg, border: `1px solid ${c.border}`, boxShadow: `0 0 24px ${c.glow}` }}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded-md" style={{ color: c.accent, background: `${c.accent}15` }}>
                {job.matchRate}% match
              </span>
              <span className="text-[10px] uppercase tracking-widest text-white/25 font-medium">{job.matchType}</span>
            </div>
            <h3 className="text-base font-semibold text-white/90 mb-1 leading-snug">{job.title}</h3>
            <p className="text-sm text-white/40 font-medium">{job.company}</p>
          </motion.button>
        </motion.div>
      ) : (
        <div />
      )}
    </div>
  );
}

/* ─── Bubbles ─── */
function Bubbles() {
  const bubbles = useMemo(() =>
    [...Array(18)].map(() => ({
      left: `${5 + Math.random() * 90}%`,
      size: 3 + Math.random() * 5,
      duration: 8 + Math.random() * 15,
      delay: Math.random() * 10,
      opacity: 0.1 + Math.random() * 0.2,
    })),
  []);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {bubbles.map((b, i) => (
        <div
          key={i}
          className="bubble"
          style={{
            left: b.left, bottom: '-20px',
            width: `${b.size}px`, height: `${b.size}px`,
            opacity: b.opacity,
            animationDuration: `${b.duration}s`,
            animationDelay: `${b.delay}s`,
          }}
        />
      ))}
    </div>
  );
}

/* ─── Main Component ─── */
export default function Zone3Descent({ onSelectJob }) {
  const insights = MARKET_INSIGHTS;

  const shallowJobs = JOBS.filter((j) => j.depth === 'shallow');
  const midJobs = JOBS.filter((j) => j.depth === 'mid');
  const deepJobs = JOBS.filter((j) => j.depth === 'deep');
  const abyssJobs = JOBS.filter((j) => j.depth === 'abyss');

  const allSections = [
    { label: 'Surface — Matched by Wants', depth: 'shallow', jobs: shallowJobs },
    { label: 'Twilight Zone — Balanced Match', depth: 'mid', jobs: midJobs },
    { label: 'Deep Water — Skills Match', depth: 'deep', jobs: deepJobs },
    { label: 'The Abyss — High Skill Ceiling', depth: 'abyss', jobs: abyssJobs },
  ];

  let globalIndex = 0;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
    >
      {/* ════════════════════════════════════════════════════
          ABOVE WATER — Command Center + Boat on Water
         ════════════════════════════════════════════════════ */}
      <div
        className="relative"
        style={{
          background: 'linear-gradient(180deg, #ecfeff 0%, #cffafe 25%, #a5f3fc 55%, #67e8f9 85%, #22d3ee 100%)',
        }}
      >
        {/* Sunlight */}
        <div
          className="absolute -top-20 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full opacity-30 pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(255,255,255,0.8) 0%, transparent 70%)' }}
        />

        <div className="relative z-10 max-w-4xl mx-auto px-6 pt-12 pb-16">
          {/* Header */}
          <motion.div
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-10"
          >
            <div className="inline-flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-500 to-teal-600 flex items-center justify-center shadow-md shadow-cyan-500/20">
                <Layers className="w-4 h-4 text-white" strokeWidth={2.5} />
              </div>
              <span className="text-lg font-bold text-cyan-700/70 tracking-tight">Reef</span>
            </div>
            <h1 className="text-3xl md:text-4xl font-extrabold text-slate-800 tracking-tight mb-2">
              Your Command Center
            </h1>
            <p className="text-slate-500 max-w-md mx-auto text-sm">
              AI-generated insights for your profile. Scroll down to dive into matched roles.
            </p>
          </motion.div>

          {/* Insight Cards — 2 columns */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-6">
            <InsightCard title="Best Roles to Target" icon={Target} delay={0.2}>
              <div className="space-y-2.5">
                {insights.bestRoles.map((role, i) => (
                  <div key={i} className="flex items-center justify-between bg-white/50 rounded-xl px-3.5 py-2.5">
                    <div>
                      <p className="text-sm font-medium text-slate-700">{role.title}</p>
                      <p className="text-xs text-slate-400">Demand: {role.demand}</p>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-10 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                        <div className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-teal-400" style={{ width: `${role.fit}%` }} />
                      </div>
                      <span className="text-xs font-semibold text-cyan-600">{role.fit}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </InsightCard>

            <InsightCard title="Skills to Learn Next" icon={Rocket} delay={0.35}>
              <div className="space-y-3">
                {insights.skillsToLearn.map((s, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${
                        s.priority === 'Critical' ? 'bg-rose-400' : s.priority === 'High' ? 'bg-amber-400' : 'bg-emerald-400'
                      }`} />
                      <span className="text-sm text-slate-700">{s.skill}</span>
                    </div>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                      s.priority === 'Critical' ? 'bg-rose-50 text-rose-500'
                        : s.priority === 'High' ? 'bg-amber-50 text-amber-600'
                        : 'bg-emerald-50 text-emerald-600'
                    }`}>
                      {s.priority}
                    </span>
                  </div>
                ))}
              </div>
            </InsightCard>
          </div>
        </div>

      </div>

      {/* ════════════════════════════════════════════════════
          BELOW WATER — The Descent
         ════════════════════════════════════════════════════ */}
      <div
        className="relative overflow-visible"
        style={{
          background: 'linear-gradient(180deg, #0e7490 0%, #0c4a6e 5%, #082f49 14%, #061b30 26%, #041225 46%, #020a18 66%, #01050e 83%, #000208 100%)',
        }}
      >
        <Bubbles />

        {/* ── THE FISHING LINE — starts at top-0 and runs to bottom ── */}
        <div
          className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-px pointer-events-none vine-line"
          style={{
            background: 'linear-gradient(180deg, rgba(0,255,213,0.6) 0%, rgba(0,255,213,0.35) 25%, rgba(99,102,241,0.3) 55%, rgba(168,85,247,0.2) 80%, rgba(168,85,247,0.05) 100%)',
          }}
        />

        {/* ── BOAT + FISHERMAN ──
            Wrapper div handles centering (left-1/2 -translate-x-1/2).
            Inner motion.div handles the gentle float animation.
            This separation prevents Framer Motion from overriding the centering transform.

            SVG layout (viewBox 0 0 200 120):
              • Person sits at y=0–58, centered at x=100 (SVG center = page center)
              • Hull: y=60–120 (top edge = waterline)
              • Rod tip at x=100, y=14  →  fishing line goes straight down x=100
              • x=100 = 50% of 200px = page center = central fishing line position
        */}
        <div
          className="absolute left-1/2 -translate-x-1/2 z-30 pointer-events-none"
          style={{ width: 340, top: -155 }}
        >
          <motion.div
            animate={{ y: [0, -5, 0], rotate: [0, -0.6, 0, 0.6, 0] }}
            transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
          >
            <svg viewBox="0 0 200 120" fill="none" xmlns="http://www.w3.org/2000/svg">

              {/* ── Fishing rod — from hand at x=115 arcing forward to tip at x=100 ── */}
              <path
                d="M115 36 Q110 28 105 22 Q102 18 100 14"
                stroke="#8B7355" strokeWidth="2" strokeLinecap="round" fill="none"
              />
              {/* Rod handle behind hand */}
              <path d="M115 36 Q118 40 120 44" stroke="#8B7355" strokeWidth="2.5" strokeLinecap="round" fill="none" />

              {/* ── Fishing line from rod tip (x=100) straight down ── */}
              {/* In air — thin dashed */}
              <line x1="100" y1="14" x2="100" y2="60"
                stroke="rgba(0,255,213,0.3)" strokeWidth="0.8" strokeDasharray="3 2" />
              {/* In water — glowing, connects to central line below */}
              <line x1="100" y1="60" x2="100" y2="120"
                stroke="rgba(0,255,213,0.55)" strokeWidth="0.8"
                style={{ filter: 'drop-shadow(0 0 3px rgba(0,255,213,0.5))' }} />
              {/* Hook at waterline */}
              <path d="M100 56 L100 64 Q100 68 97 69 Q95 70 95 67"
                stroke="#00ffd5" strokeWidth="1.2" strokeLinecap="round" fill="none"
                style={{ filter: 'drop-shadow(0 0 4px rgba(0,255,213,0.6))' }} />

              {/* ── Fisherman — seated on hull, holding rod forward ── */}
              {/* Head */}
              <circle cx="112" cy="16" r="8" fill="#FABE91" />
              {/* Bucket hat */}
              <ellipse cx="112" cy="11" rx="10" ry="3" fill="#2D7A8A" />
              <path d="M104 11 Q105 5 112 3 Q119 5 120 11" fill="#2D7A8A" />
              {/* Body — slight forward lean */}
              <path d="M105 24 L119 24 L118 48 L106 48 Z" fill="#1A8A9A" />
              {/* Right arm — extends forward to grip rod */}
              <path d="M119 32 Q118 38 120 44" stroke="#FABE91" strokeWidth="4" strokeLinecap="round" fill="none" />
              {/* Left arm — reaches forward toward rod */}
              <path d="M105 32 Q102 36 100 34" stroke="#FABE91" strokeWidth="4" strokeLinecap="round" fill="none" />
              {/* Legs — seated, dangling at hull edge */}
              <path d="M108 48 Q106 54 104 58" stroke="#1E6A7A" strokeWidth="4" strokeLinecap="round" fill="none" />
              <path d="M116 48 Q118 54 120 58" stroke="#1E6A7A" strokeWidth="4" strokeLinecap="round" fill="none" />

              {/* ── Boat hull — top at y=60 (waterline), bottom at y=120 (SVG bottom) ── */}
              <path d="M15 60 L32 120 L168 120 L185 60 Z" fill="url(#hullG5)" />
              <path d="M15 60 L185 60" stroke="rgba(255,255,255,0.12)" strokeWidth="0.8" />
              <path d="M28 85 L172 85" stroke="rgba(255,255,255,0.15)" strokeWidth="1" />
              {/* Portholes */}
              <circle cx="72" cy="98" r="3.5" fill="rgba(255,255,255,0.08)" stroke="rgba(255,255,255,0.12)" strokeWidth="0.6" />
              <circle cx="100" cy="98" r="3.5" fill="rgba(255,255,255,0.08)" stroke="rgba(255,255,255,0.12)" strokeWidth="0.6" />
              <circle cx="128" cy="98" r="3.5" fill="rgba(255,255,255,0.08)" stroke="rgba(255,255,255,0.12)" strokeWidth="0.6" />

              <defs>
                <linearGradient id="hullG5" x1="15" y1="60" x2="185" y2="120">
                  <stop offset="0%" stopColor="#0e7490" />
                  <stop offset="50%" stopColor="#0a5f7a" />
                  <stop offset="100%" stopColor="#074f68" />
                </linearGradient>
              </defs>
            </svg>
          </motion.div>
        </div>

        {/* ── Animated waves at surface — z-20 renders over hull/water seam ── */}
        <div className="absolute top-0 left-0 right-0 z-20 overflow-hidden pointer-events-none" style={{ height: 50 }}>
          <svg
            viewBox="0 0 1440 50"
            className="absolute top-0 w-[200%] h-full"
            preserveAspectRatio="none"
            style={{ animation: 'wave-drift 7s linear infinite' }}
          >
            <path
              d="M0,16 C120,38 240,2 360,20 C480,38 600,2 720,20 C840,38 960,2 1080,20 C1200,38 1320,2 1440,20 L1440,50 L0,50 Z"
              fill="#0e7490"
            />
          </svg>
          <svg
            viewBox="0 0 1440 50"
            className="absolute top-0 w-[200%] h-full"
            preserveAspectRatio="none"
            style={{ animation: 'wave-drift 11s linear infinite reverse' }}
          >
            <path
              d="M0,26 C180,8 360,40 540,24 C720,8 900,40 1080,24 C1260,8 1440,40 1440,24 L1440,50 L0,50 Z"
              fill="rgba(14,116,144,0.6)"
            />
          </svg>
        </div>

        {/* Descent header */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="relative z-10 text-center pt-16 pb-8 px-6"
        >
          <h2 className="text-2xl md:text-3xl font-extrabold text-white/90 tracking-tight mb-2">The Descent</h2>
          <p className="text-white/30 max-w-sm mx-auto text-sm">
            Surface jobs match your wants — deeper jobs match your skills.
          </p>
        </motion.div>

        {/* Job sections */}
        <div className="relative z-10 pb-32">
          {allSections.map((section) => {
            if (section.jobs.length === 0) return null;
            return (
              <div key={section.depth}>
                <DepthLabel label={section.label} depth={section.depth} />
                <div className="space-y-6 px-4">
                  {section.jobs.map((job) => {
                    const side = globalIndex % 2 === 0 ? 'left' : 'right';
                    globalIndex++;
                    return (
                      <JobRow key={job.id} job={job} side={side} onSelect={onSelectJob} />
                    );
                  })}
                </div>
              </div>
            );
          })}

          {/* Bottom */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center pt-20 pb-8"
          >
            <p className="text-white/15 text-sm font-medium tracking-widest uppercase">
              You've reached the bottom of the reef
            </p>
            <div className="mt-4 w-8 h-8 mx-auto rounded-full border border-white/10 flex items-center justify-center">
              <div className="w-2 h-2 rounded-full bg-purple-500/30" />
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
