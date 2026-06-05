import type { Job, MatchProfile } from './schema'

// Deterministic: take the top (N - reserve) by score, then fill `reserve` slots
// preferring novelty — jobs whose source isn't yet represented — else next by score.
export function buildShortlist(ranked: Job[], profile: MatchProfile): Job[] {
  const N = profile.shortlistSize
  const sorted = [...ranked].sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
  if (sorted.length <= N) return sorted

  const reserve = Math.floor(profile.exploreShare * N)
  const topCount = N - reserve
  const chosen = sorted.slice(0, topCount)
  const chosenIds = new Set(chosen.map(j => j.id))
  const sources = new Set(chosen.map(j => j.source))
  const rest = sorted.slice(topCount)

  const novel = rest.filter(j => !sources.has(j.source))
  for (const j of novel) {
    if (chosen.length >= N) break
    chosen.push(j); chosenIds.add(j.id)
  }
  for (const j of rest) {
    if (chosen.length >= N) break
    if (!chosenIds.has(j.id)) { chosen.push(j); chosenIds.add(j.id) }
  }
  return chosen
}
