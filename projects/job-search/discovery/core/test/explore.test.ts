import { describe, it, expect } from 'vitest'
import { buildShortlist } from '../src/explore'
import type { Job, MatchProfile } from '../src/schema'

const profile: MatchProfile = {
  roleFamilies: [], stackKeywords: [], localCities: [], remoteOk: true, minSalaryAud: 0,
  recencyDays: 30, excludeSeniorities: [], exploreShare: 0.25, shortlistSize: 4,
}
const mk = (id: string, source: string, score: number): Job => ({
  id, source, sourceUrl: 'u', title: 't', company: id, location: 'l', remote: 'remote',
  employmentType: 'unknown', seniority: 'mid', tags: [], descriptionText: '', fetchedAt: 'now', score,
})

describe('buildShortlist', () => {
  it('fills shortlistSize and reserves explore slots for novel sources', () => {
    const jobs = [
      mk('a1', 'A', 90), mk('a2', 'A', 85), mk('a3', 'A', 80), mk('a4', 'A', 70),
      mk('b1', 'B', 40),
    ]
    const out = buildShortlist(jobs, profile)
    expect(out.length).toBe(4)
    expect(out.some(j => j.source === 'B')).toBe(true)
  })
  it('never returns more than shortlistSize', () => {
    const jobs = Array.from({ length: 10 }, (_, i) => mk(`x${i}`, 'A', 100 - i))
    expect(buildShortlist(jobs, profile).length).toBe(4)
  })
  it('handles fewer jobs than shortlistSize', () => {
    expect(buildShortlist([mk('a', 'A', 10)], profile).length).toBe(1)
  })
})
