import type { RawJob, MatchProfile } from '../schema'
import type { Adapter, FetchJson } from './types'
import { defaultFetchJson } from './types'

export function parseRemotive(payload: any): RawJob[] {
  const jobs = Array.isArray(payload?.jobs) ? payload.jobs : []
  return jobs.map((e: any): RawJob => ({
    source: 'remotive',
    sourceId: String(e.id ?? ''),
    title: String(e.title ?? ''),
    company: String(e.company_name ?? ''),
    location: String(e.candidate_required_location ?? 'Remote'),
    url: String(e.url ?? ''),
    postedAt: e.publication_date ? String(e.publication_date) : undefined,
    tags: Array.isArray(e.tags) ? e.tags.map(String) : [],
    descriptionText: String(e.description ?? '').replace(/<[^>]+>/g, ' ').trim(),
    remoteHint: 'remote',
  }))
}

export function remotiveAdapter(fetchJson: FetchJson = defaultFetchJson): Adapter {
  return {
    id: 'remotive', kind: 'automated',
    async fetch(profile: MatchProfile): Promise<RawJob[]> {
      const q = encodeURIComponent(profile.roleFamilies[0] ?? 'engineer')
      return parseRemotive(await fetchJson(`https://remotive.com/api/remote-jobs?search=${q}`))
    },
  }
}
