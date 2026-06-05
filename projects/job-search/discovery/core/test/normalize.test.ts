import { describe, it, expect } from 'vitest'
import { normalize } from '../src/normalize'
import type { RawJob } from '../src/schema'

const raw: RawJob = {
  source: 'remoteok', title: 'Senior Backend Engineer (Contract)', company: 'Acme',
  location: 'Remote', url: 'https://acme/jobs/1', tags: ['node', 'aws'],
  descriptionText: 'Build things. Remote-first.', remoteHint: 'remote',
  postedAt: '2026-06-01T00:00:00Z',
}

describe('normalize', () => {
  it('maps a RawJob to a Job with a stable id', () => {
    const j = normalize(raw, '2026-06-05T00:00:00Z')
    expect(j.id).toHaveLength(16)
    expect(j.company).toBe('Acme')
    expect(j.sourceUrl).toBe('https://acme/jobs/1')
    expect(j.fetchedAt).toBe('2026-06-05T00:00:00Z')
  })
  it('infers seniority from the title', () => {
    expect(normalize(raw, 'now').seniority).toBe('senior')
    expect(normalize({ ...raw, title: 'Junior Dev' }, 'now').seniority).toBe('junior')
    expect(normalize({ ...raw, title: 'Backend Developer' }, 'now').seniority).toBe('mid')
  })
  it('infers contract employment type', () => {
    expect(normalize(raw, 'now').employmentType).toBe('contract')
    expect(normalize({ ...raw, title: 'Backend Engineer' }, 'now').employmentType).toBe('unknown')
  })
  it('carries the remote hint through', () => {
    expect(normalize(raw, 'now').remote).toBe('remote')
  })
})
