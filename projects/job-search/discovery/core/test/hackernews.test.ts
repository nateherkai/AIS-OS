import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { parseHnThread } from '../src/adapters/hackernews'

const thread = JSON.parse(readFileSync(new URL('./fixtures/hn-thread.json', import.meta.url), 'utf8'))

describe('hackernews adapter', () => {
  it('maps top-level comments to raw jobs', () => {
    const jobs = parseHnThread(thread)
    expect(jobs.length).toBeGreaterThan(0)
    expect(jobs.every(j => j.source === 'hackernews' && j.descriptionText.length > 0)).toBe(true)
    // HN postings commonly start "Company | Role | Location | ..."
    expect(jobs.every(j => j.company.length > 0 && j.title.length > 0)).toBe(true)
  })
})
