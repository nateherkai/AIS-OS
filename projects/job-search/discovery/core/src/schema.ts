import { z } from 'zod'

export const RawJob = z.object({
  source: z.string(),
  sourceId: z.string().optional(),
  title: z.string(),
  company: z.string(),
  location: z.string().default(''),
  url: z.string(),
  postedAt: z.string().optional(),          // ISO 8601
  tags: z.array(z.string()).default([]),
  descriptionText: z.string().default(''),
  remoteHint: z.enum(['remote', 'hybrid', 'onsite', 'unknown']).default('unknown'),
})
export type RawJob = z.infer<typeof RawJob>

export const Job = z.object({
  id: z.string(),
  source: z.string(),
  sourceUrl: z.string(),
  title: z.string(),
  company: z.string(),
  location: z.string(),
  remote: z.enum(['remote', 'hybrid', 'onsite', 'unknown']),
  employmentType: z.enum(['permanent', 'contract', 'unknown']),
  seniority: z.enum(['junior', 'mid', 'senior', 'lead', 'manager', 'unknown']),
  salary: z.object({
    min: z.number().optional(), max: z.number().optional(),
    currency: z.string().optional(), period: z.enum(['year', 'day', 'hour']).optional(),
  }).optional(),
  postedAt: z.string().optional(),
  tags: z.array(z.string()),
  descriptionText: z.string(),
  fetchedAt: z.string(),
  score: z.number().optional(),
})
export type Job = z.infer<typeof Job>

export const MatchProfile = z.object({
  roleFamilies: z.array(z.string()),
  stackKeywords: z.array(z.string()),
  localCities: z.array(z.string()),
  remoteOk: z.boolean(),
  minSalaryAud: z.number(),
  recencyDays: z.number(),
  excludeSeniorities: z.array(z.string()),
  exploreShare: z.number(),                 // 0..1
  shortlistSize: z.number(),
})
export type MatchProfile = z.infer<typeof MatchProfile>
