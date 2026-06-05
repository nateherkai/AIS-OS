import type { RawJob, MatchProfile } from '../schema'

export interface Adapter {
  id: string
  kind: 'automated' | 'gated'
  // Plan 2 widens this to also return a BrowsePlan for gated adapters.
  fetch(profile: MatchProfile): Promise<RawJob[]>
}

export type FetchJson = (url: string, init?: RequestInit) => Promise<unknown>
export const defaultFetchJson: FetchJson = async (url, init) => {
  const res = await fetch(url, init)
  if (!res.ok) throw new Error(`${url} -> ${res.status}`)
  return res.json()
}
