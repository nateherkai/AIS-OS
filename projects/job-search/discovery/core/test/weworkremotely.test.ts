import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { parseWwr } from '../src/adapters/weworkremotely'

const xml = readFileSync(new URL('./fixtures/wwr.xml', import.meta.url), 'utf8')

describe('wwr adapter', () => {
  it('splits "Company: Role" titles', async () => {
    const jobs = await parseWwr(xml)
    expect(jobs.length).toBeGreaterThan(0)
    expect(jobs.every(j => j.source === 'weworkremotely' && j.company && j.title)).toBe(true)
  })
})
