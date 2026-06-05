import { runPipeline } from './pipeline'
import { automatedAdapters } from './adapters/index'
import type { MatchProfile } from './schema'

// Placeholder profile; replaced by aios/profile.ts wiring in Task 14.
const profile: MatchProfile = {
  roleFamilies: ['engineer', 'developer', 'ai engineer', 'platform', 'integration', 'automation'],
  stackKeywords: ['node', 'typescript', 'python', 'react', 'aws', 'gcp', 'llm'],
  localCities: ['melbourne'], remoteOk: true, minSalaryAud: 150000, recencyDays: 21,
  excludeSeniorities: ['junior', 'manager'], exploreShare: 0.2, shortlistSize: 12,
}

const now = new Date().toISOString()
const res = await runPipeline(profile, automatedAdapters(), new Set(), now)
console.log(`\nSkipped: ${res.skipped.map(s => `${s.id}(${s.error})`).join(', ') || 'none'}`)
for (const j of res.shortlist) {
  console.log(`- [${j.score ?? '-'}] ${j.title} @ ${j.company} (${j.source}) ${j.sourceUrl}`)
}
