import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Layers } from 'lucide-react';

export default function SplashScreen({ onComplete }) {
  const [phase, setPhase] = useState(0); // 0=logo, 1=tagline, 2=fade out

  useEffect(() => {
    const t1 = setTimeout(() => setPhase(1), 800);
    const t2 = setTimeout(() => setPhase(2), 2200);
    const t3 = setTimeout(onComplete, 2900);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, [onComplete]);

  return (
    <motion.div
      initial={{ opacity: 1 }}
      animate={{ opacity: phase === 2 ? 0 : 1 }}
      transition={{ duration: 0.7 }}
      className="fixed inset-0 z-50 flex items-center justify-center overflow-hidden"
      style={{
        background: 'linear-gradient(180deg, #0c2a3a 0%, #061620 50%, #020a10 100%)',
      }}
    >
      {/* Animated ripple rings */}
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="absolute rounded-full border border-cyan-400/10"
          initial={{ width: 0, height: 0, opacity: 0.6 }}
          animate={{ width: 600 + i * 200, height: 600 + i * 200, opacity: 0 }}
          transition={{ duration: 3, delay: i * 0.5, repeat: Infinity, ease: 'easeOut' }}
        />
      ))}

      {/* Floating particles */}
      {[...Array(20)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 rounded-full bg-cyan-400/20"
          style={{ left: `${10 + Math.random() * 80}%`, top: `${10 + Math.random() * 80}%` }}
          animate={{ y: [0, -30 - Math.random() * 30, 0], opacity: [0, 0.5, 0] }}
          transition={{ duration: 3 + Math.random() * 3, delay: Math.random() * 2, repeat: Infinity }}
        />
      ))}

      <div className="relative text-center">
        {/* Logo */}
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="mx-auto mb-6 w-20 h-20 rounded-3xl bg-gradient-to-br from-cyan-400 to-teal-600 flex items-center justify-center"
          style={{ boxShadow: '0 0 60px rgba(0,255,213,0.2), 0 0 120px rgba(0,255,213,0.08)' }}
        >
          <Layers className="w-10 h-10 text-white" strokeWidth={2} />
        </motion.div>

        {/* Brand name */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="text-5xl font-extrabold tracking-tight mb-3"
          style={{
            background: 'linear-gradient(135deg, #00ffd5, #22d3ee, #67e8f9)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          Reef
        </motion.h1>

        {/* Tagline */}
        <AnimatePresence>
          {phase >= 1 && (
            <motion.p
              initial={{ opacity: 0, y: 10, filter: 'blur(8px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.5 }}
              className="text-white/40 text-lg font-light tracking-wide"
            >
              Dive deeper. Land better.
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
