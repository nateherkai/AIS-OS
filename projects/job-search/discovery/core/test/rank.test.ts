import { describe, it, expect } from 'vitest'
import { rank, scoreJob } from '../src/rank'
import type { Job, MatchProfile } from '../src/schema'

const profile: MatchProfile = {
  roleFamilies: ['engineer'], stackKeywords: ['node', 'aws', 'llm'], localCities: ['melbourne'],
  remoteOk: true, minSalaryAud: 150000, recencyDays: 30, excludeSeniorities: ['junior'],
  exploreShare: 0.2, shortlistSize: 12,
}
const now = new Date('2026-06-05T00:00:00Z')
const mk = (over: Partial<Job>): Job => ({
  id: 'x', source: 's', sourceUrl: 'u', title: 'Engineer', company: 'c', location: 'Remote',
  remote: 'remote', employmentType: 'permanent', seniority: 'senior', tags: [],
  descriptionText: '', fetchedAt: now.toISOString(), ...over,
})

describe('rank', () => {
  it('scores higher with more stack overlap', () => {
    const lots = scoreJob(mk({ tags: ['node', 'aws'], descriptionText: 'llm work' }), profile, now)
    const few = scoreJob(mk({ tags: [], descriptionText: 'cobol' }), profile, now)
    expect(lots).toBeGreaterThan(few)
  })
  it('rewards a recent posting over an old one', () => {
    const recent = scoreJob(mk({ postedAt: '2026-06-04T00:00:00Z' }), profile, now)
    const old = scoreJob(mk({ postedAt: '2026-01-01T00:00:00Z' }), profile, now)
    expect(recent).toBeGreaterThan(old)
  })
  it('returns jobs sorted by score desc with score attached', () => {
    const out = rank([mk({ id: 'a', tags: [] }), mk({ id: 'b', tags: ['node', 'aws', 'llm'] })], profile, now)
    expect(out[0].id).toBe('b')
    expect(typeof out[0].score).toBe('number')
  })
})
