import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { DOMAINS, ENVIRONMENTS } from '../data/mockData';
import {
  Layers, ClipboardList, BarChart3, Code2, Palette, TrendingUp, Brain,
  Home, RefreshCw, Building2, Check, ArrowRight,
} from 'lucide-react';

const DOMAIN_ICONS = { ClipboardList, BarChart3, Code2, Palette, TrendingUp, Brain };
const ENV_ICONS = { Home, RefreshCw, Building2 };

export default function Zone1Wants({ onSubmit }) {
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [selectedEnv, setSelectedEnv] = useState(null);

  const canSubmit = selectedDomain && selectedEnv;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, y: -40 }}
      transition={{ duration: 0.6 }}
      className="min-h-screen relative overflow-hidden flex items-center justify-center"
      style={{
        background: 'linear-gradient(180deg, #ecfeff 0%, #cffafe 30%, #a5f3fc 60%, #67e8f9 100%)',
      }}
    >
      {/* Sunlight rays */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div
          className="absolute -top-32 left-1/2 -translate-x-1/2 w-[800px] h-[800px] rounded-full opacity-40"
          style={{
            background: 'radial-gradient(circle, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0) 70%)',
          }}
        />
        {[...Array(12)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-2 h-2 rounded-full bg-white/40"
            style={{
              left: `${10 + Math.random() * 80}%`,
              top: `${10 + Math.random() * 80}%`,
            }}
            animate={{ y: [0, -20, 0], opacity: [0.2, 0.6, 0.2] }}
            transition={{ duration: 3 + Math.random() * 3, repeat: Infinity, delay: Math.random() * 2 }}
          />
        ))}
      </div>

      <div className="relative z-10 w-full max-w-2xl mx-auto px-6 py-16">
        {/* Brand */}
        <motion.div
          initial={{ y: -30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-500 to-teal-600 flex items-center justify-center shadow-lg shadow-cyan-500/25">
              <Layers className="w-6 h-6 text-white" strokeWidth={2.5} />
            </div>
            <span className="text-3xl font-bold bg-gradient-to-r from-cyan-700 to-teal-700 bg-clip-text text-transparent tracking-tight">
              Reef
            </span>
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold text-slate-800 tracking-tight leading-tight mb-4">
            Discover where you{' '}
            <span className="bg-gradient-to-r from-cyan-600 to-teal-500 bg-clip-text text-transparent">
              truly fit
            </span>
          </h1>
          <p className="text-lg text-slate-500 max-w-md mx-auto leading-relaxed">
            AI-powered job discovery calibrated for fresh graduates. No more "entry-level" requiring 5 years experience.
          </p>
        </motion.div>

        {/* Domain Selection */}
        <motion.div
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="glass-light rounded-3xl p-8 mb-6"
        >
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-4">
            Target Domain
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {DOMAINS.map((d) => {
              const Icon = DOMAIN_ICONS[d.iconName];
              return (
                <motion.button
                  key={d.id}
                  whileHover={{ scale: 1.03, y: -2 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => setSelectedDomain(d.id)}
                  className={`relative flex items-center gap-3 px-4 py-3.5 rounded-2xl text-left transition-all duration-300 cursor-pointer ${
                    selectedDomain === d.id
                      ? 'bg-gradient-to-r from-cyan-500 to-teal-500 text-white shadow-lg shadow-cyan-500/25'
                      : 'bg-white/60 hover:bg-white/80 text-slate-700 border border-white/50 hover:border-cyan-200 hover:shadow-md'
                  }`}
                >
                  <Icon className="w-5 h-5 shrink-0" strokeWidth={1.8} />
                  <span className="font-medium text-sm">{d.label}</span>
                  <AnimatePresence>
                    {selectedDomain === d.id && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        exit={{ scale: 0 }}
                        className="absolute right-3 w-5 h-5 rounded-full bg-white/30 flex items-center justify-center"
                      >
                        <Check className="w-3 h-3" strokeWidth={3} />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.button>
              );
            })}
          </div>
        </motion.div>

        {/* Environment Selection */}
        <motion.div
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.45 }}
          className="glass-light rounded-3xl p-8 mb-10"
        >
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-4">
            Working Environment
          </h2>
          <div className="grid grid-cols-3 gap-3">
            {ENVIRONMENTS.map((e) => {
              const Icon = ENV_ICONS[e.iconName];
              return (
                <motion.button
                  key={e.id}
                  whileHover={{ scale: 1.03, y: -2 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => setSelectedEnv(e.id)}
                  className={`flex flex-col items-center gap-2 px-4 py-5 rounded-2xl transition-all duration-300 cursor-pointer ${
                    selectedEnv === e.id
                      ? 'bg-gradient-to-r from-cyan-500 to-teal-500 text-white shadow-lg shadow-cyan-500/25'
                      : 'bg-white/60 hover:bg-white/80 text-slate-700 border border-white/50 hover:border-cyan-200 hover:shadow-md'
                  }`}
                >
                  <Icon className="w-6 h-6" strokeWidth={1.8} />
                  <span className="font-medium text-sm">{e.label}</span>
                </motion.button>
              );
            })}
          </div>
        </motion.div>

        {/* CTA */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="text-center"
        >
          <motion.button
            whileHover={canSubmit ? { scale: 1.04, y: -2 } : {}}
            whileTap={canSubmit ? { scale: 0.97 } : {}}
            onClick={() => canSubmit && onSubmit({ domain: selectedDomain, environment: selectedEnv })}
            disabled={!canSubmit}
            className={`relative inline-flex items-center gap-3 px-10 py-4.5 rounded-2xl text-lg font-semibold transition-all duration-500 cursor-pointer ${
              canSubmit
                ? 'bg-gradient-to-r from-cyan-500 via-teal-500 to-emerald-500 text-white shadow-xl shadow-cyan-500/30 hover:shadow-2xl hover:shadow-cyan-500/40'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed'
            }`}
          >
            {canSubmit && (
              <motion.div
                className="absolute inset-0 rounded-2xl opacity-50"
                style={{
                  background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
                  backgroundSize: '200% 100%',
                }}
                animate={{ backgroundPosition: ['200% 0', '-200% 0'] }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              />
            )}
            <span className="relative z-10">Next</span>
            <ArrowRight className="relative z-10 w-5 h-5" strokeWidth={2.5} />
          </motion.button>
          {!canSubmit && (
            <p className="mt-3 text-sm text-slate-400">Select a domain and environment to continue</p>
          )}
        </motion.div>
      </div>

      {/* Bottom wave */}
      <div className="absolute bottom-0 left-0 right-0 h-20 pointer-events-none">
        <svg viewBox="0 0 1440 100" className="w-full h-full" preserveAspectRatio="none">
          <path d="M0,40 C360,100 720,0 1080,60 C1260,80 1380,40 1440,50 L1440,100 L0,100 Z" fill="rgba(6,182,212,0.15)" />
          <path d="M0,60 C360,20 720,80 1080,30 C1260,15 1380,50 1440,40 L1440,100 L0,100 Z" fill="rgba(6,182,212,0.08)" />
        </svg>
      </div>
    </motion.div>
  );
}
