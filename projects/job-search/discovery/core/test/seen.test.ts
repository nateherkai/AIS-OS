import { describe, it, expect } from 'vitest'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { loadSeen, saveSeen } from '../../aios/seen'

describe('seen-store', () => {
  it('round-trips ids and returns an empty set for a missing file', () => {
    const f = join(mkdtempSync(join(tmpdir(), 'seen-')), 'seen.json')
    expect(loadSeen(f).size).toBe(0)
    saveSeen(f, new Set(['a', 'b']))
    expect([...loadSeen(f)].sort()).toEqual(['a', 'b'])
  })
})
