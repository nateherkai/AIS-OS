import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'
import { mkdirSync, writeFileSync } from 'node:fs'
import { runPipeline } from '../core/src/pipeline'
import { automatedAdapters } from '../core/src/adapters/index'
import { leadKey, readLeadKeys } from './tracker'
import { loadSeen } from './seen'
import { yuanProfile } from './profile'

const here = dirname(fileURLToPath(import.meta.url))
const root = resolve(here, '..')                          // projects/job-search/discovery
const seenPath = resolve(root, 'seen.json')
const trackerPath = resolve(here, '../../applications.md') // projects/job-search/applications.md
const queueDir = resolve(root, 'queue')

const res = await runPipeline(yuanProfile, automatedAdapters(), loadSeen(seenPath), new Date().toISOString())
const trackerKeys = readLeadKeys(trackerPath)
const fresh = res.shortlist.filter(j => !trackerKeys.has(leadKey(j.company, j.title)))

mkdirSync(queueDir, { recursive: true })
writeFileSync(resolve(queueDir, 'last-run.json'), JSON.stringify(fresh, null, 2))

console.log(`\n# Job shortlist (${fresh.length})  Skipped: ${res.skipped.map(s => s.id).join(', ') || 'none'}\n`)
fresh.forEach((j, i) => {
  console.log(`${i + 1}. [${j.score}] ${j.title} @ ${j.company} — ${j.remote}/${j.seniority} (${j.source})`)
  console.log(`   ${j.sourceUrl}`)
})
