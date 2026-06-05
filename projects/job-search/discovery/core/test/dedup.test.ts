import { describe, it, expect } from 'vitest'
import { dedup } from '../src/dedup'
import type { Job } from '../src/schema'

const mk = (id: string): Job => ({
  id, source: 's', sourceUrl: 'u', title: 't', company: 'c', location: 'l',
  remote: 'remote', employmentType: 'unknown', seniority: 'mid', tags: [],
  descriptionText: '', fetchedAt: 'now',
})

describe('dedup', () => {
  it('removes ids already in the seen set', () => {
    const out = dedup([mk('a'), mk('b')], new Set(['a']))
    expect(out.map(j => j.id)).toEqual(['b'])
  })
  it('removes in-batch duplicate ids, keeping first', () => {
    const out = dedup([mk('a'), mk('a'), mk('b')], new Set())
    expect(out.map(j => j.id)).toEqual(['a', 'b'])
  })
})
