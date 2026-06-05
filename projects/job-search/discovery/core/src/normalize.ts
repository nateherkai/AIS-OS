import type { Job, RawJob } from './schema'
import { jobId } from './hash'

function inferSeniority(title: string): Job['seniority'] {
  const t = title.toLowerCase()
  if (/\b(grad|graduate|junior|jr)\b/.test(t)) return 'junior'
  if (/\b(senior|sr|staff|principal)\b/.test(t)) return 'senior'
  if (/\b(lead|tech lead)\b/.test(t)) return 'lead'
  if (/\b(manager|head of|director|vp)\b/.test(t)) return 'manager'
  return 'mid'
}

function inferEmployment(text: string): Job['employmentType'] {
  const t = text.toLowerCase()
  if (/\b(contract|contractor|freelance|day rate)\b/.test(t)) return 'contract'
  if (/\b(permanent|full[- ]time|perm)\b/.test(t)) return 'permanent'
  return 'unknown'
}

export function normalize(raw: RawJob, fetchedAt: string): Job {
  const text = `${raw.title} ${raw.descriptionText}`
  return {
    id: jobId(raw.company, raw.title, raw.location),
    source: raw.source,
    sourceUrl: raw.url,
    title: raw.title.trim(),
    company: raw.company.trim(),
    location: raw.location.trim(),
    remote: raw.remoteHint,
    employmentType: inferEmployment(text),
    seniority: inferSeniority(raw.title),
    postedAt: raw.postedAt,
    tags: raw.tags,
    descriptionText: raw.descriptionText,
    fetchedAt,
  }
}
