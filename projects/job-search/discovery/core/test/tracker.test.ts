import { describe, it, expect } from 'vitest'
import { writeFileSync, mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { readLeadKeys, appendLeads } from '../../aios/tracker'
import type { Job } from '../src/schema'

const sample = `# Applications Tracker

| # | Company | Role | Source | Link | Status | CV variant | Cover letter | Applied | Next action | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Acme | Senior Engineer | remoteok | https://x | Lead |  |  |  |  |  |
`

const mkJob = (over: Partial<Job>): Job => ({
  id: 'x', source: 'remotive', sourceUrl: 'https://y', title: 'Platform Engineer',
  company: 'Beta', location: 'Remote', remote: 'remote', employmentType: 'permanent',
  seniority: 'senior', tags: [], descriptionText: '', fetchedAt: 'now', score: 88, ...over,
})

describe('tracker', () => {
  it('reads existing lead keys (company|title, lowercased)', () => {
    const f = join(mkdtempSync(join(tmpdir(), 'trk-')), 'applications.md')
    writeFileSync(f, sample)
    expect(readLeadKeys(f).has('acme|senior engineer')).toBe(true)
  })
  it('appends a job as a Lead row and is idempotent on re-read', () => {
    const f = join(mkdtempSync(join(tmpdir(), 'trk-')), 'applications.md')
    writeFileSync(f, sample)
    appendLeads(f, [mkJob({})])
    const keys = readLeadKeys(f)
    expect(keys.has('beta|platform engineer')).toBe(true)
    expect(keys.has('acme|senior engineer')).toBe(true)
  })
})
