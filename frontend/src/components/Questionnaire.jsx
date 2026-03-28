import { useMemo, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { DOMAIN_OPTIONS, ENVIRONMENT_OPTIONS, DEFAULT_SKILLS } from '../data/catalog'
import {
  Layers, ClipboardList, BarChart3, Code2, Palette, TrendingUp, Brain,
  Home, RefreshCw, Building2, Check, X, Sparkles, ChevronRight, Link2,
} from 'lucide-react'

const DOMAIN_ICONS = { ClipboardList, BarChart3, Code2, Palette, TrendingUp, Brain }
const ENV_ICONS = { Home, RefreshCw, Building2 }

const STEPS = [
  { id: 'domain', question: 'What domain are you targeting?', sub: 'Choose the field that excites you most.' },
  { id: 'env', question: 'Where do you want to work?', sub: 'Pick your ideal work environment.' },
  { id: 'skills', question: 'What are your key skills?', sub: 'Add the skills you bring to the table, and optionally link a LinkedIn jobs search.' },
]

function OceanBg() {
  const particles = useMemo(() =>
    [...Array(30)].map(() => ({
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: 2 + Math.random() * 4,
      dur: 4 + Math.random() * 6,
      delay: Math.random() * 4,
    })),
  [])

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      <div className="absolute top-0 left-1/4 w-px h-[60%] opacity-[0.04]" style={{ background: 'linear-gradient(to bottom, white, transparent)' }} />
      <div className="absolute top-0 left-[45%] w-px h-[50%] opacity-[0.03] rotate-3" style={{ background: 'linear-gradient(to bottom, white, transparent)' }} />
      <div className="absolute top-0 right-1/3 w-px h-[55%] opacity-[0.03] -rotate-2" style={{ background: 'linear-gradient(to bottom, white, transparent)' }} />
      {particles.map((p, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            background: `rgba(0, 255, 213, ${0.05 + Math.random() * 0.1})`,
          }}
          animate={{ y: [0, -20, 0], opacity: [0.1, 0.4, 0.1] }}
          transition={{ duration: p.dur, delay: p.delay, repeat: Infinity }}
        />
      ))}
      <svg className="absolute bottom-0 left-0 w-full h-32 opacity-[0.06]" viewBox="0 0 1440 128" preserveAspectRatio="none">
        <path d="M0,64 C240,100 480,28 720,64 C960,100 1200,28 1440,64 L1440,128 L0,128 Z" fill="white" />
      </svg>
      <svg className="absolute bottom-0 left-0 w-full h-24 opacity-[0.04]" viewBox="0 0 1440 96" preserveAspectRatio="none">
        <path d="M0,48 C360,80 720,16 1080,48 C1260,64 1380,32 1440,40 L1440,96 L0,96 Z" fill="white" />
      </svg>
    </div>
  )
}

function BubbleCard({ children }) {
  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0, y: 40 }}
      animate={{ scale: 1, opacity: 1, y: 0 }}
      exit={{ scale: 0.9, opacity: 0, y: -30 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="w-full max-w-lg mx-auto"
    >
      <div
        className="relative rounded-3xl p-8 backdrop-blur-xl"
        style={{
          background: 'rgba(255,255,255,0.08)',
          border: '1px solid rgba(255,255,255,0.12)',
          boxShadow: '0 20px 60px rgba(0,0,0,0.15), 0 0 40px rgba(0,255,213,0.03), inset 0 1px 0 rgba(255,255,255,0.1)',
        }}
      >
        <div
          className="absolute -bottom-3 left-1/2 -translate-x-1/2 w-6 h-6 rotate-45"
          style={{
            background: 'rgba(255,255,255,0.08)',
            borderRight: '1px solid rgba(255,255,255,0.12)',
            borderBottom: '1px solid rgba(255,255,255,0.12)',
          }}
        />
        {children}
      </div>
    </motion.div>
  )
}

function SkillTag({ skill, onRemove }) {
  return (
    <motion.span
      layout
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      exit={{ scale: 0 }}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-sm font-medium bg-cyan-400/15 text-cyan-300 border border-cyan-400/20"
    >
      {skill}
      <button onClick={() => onRemove(skill)} className="ml-0.5 w-4 h-4 rounded-full flex items-center justify-center hover:bg-cyan-400/20 transition-colors cursor-pointer">
        <X className="w-2.5 h-2.5" strokeWidth={2.5} />
      </button>
    </motion.span>
  )
}

export default function Questionnaire({ onComplete }) {
  const [step, setStep] = useState(0)
  const [selectedDomain, setSelectedDomain] = useState(null)
  const [selectedEnv, setSelectedEnv] = useState(null)
  const [skills, setSkills] = useState([...DEFAULT_SKILLS])
  const [inputValue, setInputValue] = useState('')
  const [linkedinUrl, setLinkedinUrl] = useState('')
  const inputRef = useRef(null)

  const progress = ((step + 1) / STEPS.length) * 100
  const canNext =
    (step === 0 && selectedDomain) ||
    (step === 1 && selectedEnv) ||
    (step === 2 && skills.length > 0)

  const handleNext = () => {
    if (step < 2) {
      setStep(step + 1)
      return
    }
    onComplete({
      domain: selectedDomain,
      environment: selectedEnv,
      skills,
      linkedinUrl: linkedinUrl.trim() || null,
    })
  }

  const addSkill = () => {
    const trimmed = inputValue.trim()
    if (trimmed && !skills.includes(trimmed)) {
      setSkills([...skills, trimmed])
      setInputValue('')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addSkill()
    }
    if (e.key === 'Backspace' && inputValue === '' && skills.length > 0) {
      setSkills(skills.slice(0, -1))
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen relative flex flex-col"
      style={{
        background: 'linear-gradient(180deg, #0f3d50 0%, #0a2e3e 20%, #072535 45%, #041c2a 70%, #021420 100%)',
      }}
    >
      <OceanBg />

      <div className="relative z-10 px-6 pt-6 pb-4">
        <div className="flex items-center justify-between max-w-lg mx-auto">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-400 to-teal-500 flex items-center justify-center">
              <Layers className="w-4 h-4 text-white" strokeWidth={2.5} />
            </div>
            <span className="text-base font-bold text-cyan-300/70 tracking-tight">Reef</span>
          </div>
          <span className="text-xs text-white/25 font-mono">{step + 1} / {STEPS.length}</span>
        </div>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center relative z-10 px-6 pb-32">
        <AnimatePresence mode="wait">
          <motion.div
            key={`header-${step}`}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            transition={{ duration: 0.3 }}
            className="text-center mb-8"
          >
            <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight mb-2">
              {STEPS[step].question}
            </h1>
            <p className="text-white/30 text-sm">{STEPS[step].sub}</p>
          </motion.div>
        </AnimatePresence>

        <AnimatePresence mode="wait">
          {step === 0 && (
            <BubbleCard key="domain">
              <div className="grid grid-cols-2 gap-2.5">
                {DOMAIN_OPTIONS.map((d) => {
                  const Icon = DOMAIN_ICONS[d.iconName]
                  const selected = selectedDomain === d.id
                  return (
                    <motion.button
                      key={d.id}
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.97 }}
                      onClick={() => setSelectedDomain(d.id)}
                      className={`relative flex items-center gap-2.5 px-4 py-3 rounded-xl text-left transition-all duration-200 cursor-pointer ${
                        selected
                          ? 'bg-cyan-400/15 text-cyan-300 border border-cyan-400/30 shadow-lg shadow-cyan-500/10'
                          : 'bg-white/5 text-white/60 border border-white/8 hover:bg-white/8 hover:border-white/15'
                      }`}
                    >
                      <Icon className="w-4 h-4 shrink-0" strokeWidth={1.8} />
                      <span className="font-medium text-sm">{d.label}</span>
                      {selected && (
                        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="absolute right-2 w-4 h-4 rounded-full bg-cyan-400/20 flex items-center justify-center">
                          <Check className="w-2.5 h-2.5 text-cyan-300" strokeWidth={3} />
                        </motion.div>
                      )}
                    </motion.button>
                  )
                })}
              </div>
            </BubbleCard>
          )}

          {step === 1 && (
            <BubbleCard key="env">
              <div className="grid grid-cols-3 gap-3">
                {ENVIRONMENT_OPTIONS.map((e) => {
                  const Icon = ENV_ICONS[e.iconName]
                  const selected = selectedEnv === e.id
                  return (
                    <motion.button
                      key={e.id}
                      whileHover={{ scale: 1.04 }}
                      whileTap={{ scale: 0.96 }}
                      onClick={() => setSelectedEnv(e.id)}
                      className={`flex flex-col items-center gap-2 px-4 py-5 rounded-xl transition-all duration-200 cursor-pointer ${
                        selected
                          ? 'bg-cyan-400/15 text-cyan-300 border border-cyan-400/30 shadow-lg shadow-cyan-500/10'
                          : 'bg-white/5 text-white/60 border border-white/8 hover:bg-white/8 hover:border-white/15'
                      }`}
                    >
                      <Icon className="w-6 h-6" strokeWidth={1.8} />
                      <span className="font-medium text-sm">{e.label}</span>
                    </motion.button>
                  )
                })}
              </div>
            </BubbleCard>
          )}

          {step === 2 && (
            <BubbleCard key="skills">
              <div className="flex flex-wrap items-center gap-2 min-h-[52px] p-3 rounded-xl bg-white/5 border border-white/10 focus-within:border-cyan-400/30 focus-within:bg-white/8 transition-all cursor-text" onClick={() => inputRef.current?.focus()}>
                <AnimatePresence>
                  {skills.map((skill) => (
                    <SkillTag key={skill} skill={skill} onRemove={(value) => setSkills(skills.filter((item) => item !== value))} />
                  ))}
                </AnimatePresence>
                <input
                  ref={inputRef}
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={skills.length === 0 ? 'Type a skill and press Enter...' : 'Add more...'}
                  className="flex-1 min-w-[100px] bg-transparent outline-none text-sm text-white/70 placeholder:text-white/20"
                />
              </div>
              <p className="mt-2 text-[11px] text-white/20">Press Enter to add, Backspace to remove</p>

              <div className="mt-5 rounded-2xl border border-white/10 bg-black/10 p-4">
                <div className="flex items-center gap-2 text-cyan-300/90">
                  <Link2 className="h-4 w-4" strokeWidth={2} />
                  <span className="text-sm font-semibold">Optional LinkedIn jobs link</span>
                </div>
                <p className="mt-2 text-xs text-white/35">
                  Paste a LinkedIn Jobs search URL if you want the backend to ask TinyFish to import fresh postings before ranking.
                </p>
                <input
                  type="url"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  placeholder="https://www.linkedin.com/jobs/search/?keywords=backend%20engineer"
                  className="mt-3 w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/75 outline-none transition-colors placeholder:text-white/20 focus:border-cyan-400/30 focus:bg-white/8"
                />
              </div>
            </BubbleCard>
          )}
        </AnimatePresence>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="mt-8">
          <motion.button
            whileHover={canNext ? { scale: 1.05 } : {}}
            whileTap={canNext ? { scale: 0.96 } : {}}
            onClick={handleNext}
            disabled={!canNext}
            className={`inline-flex items-center gap-2.5 px-8 py-3.5 rounded-2xl text-base font-semibold transition-all duration-300 cursor-pointer relative overflow-hidden ${
              canNext
                ? 'bg-gradient-to-r from-cyan-500 to-teal-500 text-white shadow-xl shadow-cyan-500/25'
                : 'bg-white/5 text-white/20 cursor-not-allowed border border-white/5'
            }`}
          >
            {canNext && (
              <motion.div
                className="absolute inset-0"
                style={{ background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent)', backgroundSize: '200% 100%' }}
                animate={{ backgroundPosition: ['200% 0', '-200% 0'] }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              />
            )}
            {step === 2 ? (
              <>
                <Sparkles className="relative z-10 w-4 h-4" strokeWidth={2} />
                <span className="relative z-10">Scan the Market</span>
              </>
            ) : (
              <>
                <span className="relative z-10">Continue</span>
                <ChevronRight className="relative z-10 w-4 h-4" strokeWidth={2.5} />
              </>
            )}
          </motion.button>
        </motion.div>
      </div>

      <div className="fixed bottom-0 left-0 right-0 z-20">
        <div className="h-1 bg-white/5">
          <motion.div
            className="h-full rounded-r-full"
            style={{
              background: 'linear-gradient(90deg, #00ffd5, #22d3ee)',
              boxShadow: '0 0 12px rgba(0,255,213,0.3)',
            }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          />
        </div>
        <div className="bg-black/20 backdrop-blur-sm px-6 py-3 flex items-center justify-center gap-8">
          {STEPS.map((s, i) => (
            <div key={s.id} className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full transition-all duration-300 ${
                i < step ? 'bg-cyan-400' : i === step ? 'bg-cyan-400 shadow-lg shadow-cyan-400/50' : 'bg-white/10'
              }`} />
              <span className={`text-xs font-medium transition-colors duration-300 ${
                i <= step ? 'text-white/50' : 'text-white/15'
              }`}>
                {s.id === 'domain' ? 'Domain' : s.id === 'env' ? 'Environment' : 'Skills'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}
