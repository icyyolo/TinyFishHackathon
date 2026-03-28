import { useEffect, useMemo, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { DOMAIN_OPTIONS, ENVIRONMENT_OPTIONS, DEFAULT_SKILLS } from '../data/catalog'
import {
  Layers, ClipboardList, BarChart3, Code2, Palette, TrendingUp, Brain,
  Home, RefreshCw, Building2, Check, X, Sparkles, ChevronRight,
  Briefcase, FileText, MessageSquare,
} from 'lucide-react'

const ICON_SETS = {
  domain: { ClipboardList, BarChart3, Code2, Palette, TrendingUp, Brain },
  environment: { Home, RefreshCw, Building2 },
  env: { Home, RefreshCw, Building2 },
}

const FALLBACK_STEPS = [
  { id: 'domain', type: 'select', question: 'What domain are you targeting?', sub: 'Choose the field that excites you most.', iconSet: 'domain', options: DOMAIN_OPTIONS },
  { id: 'environment', type: 'select', question: 'Where do you want to work?', sub: 'Pick your ideal work environment.', iconSet: 'environment', options: ENVIRONMENT_OPTIONS },
  { id: 'job_types', type: 'multi_select', multiple: true, question: 'What job types are you open to?', sub: 'Select one or more preferences.', options: [{ id: 'full_time', label: 'Full-time' }, { id: 'contract', label: 'Contract' }, { id: 'internship', label: 'Internship' }] },
  { id: 'skills', type: 'tags', question: 'What are your key skills?', sub: 'Add the skills you bring to the table.', defaults: DEFAULT_SKILLS },
  { id: 'motivation', type: 'text', question: 'What type of projects do you enjoy the most?', sub: 'This helps personalize recommendation explanations.' },
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
            left: `${p.x}%`, top: `${p.y}%`,
            width: p.size, height: p.size,
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

/* ─── Step indicator with numbered circles and connector lines ─── */
function StepIndicators({ steps, currentStep }) {
  const STEP_ICONS = { domain: Briefcase, environment: Home, job_types: FileText, skills: Code2, motivation: MessageSquare }
  return (
    <div className="flex items-center justify-center gap-0">
      {steps.map((s, i) => {
        const done = i < currentStep
        const active = i === currentStep
        const Icon = STEP_ICONS[s.id]
        return (
          <div key={s.id} className="flex items-center">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className="relative w-8 h-8 rounded-full flex items-center justify-center transition-all duration-400"
                style={{
                  background: done ? 'linear-gradient(135deg, #00ffd5, #22d3ee)' : active ? 'rgba(0,255,213,0.12)' : 'rgba(255,255,255,0.05)',
                  border: active ? '2px solid #00ffd5' : done ? '2px solid transparent' : '2px solid rgba(255,255,255,0.12)',
                  boxShadow: active ? '0 0 16px rgba(0,255,213,0.35)' : 'none',
                }}
              >
                {done ? (
                  <Check className="w-3.5 h-3.5 text-slate-900" strokeWidth={3} />
                ) : Icon ? (
                  <Icon className={`w-3.5 h-3.5 ${active ? 'text-cyan-300' : 'text-white/25'}`} strokeWidth={2} />
                ) : (
                  <span className={`text-xs font-bold ${active ? 'text-cyan-300' : 'text-white/25'}`}>{i + 1}</span>
                )}
              </div>
              <span className={`text-[10px] font-semibold uppercase tracking-widest transition-colors duration-300 whitespace-nowrap ${
                active ? 'text-cyan-300/70' : done ? 'text-white/40' : 'text-white/15'
              }`}>
                {s.id.replace('_', ' ')}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className="w-10 mx-0.5 mb-5 h-px relative overflow-hidden">
                <div className="absolute inset-0 bg-white/8 rounded-full" />
                <motion.div
                  className="absolute inset-y-0 left-0 rounded-full"
                  style={{ background: 'linear-gradient(90deg, #00ffd5, #22d3ee)' }}
                  animate={{ width: i < currentStep ? '100%' : '0%' }}
                  transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

/* ─── Select step (single choice) ─── */
function SelectStep({ stepConfig, value, onChange }) {
  const iconMap = ICON_SETS[stepConfig.iconSet] || {}
  const isSmallSet = (stepConfig.options || []).length <= 3
  return (
    <BubbleCard key={stepConfig.id}>
      <div className={`grid gap-2.5 ${isSmallSet ? 'grid-cols-3' : 'grid-cols-2'}`}>
        {(stepConfig.options || []).map((opt) => {
          const Icon = iconMap[opt.iconName]
          const selected = value === opt.id
          return (
            <motion.button
              key={opt.id}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => onChange(opt.id)}
              className={`relative flex ${isSmallSet ? 'flex-col items-center gap-2 px-4 py-5' : 'items-center gap-2.5 px-4 py-3'} rounded-xl text-left transition-all duration-200 cursor-pointer ${
                selected
                  ? 'bg-cyan-400/15 text-cyan-300 border border-cyan-400/30 shadow-lg shadow-cyan-500/10'
                  : 'bg-white/5 text-white/60 border border-white/8 hover:bg-white/8 hover:border-white/15'
              }`}
            >
              {Icon && <Icon className={isSmallSet ? 'w-6 h-6' : 'w-4 h-4 shrink-0'} strokeWidth={1.8} />}
              <span className="font-medium text-sm">{opt.label}</span>
              {selected && !isSmallSet && (
                <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="absolute right-2 w-4 h-4 rounded-full bg-cyan-400/20 flex items-center justify-center">
                  <Check className="w-2.5 h-2.5 text-cyan-300" strokeWidth={3} />
                </motion.div>
              )}
            </motion.button>
          )
        })}
      </div>
    </BubbleCard>
  )
}

/* ─── Multi-select step (multiple choices) ─── */
function MultiSelectStep({ stepConfig, value, onChange }) {
  const selected = Array.isArray(value) ? value : []
  const toggle = (id) => {
    if (selected.includes(id)) onChange(selected.filter((v) => v !== id))
    else onChange([...selected, id])
  }
  return (
    <BubbleCard key={stepConfig.id}>
      <div className="grid grid-cols-1 gap-2.5">
        {(stepConfig.options || []).map((opt) => {
          const isSelected = selected.includes(opt.id)
          return (
            <motion.button
              key={opt.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => toggle(opt.id)}
              className={`relative flex items-center gap-3 px-4 py-3.5 rounded-xl text-left transition-all duration-200 cursor-pointer ${
                isSelected
                  ? 'bg-cyan-400/15 text-cyan-300 border border-cyan-400/30 shadow-lg shadow-cyan-500/10'
                  : 'bg-white/5 text-white/60 border border-white/8 hover:bg-white/8 hover:border-white/15'
              }`}
            >
              <div className={`w-5 h-5 rounded-md border flex items-center justify-center transition-all ${
                isSelected ? 'bg-cyan-400/25 border-cyan-400/40' : 'border-white/15 bg-white/5'
              }`}>
                {isSelected && <Check className="w-3 h-3 text-cyan-300" strokeWidth={3} />}
              </div>
              <span className="font-medium text-sm">{opt.label}</span>
            </motion.button>
          )
        })}
      </div>
      <p className="mt-2 text-[11px] text-white/20">Select one or more options</p>
    </BubbleCard>
  )
}

/* ─── Tags step ─── */
function TagsStep({ skills, inputValue, inputRef, onSkillsChange, onInputChange, onKeyDown, onAddSkill }) {
  return (
    <BubbleCard key="tags">
      <div className="flex flex-wrap items-center gap-2 min-h-[52px] p-3 rounded-xl bg-white/5 border border-white/10 focus-within:border-cyan-400/30 focus-within:bg-white/8 transition-all cursor-text" onClick={() => inputRef.current?.focus()}>
        <AnimatePresence>
          {skills.map((skill) => (
            <SkillTag key={skill} skill={skill} onRemove={(v) => onSkillsChange(skills.filter((s) => s !== v))} />
          ))}
        </AnimatePresence>
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={skills.length === 0 ? 'Type a skill and press Enter...' : 'Add more...'}
          className="flex-1 min-w-[100px] bg-transparent outline-none text-sm text-white/70 placeholder:text-white/20"
        />
      </div>
      <p className="mt-2 text-[11px] text-white/20">Press Enter to add · Backspace to remove last</p>
    </BubbleCard>
  )
}

/* ─── Text step ─── */
function TextStep({ stepConfig, value, onChange }) {
  return (
    <BubbleCard key={stepConfig.id}>
      <textarea
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Tell us what excites you..."
        rows={4}
        className="w-full rounded-xl bg-white/5 border border-white/10 px-4 py-3 text-sm text-white/70 outline-none transition-colors placeholder:text-white/20 focus:border-cyan-400/30 focus:bg-white/8 resize-none"
      />
      <p className="mt-2 text-[11px] text-white/20">Optional — helps us personalize your results</p>
    </BubbleCard>
  )
}

/* ─── Main Questionnaire ─── */
export default function Questionnaire({ onComplete }) {
  const [steps, setSteps] = useState(null)
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState({})
  const [skills, setSkills] = useState([...DEFAULT_SKILLS])
  const [inputValue, setInputValue] = useState('')
  const inputRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'
    fetch(`${API_BASE}/questionnaire`)
      .then((r) => { if (!r.ok) throw new Error(); return r.json() })
      .then((body) => {
        if (cancelled) return
        const data = body?.data || body
        setSteps(data.steps)
        const tagsStep = data.steps.find((s) => s.type === 'tags')
        if (tagsStep?.defaults) setSkills(tagsStep.defaults)
      })
      .catch(() => { if (!cancelled) setSteps(FALLBACK_STEPS) })
    return () => { cancelled = true }
  }, [])

  if (!steps) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="min-h-screen flex items-center justify-center"
        style={{ background: 'linear-gradient(180deg, #0f3d50 0%, #072535 50%, #021420 100%)' }}>
        <OceanBg />
        <div className="relative z-10 text-center">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-400 to-teal-500 mx-auto mb-4 flex items-center justify-center">
            <Layers className="w-4 h-4 text-white" strokeWidth={2.5} />
          </div>
          <div className="h-5 w-40 mx-auto bg-white/8 rounded-lg animate-pulse" />
        </div>
      </motion.div>
    )
  }

  const currentStep = steps[step]
  const isLast = step === steps.length - 1

  const canNext =
    (currentStep.type === 'select' && answers[currentStep.id]) ||
    (currentStep.type === 'multi_select' && Array.isArray(answers[currentStep.id]) && answers[currentStep.id].length > 0) ||
    (currentStep.type === 'tags' && skills.length > 0) ||
    (currentStep.type === 'text')

  const handleNext = () => {
    if (!isLast) {
      setStep(step + 1)
      return
    }
    onComplete({
      domain: answers.domain || null,
      environment: answers.environment || null,
      job_types: answers.job_types || [],
      skills,
      motivation: answers.motivation || null,
    })
  }

  const setAnswer = (value) => setAnswers({ ...answers, [currentStep.id]: value })

  const addSkill = () => {
    const trimmed = inputValue.trim()
    if (trimmed && !skills.includes(trimmed)) {
      setSkills([...skills, trimmed])
      setInputValue('')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); addSkill() }
    if (e.key === 'Backspace' && inputValue === '' && skills.length > 0) setSkills(skills.slice(0, -1))
  }

  return (
    <motion.div
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen relative flex flex-col"
      style={{ background: 'linear-gradient(180deg, #0f3d50 0%, #0a2e3e 20%, #072535 45%, #041c2a 70%, #021420 100%)' }}
    >
      <OceanBg />

      {/* Top bar */}
      <div className="relative z-10 px-6 pt-6 pb-4">
        <div className="flex items-center justify-between max-w-lg mx-auto">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-400 to-teal-500 flex items-center justify-center">
              <Layers className="w-4 h-4 text-white" strokeWidth={2.5} />
            </div>
            <span className="text-base font-bold text-cyan-300/70 tracking-tight">Reef</span>
          </div>
          <span className="text-xs text-white/25 font-mono">{step + 1} / {steps.length}</span>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col items-center justify-center relative z-10 px-6 pb-36">
        <AnimatePresence mode="wait">
          <motion.div
            key={`header-${step}`}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            transition={{ duration: 0.3 }}
            className="text-center mb-8"
          >
            <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight mb-2">{currentStep.question}</h1>
            <p className="text-white/30 text-sm">{currentStep.sub}</p>
          </motion.div>
        </AnimatePresence>

        <AnimatePresence mode="wait">
          {currentStep.type === 'select' && (
            <SelectStep key={currentStep.id} stepConfig={currentStep} value={answers[currentStep.id]} onChange={setAnswer} />
          )}
          {currentStep.type === 'multi_select' && (
            <MultiSelectStep key={currentStep.id} stepConfig={currentStep} value={answers[currentStep.id]} onChange={setAnswer} />
          )}
          {currentStep.type === 'tags' && (
            <TagsStep
              key="tags"
              skills={skills}
              inputValue={inputValue}
              inputRef={inputRef}
              onSkillsChange={setSkills}
              onInputChange={setInputValue}
              onKeyDown={handleKeyDown}
              onAddSkill={addSkill}
            />
          )}
          {currentStep.type === 'text' && (
            <TextStep key={currentStep.id} stepConfig={currentStep} value={answers[currentStep.id]} onChange={setAnswer} />
          )}
        </AnimatePresence>

        {/* Next / Submit button */}
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
            {isLast ? (
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

      {/* ── Step indicators — fixed at bottom ── */}
      <div className="fixed bottom-0 left-0 right-0 z-20">
        <div className="h-0.5 bg-white/5">
          <motion.div
            className="h-full"
            style={{ background: 'linear-gradient(90deg, #00ffd5, #22d3ee)', boxShadow: '0 0 12px rgba(0,255,213,0.3)' }}
            animate={{ width: `${((step + 1) / steps.length) * 100}%` }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          />
        </div>
        <div className="bg-black/25 backdrop-blur-sm px-6 py-4">
          <StepIndicators steps={steps} currentStep={step} />
        </div>
      </div>
    </motion.div>
  )
}
