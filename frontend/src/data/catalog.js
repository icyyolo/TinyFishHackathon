export const DOMAIN_OPTIONS = [
  { id: 'pm', label: 'Product Management', iconName: 'ClipboardList', targetRole: 'Product Manager' },
  { id: 'ds', label: 'Data Science', iconName: 'BarChart3', targetRole: 'Data Analyst' },
  { id: 'swe', label: 'Software Engineering', iconName: 'Code2', targetRole: 'Backend Engineer' },
  { id: 'ux', label: 'UX Design', iconName: 'Palette', targetRole: 'Product Manager' },
  { id: 'mkt', label: 'Digital Marketing', iconName: 'TrendingUp', targetRole: 'Product Manager' },
  { id: 'consulting', label: 'Consulting', iconName: 'Brain', targetRole: 'Data Analyst' },
]

export const ENVIRONMENT_OPTIONS = [
  { id: 'remote', label: 'Remote', iconName: 'Home', backendValue: 'remote' },
  { id: 'hybrid', label: 'Hybrid', iconName: 'RefreshCw', backendValue: 'hybrid' },
  { id: 'onsite', label: 'On-site', iconName: 'Building2', backendValue: 'onsite' },
]

export const DEFAULT_SKILLS = ['Python', 'SQL', 'Data Visualization']

export const SCAN_MESSAGES = [
  'Deploying AI Agent...',
  'Creating your onboarding session...',
  'Normalizing your preferences...',
  'Scanning normalized job postings...',
  'Calculating job match scores...',
  'Dive ready.',
]

export function getDomainOption(domainId) {
  return DOMAIN_OPTIONS.find((item) => item.id === domainId) || null
}

export function getEnvironmentOption(environmentId) {
  return ENVIRONMENT_OPTIONS.find((item) => item.id === environmentId) || null
}
