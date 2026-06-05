import { describe, it, expect } from 'vitest'
import { runPipeline } from '../src/pipeline'
import type { Adapter } from '../src/adapters/types'
import type { MatchProfile } from '../src/schema'

const profile: MatchProfile = {
  roleFamilies: ['engineer', 'developer'], stackKeywords: ['node'], localCities: ['melbourne'],
  remoteOk: true, minSalaryAud: 150000, recencyDays: 3650,
  excludeSeniorities: ['junior', 'manager'], exploreShare: 0, shortlistSize: 10,
}

const fakeAdapter = (id: string): Adapter => ({
  id, kind: 'automated',
  async fetch() {
    return [{ source: id, title: 'Senior Engineer', company: `Co-${id}`, location: 'Remote',
      url: `https://x/${id}`, tags: ['node'], descriptionText: 'node', remoteHint: 'remote' }]
  },
})

describe('runPipeline', () => {
  it('returns a shortlist and reports no skips on success', async () => {
    const res = await runPipeline(profile, [fakeAdapter('a'), fakeAdapter('b')], new Set(),
      '2026-06-05T00:00:00Z')
    expect(res.shortlist.length).toBe(2)
    expect(res.skipped).toEqual([])
  })
  it('isolates a failing adapter and records it as skipped', async () => {
    const boom: Adapter = { id: 'boom', kind: 'automated', async fetch() { throw new Error('429') } }
    const res = await runPipeline(profile, [fakeAdapter('a'), boom], new Set(), 'now')
    expect(res.shortlist.length).toBe(1)
    expect(res.skipped).toEqual([{ id: 'boom', error: '429' }])
  })
})
