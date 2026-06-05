import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import type { Job } from '../core/src/schema'

const norm = (s: string) => s.trim().toLowerCase().replace(/\s+/g, ' ')
export const leadKey = (company: string, title: string) => `${norm(company)}|${norm(title)}`

// Parse the markdown table; column order: #, Company, Role, Source, Link, Status, ...
export function readLeadKeys(path: string): Set<string> {
  const keys = new Set<string>()
  if (!existsSync(path)) return keys
  for (const line of readFileSync(path, 'utf8').split('\n')) {
    const m = line.match(/^\|([^|]*)\|([^|]*)\|([^|]*)\|/)   // #, Company, Role
    if (!m) continue
    const company = m[2].trim(), role = m[3].trim()
    if (!company || /^company$/i.test(company) || company.startsWith('-')) continue
    if (company.startsWith('_')) continue   // placeholder row
    keys.add(leadKey(company, role))
  }
  return keys
}

export function appendLeads(path: string, jobs: Job[]): void {
  const existing = readLeadKeys(path)
  const lines = readFileSync(path, 'utf8').split('\n')
  // find the last table row line index
  let lastRow = -1
  for (let i = 0; i < lines.length; i++) if (/^\|/.test(lines[i])) lastRow = i
  const rows = jobs
    .filter(j => !existing.has(leadKey(j.company, j.title)))
    .map(j => `| | ${j.company} | ${j.title} | ${j.source} | ${j.sourceUrl} | Lead |  |  |  |  | score ${j.score ?? '-'} |`)
  if (rows.length === 0) return
  lines.splice(lastRow + 1, 0, ...rows)
  writeFileSync(path, lines.join('\n'))
}
