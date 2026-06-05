import type { RawJob, MatchProfile } from '../schema'
import type { Adapter, FetchJson } from './types'
import { defaultFetchJson } from './types'

const strip = (html: string) =>
  html.replace(/<[^>]+>/g, ' ').replace(/&#x2F;/g, '/').replace(/&amp;/g, '&')
      .replace(/&gt;/g, '>').replace(/&lt;/g, '<').replace(/\s+/g, ' ').trim()

export function parseHnThread(thread: any): RawJob[] {
  const children = Array.isArray(thread?.children) ? thread.children : []
  return children
    .filter((c: any) => c && typeof c.text === 'string' && c.text.length > 0)
    .map((c: any): RawJob => {
      const text = strip(c.text)
      const firstLine = text.split('|').map((s: string) => s.trim())
      const company = firstLine[0]?.slice(0, 80) || 'Unknown'
      const title = firstLine[1]?.slice(0, 120) || firstLine[0]?.slice(0, 120) || 'See posting'
      const location = firstLine[2]?.slice(0, 80) || ''
      const remoteHint = /\bremote\b/i.test(text) ? 'remote' : 'unknown'
      return {
        source: 'hackernews', sourceId: String(c.id ?? ''),
        title, company, location, url: `https://news.ycombinator.com/item?id=${c.id}`,
        postedAt: c.created_at ? String(c.created_at) : undefined,
        tags: [], descriptionText: text, remoteHint: remoteHint as RawJob['remoteHint'],
      }
    })
}

export function hackerNewsAdapter(fetchJson: FetchJson = defaultFetchJson): Adapter {
  return {
    id: 'hackernews', kind: 'automated',
    async fetch(_profile: MatchProfile): Promise<RawJob[]> {
      const search: any = await fetchJson(
        'https://hn.algolia.com/api/v1/search_by_date?tags=story,author_whoishiring&hitsPerPage=20')
      const hit = (search.hits ?? []).find((h: any) => /who is hiring/i.test(h.title ?? ''))
      if (!hit) return []
      const thread = await fetchJson(`https://hn.algolia.com/api/v1/items/${hit.objectID}`)
      return parseHnThread(thread)
    },
  }
}
