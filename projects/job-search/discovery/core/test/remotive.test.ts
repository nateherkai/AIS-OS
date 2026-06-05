import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { parseRemotive } from '../src/adapters/remotive'

const payload = JSON.parse(readFileSync(new URL('./fixtures/remotive.json', import.meta.url), 'utf8'))

describe('remotive adapter', () => {
  it('maps jobs from the jobs array', () => {
    const jobs = parseRemotive(payload)
    expect(jobs.length).toBeGreaterThan(0)
    expect(jobs.every(j => j.source === 'remotive' && j.title && j.company && j.url)).toBe(true)
  })
})
