import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'
import { readFileSync } from 'node:fs'
import type { Job } from '../core/src/schema'
import { appendLeads } from './tracker'
import { loadSeen, saveSeen } from './seen'

export function selectByIndices(jobs: Job[], indices: number[]): Job[] {
  return indices.filter(i => i >= 1 && i <= jobs.length).map(i => jobs[i - 1])
}

export function approve(lastRunPath: string, trackerPath: string, seenPath: string, indices: number[]): number {
  const jobs = JSON.parse(readFileSync(lastRunPath, 'utf8')) as Job[]
  const picked = selectByIndices(jobs, indices)
  appendLeads(trackerPath, picked)
  const seen = loadSeen(seenPath)
  for (const j of picked) seen.add(j.id)
  saveSeen(seenPath, seen)
  return picked.length
}

// CLI: tsx ../aios/approve.ts 1 3 5
if (import.meta.url === `file://${process.argv[1]}`) {
  const here = dirname(fileURLToPath(import.meta.url))
  const root = resolve(here, '..')
  const indices = process.argv.slice(2).map(Number).filter(n => !Number.isNaN(n))
  const n = approve(resolve(root, 'queue/last-run.json'), resolve(here, '../../applications.md'),
    resolve(root, 'seen.json'), indices)
  console.log(`Added ${n} lead(s).`)
}
