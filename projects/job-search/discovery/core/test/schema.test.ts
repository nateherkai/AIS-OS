import { describe, it, expect } from 'vitest'
import { Job, MatchProfile } from '../src/schema'

describe('schema', () => {
  it('parses a valid Job', () => {
    const j = Job.parse({
      id: 'abc', source: 'remoteok', sourceUrl: 'https://x/y', title: 'Engineer',
      company: 'Acme', location: 'Remote', remote: 'remote',
      employmentType: 'permanent', seniority: 'senior', tags: ['node'],
      descriptionText: 'desc', fetchedAt: '2026-06-05T00:00:00Z',
    })
    expect(j.company).toBe('Acme')
  })
  it('rejects an invalid remote enum', () => {
    expect(() => Job.parse({ remote: 'space' })).toThrow()
  })
  it('parses a MatchProfile', () => {
    const p = MatchProfile.parse({
      roleFamilies: ['engineer'], stackKeywords: ['node'], localCities: ['melbourne'],
      remoteOk: true, minSalaryAud: 150000, recencyDays: 14,
      excludeSeniorities: ['junior', 'manager'], exploreShare: 0.2, shortlistSize: 12,
    })
    expect(p.shortlistSize).toBe(12)
  })
})
