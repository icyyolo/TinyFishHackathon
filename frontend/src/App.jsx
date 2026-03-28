import { useCallback, useMemo, useState } from 'react'
import { AnimatePresence } from 'framer-motion'
import SplashScreen from './components/SplashScreen'
import Questionnaire from './components/Questionnaire'
import SonarScan from './components/SonarScan'
import Zone3Descent from './components/Zone3Descent'
import JobModal from './components/JobModal'
import {
  createOnboardingSession,
  fetchJobMatch,
  fetchRecommendations,
  fetchSkillRadar,
  fetchSkillTrends,
  getOrCreateIdentity,
  importLinkedInJobs,
  savePreferences,
} from './api'
import { getDomainOption, getEnvironmentOption } from './data/catalog'

function buildSessionPayload(choices) {
  const identity = getOrCreateIdentity()
  const domain = getDomainOption(choices.domain)
  const environment = getEnvironmentOption(choices.environment)
  const targetRole = domain?.targetRole || 'Backend Engineer'
  const location = environment?.backendValue === 'remote' ? 'Remote' : 'Singapore'

  return {
    targetRole,
    sessionPayload: {
      user: {
        email: identity.email,
        full_name: identity.fullName,
      },
      basic_profile: {
        headline: `Aspiring ${targetRole}`,
        location,
        years_of_experience: 0,
        summary: `Interested in ${domain?.label || targetRole} roles with a ${environment?.label || 'flexible'} setup.`,
      },
      education_background: [],
      skills: choices.skills,
      target_roles: [targetRole],
      work_preferences: {
        locations: [location],
        remote_preference: environment?.backendValue || 'hybrid',
        employment_type: 'full-time',
      },
    },
    preferencesPayload: {
      target_roles: [targetRole],
      work_arrangement: [environment?.backendValue || 'hybrid'],
      locations: [location],
      job_type: ['full-time'],
      industries: targetRole === 'Data Analyst' ? ['tech', 'finance'] : ['tech'],
      company_type: ['product'],
    },
  }
}

function normalizeDepth(score) {
  if (score >= 90) return 'shallow'
  if (score >= 82) return 'mid'
  if (score >= 72) return 'deep'
  return 'abyss'
}

function normalizeMatchType(score) {
  if (score >= 90) return 'wants'
  if (score >= 80) return 'balanced'
  return 'skills'
}

function formatLocations(locations) {
  return (locations || []).join(' | ') || 'Unknown'
}

function formatSalary(job) {
  if (job?.salary_text) return job.salary_text
  if (job?.salary_min && job?.salary_max && job?.salary_currency) {
    return `${job.salary_currency} ${Math.round(job.salary_min)} - ${Math.round(job.salary_max)}`
  }
  return 'Salary not listed'
}

function formatPosted(postedAt) {
  if (!postedAt) return 'Recently posted'
  const date = new Date(postedAt)
  if (Number.isNaN(date.getTime())) return 'Recently posted'
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function mapRecommendationToUiJob(item) {
  const score = Math.round(item.match_score || 0)
  return {
    id: item.job_id,
    jobId: item.job_id,
    title: item.title,
    company: item.company_name,
    location: formatLocations(item.locations),
    locations: item.locations || [],
    workArrangement: item.work_arrangement,
    seniorityLevel: item.seniority_level,
    matchRate: score,
    matchType: normalizeMatchType(score),
    depth: normalizeDepth(score),
    description: item.summary,
    requirements: [
      ...(item.matched_preferences || []),
      ...((item.missing_skills || []).map((skill) => `Gap: ${skill.skill}`)),
    ].slice(0, 6),
    matchedSkills: item.matched_skills || [],
    missingSkills: item.missing_skills || [],
    summary: item.summary,
    posted: 'Recommended now',
    salary: 'Salary not listed',
    applyUrl: null,
    factorScores: [],
    lowerScoreReasons: [],
  }
}

function mapMatchDetailToUiJob(previousJob, detail) {
  const job = detail?.job || {}
  const explanation = detail?.explanation || {}
  return {
    ...previousJob,
    id: job.id || previousJob.id,
    jobId: job.id || previousJob.jobId,
    title: job.title || previousJob.title,
    company: job.company_name || previousJob.company,
    location: formatLocations(job.locations || previousJob.locations),
    locations: job.locations || previousJob.locations,
    workArrangement: job.work_arrangement || previousJob.workArrangement,
    seniorityLevel: job.seniority_level || previousJob.seniorityLevel,
    matchRate: Math.round(detail?.match_score || previousJob.matchRate || 0),
    description: explanation.summary || job.description_summary || previousJob.description,
    requirements: [
      ...((explanation.matched_skills || []).map((skill) => `Matched: ${skill.skill}`)),
      ...((explanation.missing_skills || []).map((skill) => `Gap: ${skill.skill}`)),
    ].slice(0, 8),
    matchedSkills: explanation.matched_skills || previousJob.matchedSkills || [],
    missingSkills: explanation.missing_skills || previousJob.missingSkills || [],
    matchedPreferences: explanation.matched_preferences || [],
    lowerScoreReasons: explanation.lower_score_reasons || [],
    factorScores: explanation.factor_scores || [],
    summary: explanation.summary || previousJob.summary,
    posted: formatPosted(job.posted_at),
    salary: formatSalary(job),
    applyUrl: job.apply_url || job.source_url || previousJob.applyUrl,
    sourceUrl: job.source_url || null,
  }
}

export default function App() {
  const [zone, setZone] = useState('splash')
  const [selectedJob, setSelectedJob] = useState(null)
  const [userChoices, setUserChoices] = useState({ domain: null, environment: null, skills: [], linkedinUrl: null })
  const [scanState, setScanState] = useState({ progress: 5, message: 'Deploying AI Agent...', error: null })
  const [integrationData, setIntegrationData] = useState({
    userId: null,
    sessionId: null,
    targetRole: null,
    jobs: [],
    radar: null,
    trends: [],
    linkedinImport: null,
  })

  const handleSplashComplete = useCallback(() => {
    setZone('questionnaire')
  }, [])

  const handleQuestionnaireComplete = useCallback(async (choices) => {
    setUserChoices(choices)
    setZone('scanning')
    setScanState({ progress: 10, message: 'Creating your onboarding session...', error: null })

    try {
      const { targetRole, sessionPayload, preferencesPayload } = buildSessionPayload(choices)
      const session = await createOnboardingSession(sessionPayload)

      setScanState({ progress: 32, message: 'Normalizing your preferences...', error: null })
      await savePreferences(session.user_id, preferencesPayload)

      let linkedinImport = null
      if (choices.linkedinUrl) {
        setScanState({ progress: 48, message: 'Importing LinkedIn jobs via TinyFish...', error: null })
        try {
          linkedinImport = await importLinkedInJobs({
            linkedin_url: choices.linkedinUrl,
            target_role: targetRole,
            max_jobs: 12,
          })
        } catch (error) {
          linkedinImport = {
            status: 'failed',
            message: error.message || 'Unable to import LinkedIn jobs right now.',
          }
        }
      }

      setScanState({
        progress: 62,
        message: linkedinImport?.status === 'completed'
          ? 'Ranking fresh LinkedIn and existing jobs...'
          : 'Scanning normalized job postings...',
        error: null,
      })
      const recommendations = await fetchRecommendations(session.user_id, 10)

      setScanState({ progress: 82, message: 'Calculating job match scores...', error: null })
      const [radarResult, trendsResult] = await Promise.allSettled([
        fetchSkillRadar(session.user_id, targetRole),
        fetchSkillTrends(targetRole, 6),
      ])

      setIntegrationData({
        userId: session.user_id,
        sessionId: session.id,
        targetRole,
        jobs: (recommendations?.jobs || []).map(mapRecommendationToUiJob),
        radar: radarResult.status === 'fulfilled' ? radarResult.value : null,
        trends: trendsResult.status === 'fulfilled' ? trendsResult.value?.skills || [] : [],
        linkedinImport,
      })

      setScanState({ progress: 100, message: 'Dive ready.', error: null })
      setZone('descent')
    } catch (error) {
      setScanState({
        progress: 100,
        message: 'Integration failed.',
        error: error.message || 'Unable to connect the frontend to the backend.',
      })
    }
  }, [])

  const handleSelectJob = useCallback(async (job) => {
    setSelectedJob({ ...job, isLoading: true })
    try {
      if (!integrationData.userId) {
        setSelectedJob({ ...job, isLoading: false })
        return
      }
      const detail = await fetchJobMatch(job.jobId, integrationData.userId)
      setSelectedJob(mapMatchDetailToUiJob(job, detail))
    } catch (error) {
      setSelectedJob({
        ...job,
        isLoading: false,
        error: error.message || 'Unable to load the detailed match explanation.',
      })
    }
  }, [integrationData.userId])

  const handleCloseModal = useCallback(() => {
    setSelectedJob(null)
  }, [])

  const selectedDomain = useMemo(() => getDomainOption(userChoices.domain), [userChoices.domain])

  return (
    <div className="relative">
      <AnimatePresence mode="wait">
        {zone === 'splash' && (
          <SplashScreen key="splash" onComplete={handleSplashComplete} />
        )}
        {zone === 'questionnaire' && (
          <Questionnaire key="questionnaire" onComplete={handleQuestionnaireComplete} />
        )}
        {zone === 'scanning' && (
          <SonarScan
            key="scanning"
            domainLabel={selectedDomain?.label}
            message={scanState.message}
            progress={scanState.progress}
            error={scanState.error}
          />
        )}
        {zone === 'descent' && (
          <Zone3Descent
            key="descent"
            jobs={integrationData.jobs}
            radar={integrationData.radar}
            trends={integrationData.trends}
            targetRole={integrationData.targetRole}
            onSelectJob={handleSelectJob}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {selectedJob && (
          <JobModal key="modal" job={selectedJob} onClose={handleCloseModal} />
        )}
      </AnimatePresence>
    </div>
  )
}
