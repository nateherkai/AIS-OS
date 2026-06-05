import type { Adapter } from './types'
import { remoteOkAdapter } from './remoteok'
import { remotiveAdapter } from './remotive'
import { wwrAdapter } from './weworkremotely'
import { hackerNewsAdapter } from './hackernews'

export function automatedAdapters(): Adapter[] {
  return [remoteOkAdapter(), remotiveAdapter(), wwrAdapter(), hackerNewsAdapter()]
}
