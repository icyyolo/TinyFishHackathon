import { motion } from 'framer-motion'
import { Radar } from 'lucide-react'

export default function SonarScan({ domainLabel, message, progress, error }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{
        background: 'radial-gradient(ellipse at center, #0c2a3a 0%, #061620 40%, #020a10 100%)',
      }}
    >
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage: 'linear-gradient(rgba(0,255,213,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,213,0.3) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />

      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="absolute rounded-full border border-cyan-400/20"
            style={{
              width: `${(i + 1) * 180}px`,
              height: `${(i + 1) * 180}px`,
              animation: `sonar-ping 3s ease-out ${i * 0.6}s infinite`,
            }}
          />
        ))}
      </div>

      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-[500px] h-[500px]" style={{ animation: 'sonar-sweep 3s linear infinite' }}>
          <div className="absolute top-0 left-1/2 w-0.5 h-1/2 origin-bottom" style={{ background: 'linear-gradient(to top, rgba(0,255,213,0.5), transparent)' }} />
          <div className="absolute inset-0 rounded-full" style={{ background: 'conic-gradient(from 0deg, transparent 0deg, rgba(0,255,213,0.08) 30deg, transparent 60deg)' }} />
        </div>
      </div>

      <motion.div
        animate={{
          boxShadow: [
            '0 0 20px rgba(0,255,213,0.3), 0 0 60px rgba(0,255,213,0.15)',
            '0 0 40px rgba(0,255,213,0.5), 0 0 80px rgba(0,255,213,0.25)',
            '0 0 20px rgba(0,255,213,0.3), 0 0 60px rgba(0,255,213,0.15)',
          ],
        }}
        transition={{ duration: 2, repeat: Infinity }}
        className="absolute w-4 h-4 rounded-full bg-[#00ffd5] left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
      />

      <div className="relative z-10 text-center max-w-lg mx-auto px-6">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="mb-10"
        >
          <div className="inline-flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, rgba(0,255,213,0.2), rgba(0,255,213,0.05))', border: '1px solid rgba(0,255,213,0.2)' }}>
              <Radar className="w-5 h-5 text-[#00ffd5]" strokeWidth={2} />
            </div>
            <span className="text-xl font-bold text-[#00ffd5]/80 tracking-tight">Reef</span>
          </div>
        </motion.div>

        <p className="text-xs uppercase tracking-[0.3em] text-white/20 mb-3">
          {domainLabel ? `${domainLabel} mode` : 'Career scan'}
        </p>

        <div className="h-20 flex items-center justify-center mb-8">
          <motion.p
            key={message}
            initial={{ opacity: 0, y: 10, filter: 'blur(4px)' }}
            animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
            transition={{ duration: 0.35 }}
            className="text-lg md:text-xl font-medium tracking-wide text-[#00ffd5]"
          >
            {message}
          </motion.p>
        </div>

        <div className="w-80 mx-auto h-1.5 rounded-full overflow-hidden bg-white/5">
          <motion.div
            className="h-full rounded-full"
            style={{
              background: 'linear-gradient(90deg, #00ffd5, #06b6d4, #00ffd5)',
              backgroundSize: '200% 100%',
              animation: 'shimmer 2s linear infinite',
              width: `${progress}%`,
            }}
          />
        </div>

        <motion.p className="mt-4 text-sm text-white/30 font-mono" animate={{ opacity: [0.3, 0.6, 0.3] }} transition={{ duration: 2, repeat: Infinity }}>
          {progress}% complete
        </motion.p>

        {error && (
          <div className="mt-6 rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            <p className="font-semibold mb-1">Backend connection failed</p>
            <p className="text-rose-100/80">{error}</p>
            <p className="mt-2 text-rose-100/60">Make sure the Flask backend is running on port 5000, then refresh and try again.</p>
          </div>
        )}
      </div>
    </motion.div>
  )
}
