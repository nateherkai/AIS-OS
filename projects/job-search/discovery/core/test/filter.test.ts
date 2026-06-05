import { describe, it, expect } from 'vitest'
import { passesHardFilters } from '../src/filter'
import type { Job, MatchProfile } from '../src/schema'

const profile: MatchProfile = {
  roleFamilies: ['engineer', 'developer', 'ai engineer', 'platform'],
  stackKeywords: ['node'], localCities: ['melbourne'], remoteOk: true,
  minSalaryAud: 150000, recencyDays: 21, excludeSeniorities: ['junior', 'manager'],
  exploreShare: 0.2, shortlistSize: 12,
}
const base: Job = {
  id: 'x', source: 's', sourceUrl: 'u', title: 'Senior Software Engineer', company: 'c',
  location: 'Remote', remote: 'remote', employmentType: 'permanent', seniority: 'senior',
  tags: ['node'], descriptionText: '', fetchedAt: 'now',
}

describe('passesHardFilters', () => {
  it('keeps a senior remote engineering role', () => {
    expect(passesHardFilters(base, profile)).toBe(true)
  })
  it('drops a non-engineering role', () => {
    expect(passesHardFilters({ ...base, title: 'Marketing Manager' }, profile)).toBe(false)
  })
  it('drops excluded seniorities', () => {
    expect(passesHardFilters({ ...base, title: 'Junior Engineer', seniority: 'junior' }, profile)).toBe(false)
    expect(passesHardFilters({ ...base, title: 'Engineering Manager', seniority: 'manager' }, profile)).toBe(false)
  })
  it('drops onsite roles outside local cities', () => {
    expect(passesHardFilters({ ...base, remote: 'onsite', location: 'Berlin' }, profile)).toBe(false)
  })
  it('keeps an onsite role in a local city', () => {
    expect(passesHardFilters({ ...base, remote: 'onsite', location: 'Melbourne, AU' }, profile)).toBe(true)
  })
})
