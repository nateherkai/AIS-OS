import { describe, it, expect } from 'vitest'
import { writeFileSync, mkdtempSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { approve, selectByIndices } from '../../aios/approve'
import type { Job } from '../src/schema'

const mk = (id: string, company: string): Job => ({
  id, source: 's', sourceUrl: 'https://u/' + id, title: 'Engineer', company, location: 'Remote',
  remote: 'remote', employmentType: 'permanent', seniority: 'senior', tags: [],
  descriptionText: '', fetchedAt: 'now', score: 80,
})

describe('approve', () => {
  it('selectByIndices is 1-based and bounds-checked', () => {
    expect(selectByIndices([mk('a', 'A'), mk('b', 'B')], [1, 3]).map(j => j.id)).toEqual(['a'])
  })
  it('appends picked jobs and marks them seen', () => {
    const dir = mkdtempSync(join(tmpdir(), 'apr-'))
    const last = join(dir, 'last-run.json'); writeFileSync(last, JSON.stringify([mk('a', 'A'), mk('b', 'B')]))
    const tracker = join(dir, 'applications.md')
    writeFileSync(tracker, '| # | Company | Role | Source | Link | Status | a | b | c | d | e |\n|---|---|---|---|---|---|---|---|---|---|---|\n')
    const seen = join(dir, 'seen.json')
    expect(approve(last, tracker, seen, [2])).toBe(1)
    expect(readFileSync(tracker, 'utf8')).toContain('| B |')
    expect(JSON.parse(readFileSync(seen, 'utf8'))).toEqual(['b'])
  })
})
