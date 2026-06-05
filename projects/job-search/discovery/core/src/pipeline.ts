import type { Adapter } from './adapters/types'
import type { Job, MatchProfile } from './schema'
import { normalize } from './normalize'
import { dedup } from './dedup'
import { passesHardFilters } from './filter'
import { rank } from './rank'
import { buildShortlist } from './explore'

export type Skipped = { id: string; error: string }
export type PipelineResult = { shortlist: Job[]; skipped: Skipped[] }

export async function runPipeline(
  profile: MatchProfile, adapters: Adapter[], seen: Set<string>, fetchedAt: string,
): Promise<PipelineResult> {
  const skipped: Skipped[] = []
  const raw = (await Promise.all(adapters.map(async a => {
    try { return await a.fetch(profile) }
    catch (e) { skipped.push({ id: a.id, error: (e as Error).message }); return [] }
  }))).flat()

  let jobs = raw.map(r => normalize(r, fetchedAt))
  jobs = dedup(jobs, seen)
  jobs = jobs.filter(j => passesHardFilters(j, profile))
  jobs = rank(jobs, profile)
  const shortlist = buildShortlist(jobs, profile)
  return { shortlist, skipped }
}
