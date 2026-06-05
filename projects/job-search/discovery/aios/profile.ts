import { MatchProfile } from '../core/src/schema'

// Yuan's base taste, from the spec (§8). Edit here to retune hard/soft criteria.
export const yuanProfile: MatchProfile = MatchProfile.parse({
  roleFamilies: ['software engineer', 'engineer', 'developer', 'ai engineer', 'ml engineer',
    'platform', 'integration', 'automation', 'solutions engineer', 'forward deployed', 'customer engineer'],
  stackKeywords: ['node', 'typescript', 'javascript', 'python', 'c#', 'react', 'vue', 'sql',
    'gcp', 'azure', 'aws', 'terraform', 'llm', 'ai'],
  localCities: ['melbourne', 'victoria', 'australia'],
  remoteOk: true, minSalaryAud: 150000, recencyDays: 21,
  excludeSeniorities: ['junior', 'manager'], exploreShare: 0.2, shortlistSize: 12,
})
