const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'
const STORAGE_KEY = 'reef.userIdentity'

function getStoredIdentity() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function setStoredIdentity(identity) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(identity))
}

export function getOrCreateIdentity() {
  const existing = getStoredIdentity()
  if (existing?.email && existing?.fullName) {
    return existing
  }

  const suffix = crypto.randomUUID().slice(0, 8)
  const identity = {
    email: `reef-${suffix}@example.local`,
    fullName: 'Reef Explorer',
  }
  setStoredIdentity(identity)
  return identity
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  let payload = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok) {
    const message = payload?.message || `Request failed with status ${response.status}`
    const error = new Error(message)
    error.status = response.status
    error.payload = payload
    throw error
  }

  return payload?.data ?? null
}

export function createOnboardingSession(payload) {
  return request('/onboarding/session', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function savePreferences(userId, payload) {
  return request(`/preferences/${userId}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function importLinkedInJobs(payload) {
  return request('/job-aggregation/linkedin/sync', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function fetchRecommendations(userId, limit = 10) {
  const params = new URLSearchParams({ user_id: userId, limit: String(limit) })
  return request(`/jobs/recommendations?${params.toString()}`)
}

export function fetchJobMatch(jobId, userId) {
  const params = new URLSearchParams({ user_id: userId })
  return request(`/jobs/${jobId}/match?${params.toString()}`)
}

export function fetchSkillRadar(userId, targetRole) {
  const params = new URLSearchParams({ user_id: userId, target_role: targetRole })
  return request(`/skills/radar?${params.toString()}`)
}

export function fetchSkillTrends(targetRole, limit = 6) {
  const params = new URLSearchParams({ target_role: targetRole, window_days: '90', limit: String(limit) })
  return request(`/skills/trends?${params.toString()}`)
}
