import { describe, it, expect } from 'vitest'
import { jobKey, jobId } from '../src/hash'

describe('hash', () => {
  it('builds a normalized key from company/title/location', () => {
    expect(jobKey('  Acme  ', 'Senior Engineer', 'Remote'))
      .toBe('acme|senior engineer|remote')
  })
  it('is stable and case-insensitive', () => {
    expect(jobId('Acme', 'Engineer', 'Remote')).toBe(jobId('ACME', 'engineer', 'remote'))
  })
  it('differs when company differs', () => {
    expect(jobId('Acme', 'Engineer', 'Remote')).not.toBe(jobId('Beta', 'Engineer', 'Remote'))
  })
})
