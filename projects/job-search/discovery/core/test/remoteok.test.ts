import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { parseRemoteOk } from '../src/adapters/remoteok'

const payload = JSON.parse(readFileSync(new URL('./fixtures/remoteok.json', import.meta.url), 'utf8'))

describe('remoteok adapter', () => {
  it('skips the leading legal element and maps jobs', () => {
    const jobs = parseRemoteOk(payload)
    expect(jobs.length).toBeGreaterThan(0)
    expect(jobs.every(j => j.source === 'remoteok')).toBe(true)
    expect(jobs.every(j => j.title && j.company && j.url)).toBe(true)
    expect(jobs.every(j => j.remoteHint === 'remote')).toBe(true)
  })
})
