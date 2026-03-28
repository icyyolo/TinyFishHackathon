import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, MapPin, Clock, ExternalLink } from 'lucide-react';

function CircularProgress({ value, size = 100, strokeWidth = 6 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;
  const color = value >= 90 ? '#00ffd5' : value >= 80 ? '#22d3ee' : value >= 70 ? '#818cf8' : '#a855f7';

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={strokeWidth} />
        <motion.circle
          cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
          style={{ filter: `drop-shadow(0 0 8px ${color}60)` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="text-2xl font-bold text-white"
        >
          {value}%
        </motion.span>
        <span className="text-[10px] text-white/30 uppercase tracking-widest mt-0.5">match</span>
      </div>
    </div>
  );
}

export default function JobModal({ job, onClose }) {
  useEffect(() => {
    const handleEsc = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handleEsc);
    document.body.style.overflow = 'hidden';
    return () => { document.removeEventListener('keydown', handleEsc); document.body.style.overflow = ''; };
  }, [onClose]);

  if (!job) return null;

  const accent = job.matchRate >= 90 ? '#00ffd5' : job.matchRate >= 80 ? '#22d3ee' : job.matchRate >= 70 ? '#818cf8' : '#a855f7';

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 30 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          onClick={(e) => e.stopPropagation()}
          className="relative w-full max-w-lg max-h-[85vh] overflow-y-auto rounded-3xl"
          style={{
            background: 'linear-gradient(180deg, rgba(8,25,40,0.95) 0%, rgba(3,12,20,0.98) 100%)',
            border: `1px solid ${accent}20`,
            boxShadow: `0 0 60px ${accent}10, 0 25px 50px rgba(0,0,0,0.5)`,
          }}
        >
          <button
            onClick={onClose}
            className="absolute top-4 right-4 w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center transition-colors z-10 cursor-pointer"
          >
            <X className="w-4 h-4 text-white/40" strokeWidth={1.5} />
          </button>

          <div className="absolute top-0 left-0 right-0 h-32 rounded-t-3xl pointer-events-none"
            style={{ background: `radial-gradient(ellipse at top, ${accent}12, transparent 70%)` }}
          />

          <div className="relative p-8">
            <div className="flex items-start gap-6 mb-8">
              <CircularProgress value={job.matchRate} />
              <div className="flex-1 pt-1">
                <h2 className="text-2xl font-bold text-white leading-tight mb-1.5">{job.title}</h2>
                <p className="text-base text-white/50 font-medium mb-2">{job.company}</p>
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="inline-flex items-center gap-1.5 text-xs text-white/30 font-medium">
                    <MapPin className="w-3 h-3" strokeWidth={2} />
                    {job.location}
                  </span>
                  <span className="inline-flex items-center gap-1.5 text-xs text-white/30 font-medium">
                    <Clock className="w-3 h-3" strokeWidth={2} />
                    {job.posted}
                  </span>
                </div>
              </div>
            </div>

            <div className="mb-6">
              <h3 className="text-sm font-semibold text-white/50 uppercase tracking-widest mb-3">About the Role</h3>
              <p className="text-sm text-white/40 leading-relaxed">{job.description}</p>
            </div>

            <div className="mb-8">
              <h3 className="text-sm font-semibold text-white/50 uppercase tracking-widest mb-3">Requirements</h3>
              <div className="flex flex-wrap gap-2">
                {job.requirements.map((req, i) => (
                  <span key={i} className="px-3 py-1.5 rounded-xl text-xs font-medium"
                    style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.5)' }}>
                    {req}
                  </span>
                ))}
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full py-4 rounded-2xl text-base font-semibold text-white relative overflow-hidden cursor-pointer flex items-center justify-center gap-2"
              style={{ background: `linear-gradient(135deg, ${accent}, ${accent}aa)`, boxShadow: `0 8px 32px ${accent}30` }}
            >
              <motion.div
                className="absolute inset-0"
                style={{ background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent)', backgroundSize: '200% 100%' }}
                animate={{ backgroundPosition: ['200% 0', '-200% 0'] }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              />
              <ExternalLink className="relative z-10 w-4 h-4" strokeWidth={2} />
              <span className="relative z-10">Apply Now</span>
            </motion.button>

            <p className="text-center text-[11px] text-white/15 mt-4">
              Match rate calculated by Reef AI based on your profile, skills, and preferences
            </p>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
