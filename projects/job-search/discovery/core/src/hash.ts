import { createHash } from 'node:crypto'

const norm = (s: string) => s.trim().toLowerCase().replace(/\s+/g, ' ')

export function jobKey(company: string, title: string, location: string): string {
  return `${norm(company)}|${norm(title)}|${norm(location)}`
}

export function jobId(company: string, title: string, location: string): string {
  return createHash('sha1').update(jobKey(company, title, location)).digest('hex').slice(0, 16)
}
