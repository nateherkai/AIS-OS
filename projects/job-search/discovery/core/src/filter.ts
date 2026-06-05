import type { Job, MatchProfile } from './schema'

function matchesRoleFamily(job: Job, profile: MatchProfile): boolean {
  const hay = `${job.title} ${job.tags.join(' ')}`.toLowerCase()
  return profile.roleFamilies.some(rf => hay.includes(rf.toLowerCase()))
}

function locationOk(job: Job, profile: MatchProfile): boolean {
  if (job.remote === 'remote' || job.remote === 'hybrid') return true
  if (job.remote === 'unknown' && profile.remoteOk) return true
  const loc = job.location.toLowerCase()
  return profile.localCities.some(c => loc.includes(c.toLowerCase()))
}

export function passesHardFilters(job: Job, profile: MatchProfile): boolean {
  if (!matchesRoleFamily(job, profile)) return false
  if (profile.excludeSeniorities.includes(job.seniority)) return false
  if (!locationOk(job, profile)) return false
  return true
}
