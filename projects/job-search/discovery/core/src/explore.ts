import type { Job, MatchProfile } from './schema'
export function buildShortlist(jobs: Job[], p: MatchProfile): Job[] { return jobs.slice(0, p.shortlistSize) }
