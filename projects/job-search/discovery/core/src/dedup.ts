import type { Job } from './schema'

export function dedup(jobs: Job[], seen: Set<string>): Job[] {
  const out: Job[] = []
  const batch = new Set<string>()
  for (const j of jobs) {
    if (seen.has(j.id) || batch.has(j.id)) continue
    batch.add(j.id)
    out.push(j)
  }
  return out
}
