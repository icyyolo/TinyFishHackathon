import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { DEFAULT_SKILLS } from '../data/mockData';
import { Layers, X, Sparkles, ArrowDown } from 'lucide-react';

function SkillTag({ skill, onRemove }) {
  return (
    <motion.span
      layout
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0, opacity: 0 }}
      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-sm font-medium bg-gradient-to-r from-cyan-500/15 to-teal-500/15 text-cyan-700 border border-cyan-200/60"
    >
      {skill}
      <button
        onClick={() => onRemove(skill)}
        className="ml-0.5 w-4 h-4 rounded-full flex items-center justify-center hover:bg-cyan-500/20 transition-colors cursor-pointer"
      >
        <X className="w-2.5 h-2.5" strokeWidth={2.5} />
      </button>
    </motion.span>
  );
}

export default function Zone2Skills({ onSubmit }) {
  const [skills, setSkills] = useState([...DEFAULT_SKILLS]);
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef(null);

  const addSkill = () => {
    const trimmed = inputValue.trim();
    if (trimmed && !skills.includes(trimmed)) {
      setSkills([...skills, trimmed]);
      setInputValue('');
    }
  };

  const removeSkill = (skill) => {
    setSkills(skills.filter((s) => s !== skill));
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); addSkill(); }
    if (e.key === 'Backspace' && inputValue === '' && skills.length > 0) {
      setSkills(skills.slice(0, -1));
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.6 }}
      className="min-h-screen relative overflow-hidden flex items-center justify-center"
      style={{
        background: 'linear-gradient(180deg, #ecfeff 0%, #cffafe 30%, #a5f3fc 60%, #67e8f9 100%)',
      }}
    >
      {/* Sunlight */}
      <div
        className="absolute -top-20 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full opacity-30 pointer-events-none"
        style={{ background: 'radial-gradient(circle, rgba(255,255,255,0.8) 0%, transparent 70%)' }}
      />

      <div className="relative z-10 w-full max-w-xl mx-auto px-6 py-16">
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
          <h1 className="text-3xl md:text-4xl font-extrabold text-slate-800 tracking-tight mb-3">
            Your Skills
          </h1>
          <p className="text-slate-500 max-w-md mx-auto leading-relaxed">
            Add your skills so our AI can calibrate the perfect depth for your job matches.
          </p>
        </motion.div>

        {/* Skill Input */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="glass-light rounded-2xl p-6 mb-10"
        >
          <div
            className="flex flex-wrap items-center gap-2 min-h-[52px] p-3 rounded-xl bg-white/70 border border-cyan-100 focus-within:border-cyan-300 focus-within:ring-2 focus-within:ring-cyan-200/50 transition-all cursor-text"
            onClick={() => inputRef.current?.focus()}
          >
            <AnimatePresence>
              {skills.map((skill) => (
                <SkillTag key={skill} skill={skill} onRemove={removeSkill} />
              ))}
            </AnimatePresence>
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={skills.length === 0 ? 'Type a skill and press Enter...' : 'Add more...'}
              className="flex-1 min-w-[120px] bg-transparent outline-none text-sm text-slate-700 placeholder:text-slate-300"
            />
          </div>
          <p className="mt-2.5 text-xs text-slate-400">Press Enter to add, Backspace to remove</p>
        </motion.div>

        {/* CTA */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="text-center"
        >
          <motion.button
            whileHover={{ scale: 1.04, y: -2 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => onSubmit(skills)}
            disabled={skills.length === 0}
            className={`inline-flex items-center gap-3 px-10 py-4 rounded-2xl text-lg font-semibold transition-all duration-300 cursor-pointer relative overflow-hidden ${
              skills.length > 0
                ? 'bg-gradient-to-r from-cyan-600 via-teal-600 to-emerald-600 text-white shadow-xl shadow-cyan-600/30 hover:shadow-2xl hover:shadow-cyan-600/40'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed'
            }`}
          >
            {skills.length > 0 && (
              <motion.div
                className="absolute inset-0"
                style={{
                  background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
                  backgroundSize: '200% 100%',
                }}
                animate={{ backgroundPosition: ['200% 0', '-200% 0'] }}
                transition={{ duration: 2.5, repeat: Infinity, ease: 'linear' }}
              />
            )}
            <Sparkles className="relative z-10 w-5 h-5" strokeWidth={2} />
            <span className="relative z-10">Scan the Market</span>
            <ArrowDown className="relative z-10 w-5 h-5" strokeWidth={2.5} />
          </motion.button>
        </motion.div>
      </div>
    </motion.div>
  );
}
