import Parser from 'rss-parser'
import type { RawJob, MatchProfile } from '../schema'
import type { Adapter } from './types'

const parser = new Parser({ customFields: { item: ['region'] } })

export async function parseWwr(xml: string): Promise<RawJob[]> {
  const feed = await parser.parseString(xml)
  return (feed.items ?? []).map((it: any): RawJob => {
    const raw = String(it.title ?? '')
    const idx = raw.indexOf(':')
    const company = idx > -1 ? raw.slice(0, idx).trim() : 'Unknown'
    const title = idx > -1 ? raw.slice(idx + 1).trim() : raw.trim()
    return {
      source: 'weworkremotely',
      title, company,
      location: String(it.region ?? 'Remote'),
      url: String(it.link ?? it.guid ?? ''),
      postedAt: it.pubDate ? new Date(it.pubDate).toISOString() : undefined,
      tags: [],
      descriptionText: String(it.contentSnippet ?? it.content ?? '').replace(/<[^>]+>/g, ' ').trim(),
      remoteHint: 'remote',
    }
  })
}

export function wwrAdapter(): Adapter {
  return {
    id: 'weworkremotely', kind: 'automated',
    async fetch(_profile: MatchProfile): Promise<RawJob[]> {
      const res = await fetch('https://weworkremotely.com/categories/remote-programming-jobs.rss')
      if (!res.ok) throw new Error(`wwr -> ${res.status}`)
      return parseWwr(await res.text())
    },
  }
}
