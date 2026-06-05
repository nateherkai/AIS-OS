import type { RawJob, MatchProfile } from '../schema'
import type { Adapter, FetchJson } from './types'
import { defaultFetchJson } from './types'

const UA = 'job-discovery/0.1 (+https://github.com/yuanxchen)'

export function parseRemoteOk(payload: unknown): RawJob[] {
  if (!Array.isArray(payload)) return []
  return payload
    .filter((e: any) => e && e.position && e.company)   // drops the leading legal object
    .map((e: any): RawJob => ({
      source: 'remoteok',
      sourceId: String(e.id ?? ''),
      title: String(e.position),
      company: String(e.company),
      location: String(e.location ?? 'Remote'),
      url: String(e.url ?? e.apply_url ?? ''),
      postedAt: e.date ? String(e.date) : undefined,
      tags: Array.isArray(e.tags) ? e.tags.map(String) : [],
      descriptionText: String(e.description ?? '').replace(/<[^>]+>/g, ' ').trim(),
      remoteHint: 'remote',
    }))
}

export function remoteOkAdapter(fetchJson: FetchJson = defaultFetchJson): Adapter {
  return {
    id: 'remoteok',
    kind: 'automated',
    async fetch(_profile: MatchProfile): Promise<RawJob[]> {
      const payload = await fetchJson('https://remoteok.com/api', { headers: { 'User-Agent': UA } })
      return parseRemoteOk(payload)
    },
  }
}
