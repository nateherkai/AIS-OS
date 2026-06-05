import type { Job } from './schema'
export function dedup(jobs: Job[], _seen: Set<string>): Job[] { return jobs }
