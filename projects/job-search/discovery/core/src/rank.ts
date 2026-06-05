import type { Job, MatchProfile } from './schema'

const W = { stack: 50, startup: 10, salary: 15, recency: 25 }   // sums to 100

export function scoreJob(job: Job, profile: MatchProfile, now: Date): number {
  const hay = `${job.title} ${job.tags.join(' ')} ${job.descriptionText}`.toLowerCase()

  const hits = profile.stackKeywords.filter(k => hay.includes(k.toLowerCase())).length
  const stack = profile.stackKeywords.length
    ? (hits / profile.stackKeywords.length) * W.stack : 0

  const startup = /\b(startup|seed|series a|early stage|founding)\b/.test(hay) ? W.startup : 0

  let salary = 0
  if (job.salary?.min && job.salary.min >= profile.minSalaryAud) salary = W.salary

  let recency = 0
  if (job.postedAt) {
    const ageDays = (now.getTime() - new Date(job.postedAt).getTime()) / 86_400_000
    recency = Math.max(0, 1 - ageDays / profile.recencyDays) * W.recency
  }

  return Math.round(Math.min(100, stack + startup + salary + recency))
}

export function rank(jobs: Job[], profile: MatchProfile, now: Date = new Date()): Job[] {
  return jobs
    .map(j => ({ ...j, score: scoreJob(j, profile, now) }))
    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
}
